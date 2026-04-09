"""
opensearch_check.py

Tests connectivity to an OpenSearch instance and lists all indices.
Called from Harness pipeline via:
    python opensearch_check.py

Environment variables (injected by Harness):
    OPENSEARCH_HOST      - e.g. 10.0.1.5
    OPENSEARCH_PORT      - e.g. 9200 (default)
    OPENSEARCH_USER      - dashboard username
    OPENSEARCH_PASSWORD  - dashboard password
    OPENSEARCH_USE_SSL   - true/false (default false for HTTP VMs)
"""

import os
import sys
import json
import urllib.request
import urllib.error
import base64
import ssl


def get_env(key: str, default: str = None) -> str:
    value = os.environ.get(key, default)
    if value is None:
        print(f"[ERROR] Missing required environment variable: {key}")
        sys.exit(1)
    return value


def build_auth_header(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def make_request(url: str, auth_header: str, use_ssl: bool) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", auth_header)
    req.add_header("Content-Type", "application/json")

    ctx = ssl.create_default_context() if use_ssl else None
    if ctx:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main():
    host     = get_env("OPENSEARCH_HOST")
    port     = get_env("OPENSEARCH_PORT", "9200")
    user     = get_env("OPENSEARCH_USER")
    password = get_env("OPENSEARCH_PASSWORD")
    use_ssl  = get_env("OPENSEARCH_USE_SSL", "false").lower() == "true"

    scheme   = "https" if use_ssl else "http"
    base_url = f"{scheme}://{host}:{port}"
    auth     = build_auth_header(user, password)

    # ------------------------------------------------------------------
    # Step 1: Connectivity check — cluster health
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"  OpenSearch Connectivity Check")
    print(f"  Target: {base_url}")
    print(f"{'='*60}\n")

    try:
        health = make_request(f"{base_url}/_cluster/health", auth, use_ssl)
        print("[OK] Connected to OpenSearch cluster")
        print(f"     Cluster name : {health.get('cluster_name')}")
        print(f"     Status       : {health.get('status')}")
        print(f"     Nodes        : {health.get('number_of_nodes')}")
        print(f"     Shards       : {health.get('active_shards')}")
    except urllib.error.URLError as e:
        print(f"[FAIL] Cannot reach OpenSearch at {base_url}")
        print(f"       Reason: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Unexpected error during connectivity check: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2: List all indices
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("  Indices")
    print(f"{'='*60}")

    try:
        indices = make_request(
            f"{base_url}/_cat/indices?format=json&s=index", auth, use_ssl
        )

        if not indices:
            print("  (no indices found)")
        else:
            print(f"  {'INDEX':<45} {'STATUS':<10} {'DOCS':>10} {'SIZE':>10}")
            print(f"  {'-'*45} {'-'*10} {'-'*10} {'-'*10}")
            for idx in indices:
                name   = idx.get("index", "")
                status = idx.get("health", "")
                docs   = idx.get("docs.count", "0")
                size   = idx.get("store.size", "0b")
                print(f"  {name:<45} {status:<10} {docs:>10} {size:>10}")

        print(f"\n  Total indices: {len(indices)}")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Failed to list indices: HTTP {e.code} {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Unexpected error listing indices: {e}")
        sys.exit(1)

    print("\n[DONE] All checks passed.\n")


if __name__ == "__main__":
    main()
