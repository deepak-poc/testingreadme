"""
opensearch_deploy_indices.py

Fetches all index JSON files from a Harness Filestore folder,
then deploys each as an OpenSearch index.  No external dependencies.

Environment variables (injected by Harness):
    OPENSEARCH_HOST          - e.g. 10.0.1.5
    OPENSEARCH_PORT          - e.g. 9200 (default)
    OPENSEARCH_USER          - username
    OPENSEARCH_PASSWORD      - password
    OPENSEARCH_USE_SSL       - true/false (default false)

    HARNESS_API_KEY          - Harness Platform API key (Filestore read)
    HARNESS_HOST             - default https://app.harness.io
    HARNESS_ACCOUNT_ID       - <+account.identifier>
    HARNESS_ORG_ID           - <+org.identifier>
    HARNESS_PROJECT_ID       - <+project.identifier>
    FILESTORE_FOLDER_ID      - folder identifier in Filestore
                               (default ascend_dev_opensearch_nonprd_indices)
"""

import os
import sys
import json
import base64
import ssl
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def get_env(key, default=None):
    val = os.environ.get(key, default)
    if val is None:
        print(f"[ERROR] Missing required environment variable: {key}")
        sys.exit(1)
    return val


def build_auth_header(user, password):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def ssl_ctx(use_ssl):
    if not use_ssl:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ---------------------------------------------------------------------------
# OpenSearch helpers
# ---------------------------------------------------------------------------

def os_request(url, auth, use_ssl, method="GET", body=None):
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", auth)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, context=ssl_ctx(use_ssl), timeout=30) as r:
        return json.loads(r.read().decode())


def index_exists(base_url, name, auth, use_ssl):
    req = urllib.request.Request(f"{base_url}/{name}", method="HEAD")
    req.add_header("Authorization", auth)
    try:
        urllib.request.urlopen(req, context=ssl_ctx(use_ssl), timeout=10)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


# ---------------------------------------------------------------------------
# Harness Filestore helpers
# ---------------------------------------------------------------------------

def harness_get(url, api_key):
    req = urllib.request.Request(url)
    req.add_header("x-api-key", api_key)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def harness_download(url, api_key):
    req = urllib.request.Request(url)
    req.add_header("x-api-key", api_key)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_indices_from_filestore(harness_host, account_id, org_id,
                                 project_id, folder_id, api_key):
    """Lists the folder and downloads every .json file.
    Returns {index_name: definition_dict}."""

    params = (f"accountIdentifier={account_id}"
              f"&orgIdentifier={org_id}"
              f"&projectIdentifier={project_id}")

    list_url = (f"{harness_host}/ng/api/file-store"
                f"?{params}&parentIdentifier={folder_id}&pageSize=50")

    print(f"  Listing Filestore folder : {folder_id}")
    try:
        resp = harness_get(list_url, api_key)
    except Exception as e:
        print(f"[FAIL] Cannot list Filestore folder '{folder_id}': {e}")
        sys.exit(1)

    all_files  = resp.get("data", {}).get("content", [])
    json_files = [f for f in all_files if f.get("name", "").endswith(".json")]
    print(f"  Found {len(json_files)} JSON file(s)\n")

    indices = {}
    for f in json_files:
        file_id    = f["identifier"]
        file_name  = f["name"]
        index_name = os.path.splitext(file_name)[0]

        dl_url = (f"{harness_host}/ng/api/file-store/files/{file_id}/download"
                  f"?{params}")
        try:
            raw   = harness_download(dl_url, api_key)
            lines = raw.decode("utf-8").splitlines()
            # Strip leading DevTools header line e.g. "PUT index-name"
            if lines and lines[0].strip().upper().startswith(("PUT ", "POST ", "GET ")):
                lines = lines[1:]
            definition = json.loads("\n".join(lines))
            indices[index_name] = definition
            print(f"  [FETCHED] {file_name}")
        except Exception as e:
            print(f"  [ERROR]   {file_name} — {e}")

    return indices


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # OpenSearch
    host     = get_env("OPENSEARCH_HOST")
    port     = get_env("OPENSEARCH_PORT", "9200")
    user     = get_env("OPENSEARCH_USER")
    password = get_env("OPENSEARCH_PASSWORD")
    use_ssl  = get_env("OPENSEARCH_USE_SSL", "false").lower() == "true"

    base_url = f"{'https' if use_ssl else 'http'}://{host}:{port}"
    auth     = build_auth_header(user, password)

    # Harness Filestore
    harness_host = get_env("HARNESS_HOST", "https://app.harness.io")
    account_id   = get_env("HARNESS_ACCOUNT_ID")
    org_id       = get_env("HARNESS_ORG_ID")
    project_id   = get_env("HARNESS_PROJECT_ID")
    folder_id    = get_env("FILESTORE_FOLDER_ID", "ascend_dev_opensearch_nonprd_indices")
    api_key      = get_env("HARNESS_API_KEY")

    print(f"\n{'='*60}")
    print(f"  OpenSearch Index Deployment")
    print(f"  OpenSearch : {base_url}")
    print(f"  Filestore  : {folder_id}")
    print(f"{'='*60}\n")

    # Verify OpenSearch connectivity
    try:
        health = os_request(f"{base_url}/_cluster/health", auth, use_ssl)
        print(f"[OK] OpenSearch cluster '{health.get('cluster_name')}' "
              f"status={health.get('status')}\n")
    except Exception as e:
        print(f"[FAIL] Cannot connect to OpenSearch: {e}")
        sys.exit(1)

    # Fetch all index definitions from Filestore
    print(f"{'='*60}")
    print("  Phase 1 — Fetching from Harness Filestore")
    print(f"{'='*60}")
    indices = fetch_indices_from_filestore(
        harness_host, account_id, org_id, project_id, folder_id, api_key
    )

    if not indices:
        print("[WARN] No index files found — nothing to deploy.")
        sys.exit(0)

    # Deploy each index
    print(f"\n{'='*60}")
    print("  Phase 2 — Deploying to OpenSearch")
    print(f"{'='*60}\n")

    deployed, skipped, failed = [], [], []

    for index_name, definition in indices.items():
        if index_exists(base_url, index_name, auth, use_ssl):
            print(f"  [SKIP]    {index_name} — already exists")
            skipped.append(index_name)
            continue
        try:
            result = os_request(
                f"{base_url}/{index_name}", auth, use_ssl,
                method="PUT", body=json.dumps(definition).encode()
            )
            if result.get("acknowledged"):
                print(f"  [CREATED] {index_name}")
                deployed.append(index_name)
            else:
                print(f"  [WARN]    {index_name} — acknowledged=false")
                failed.append(index_name)
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:200] if hasattr(e, "read") else ""
            print(f"  [ERROR]   {index_name} — HTTP {e.code}: {err}")
            failed.append(index_name)
        except Exception as e:
            print(f"  [ERROR]   {index_name} — {e}")
            failed.append(index_name)

    # Summary
    print(f"\n{'='*60}")
    print("  Summary")
    print(f"{'='*60}")
    print(f"  Created : {len(deployed)}")
    print(f"  Skipped : {len(skipped)}  (already existed)")
    print(f"  Failed  : {len(failed)}")

    if failed:
        print("\n[FAIL] One or more indices failed to deploy.")
        sys.exit(1)

    print("\n[DONE] Index deployment complete.\n")


if __name__ == "__main__":
    main()
