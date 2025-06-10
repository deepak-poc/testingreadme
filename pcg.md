# SAMDA Action Workflows

This repository provides reusable GitHub Actions workflows designed to standardize and automate CI/CD processes across projects, with support for validation, deployment, version bumping, stale PR checking, and more.

---

## Workflows Overview

### `validate-action.yml`

**Description:**  
Ensures proper version bumping practices by comparing `.bumpversion.cfg` and `pyproject.toml`. Validates patch-only version increments.

**Usage:**  
Called via `workflow_call` to validate version update in PRs.

**Inputs:**  
_None_

**Secrets:**  
- `GITHUB_TOKEN`

**Highlights:**
- Extracts version info from configuration files
- Fails if mismatch or invalid bump
- Enforces patch-only bumps

---

### `deploy-action.yml`

**Description:**  
This reusable workflow handles the deployment of SAMDA projects. It checks out a specific release version, authenticates with Google Cloud, and executes a deployment script against a specified environment.

**Usage:**  
Reusable for structured deploy logic with project-specific commands.
```
jobs:
  deploy-to-dev:
    uses: ./.github/workflows/your-reusable-workflow-name.yml
    with:
      release_version: '1.0.1'
      envname: 'dev'
      deploy_script: './scripts/deploy.sh'
      deploy_options: '--verbose'
    secrets:
      GCP_SERVICE_ACCOUNT_KEY: ${{ secrets.GCP_SA_KEY_DEV }}
```

**Inputs:**  

| Input | Type     | Description                | Required |
| :-------- | :------- | :------------------------- | :------------------------- |
| `release_version` | `string` | The release version to deploy (e.g., 1.0.1). It must follow semantic versioning. | Yes |
| `envname` | `string` | The environment to deploy to (e.g., dev, staging, prod). | Yes |
| `deploy_script` | `string` | The deployment script to execute. | No|
| `deploy_options` | `string` | Optional arguments to pass to the deployment script.	 | No |

**Secrets:**  

| Secrets | Description |
| :-------- | :------- | 
| `GITHUB_TOKEN` | This is automatically provided by GitHub. | 
| `GCP_SERVICE_ACCOUNT_KEY` | The JSON key for the Google Cloud service account used for authentication. |


**Highlights:**
- **Production Deploy Guard:** Restricts deployments to the prod environment to only repository OWNER or ADMIN users.
- **Version Validation:** Automatically validates that the release_version input adheres to the semantic versioning format (e.g., X.Y.Z).
- **Tag-based Checkout**: Checks out the exact code corresponding to the release by using the main-${{ inputs.release_version }} tag.
- **Dynamic Script Execution:** Runs a specified deployment script, passing in the environment, GCP project ID, and bucket names as arguments.

---

### `build-action.yml`

### Description
This reusable workflow compiles and builds SAMDA projects using make-based automation. It integrates token-based GitHub authentication, submodule injection for shared makefile templates, and supports secure ProGet and GCP integration.

### Usage
To use this workflow, call it from another repository using `workflow_call` and provide the required inputs and secrets.

### Inputs

- **build_file** (string, required): Makefile to be executed for the build (e.g., `makefile.linux`).
- **build_options** (string, optional): Extra arguments passed to the `make` command.

### Secrets

- **WPC_PRO_HOST** (required): ProGet host address for internal PyPI resolution.
- **WPC_PRO_API_USER** (required): Username for ProGet API.
- **WPC_PRO_API_SECRET** (required): Secret for ProGet API access.
- **GITHUB_TOKEN** (required): Token for accessing private GitHub repositories.
- **GCP_SERVICE_ACCOUNT_KEY** (required): JSON key for authenticating with GCP.
- **PROGET_CA_CERT** (required): Certificate authority file for ProGet SSL.
- **BASIC_APP_ID** (required): GitHub App ID for generating tokens.
- **BASIC_APP_KEY** (required): Private key used with GitHub App to sign tokens.

### Highlights

- Cleans old or unused submodules before starting.
- Dynamically injects reusable makefile templates via submodule.
- Uses GitHub App authentication for secure token generation.
- Authenticates and builds using secure credentials and make.


---

### `opensource-gov.yml`

**Description:**  
This workflow automates the submission of reviewed open-source dependencies. It is triggered when an existing issue is edited to include a specific tag (<!-- OSG DEPENDENCY-REPORT) and helps ensure that all dependency reviews are tracked and submitted according to internal security policies.

**Usage:**  
The workflow should be referenced in repositories that want to support automated dependency review submission via issues.
```
jobs:
  mark-reviews:
    name: Submit Reviewed Dependencies
    uses: charlesschwab/application-security/.github/workflows/opensource-gov.yml@v5
    secrets: inherit
    with:
      run-mode: 'submit-reviews'
      issue-number: '${{ github.event.issue.number }}'
      review-user: '${{ github.event.sender.login }}'
```

**Inputs:**  

| Name           | Description                                              | Required | Example                            |
| -------------- | -------------------------------------------------------- | -------- | ---------------------------------- |
| `run-mode`     | Workflow mode – currently supports `submit-reviews` only | Yes    | `submit-reviews`                   |
| `issue-number` | Issue number containing the dependency review report     | Yes    | `${{ github.event.issue.number }}` |
| `review-user`  | GitHub username of the person submitting the review      | Yes    | `${{ github.event.sender.login }}` |

**Secrets:**  
_Inherits default secrets_

**Highlights:**
- Triggered by issue edits with a special dependency report tag.
- Auto-submits dependency reviews to the Open Source Governance system.
- Helps fulfill open source governance policy

---

### `release-action.yml`

**Description:**  
Automates tagging and release creation after a merge. Calculates new version from config and pushes to GitHub with changelog.

**Usage:**  
Triggered after merge to `main`.

**Inputs:**  
- `release_version` (optional) – Bump version to tag

**Secrets:**  
- `GITHUB_TOKEN`

**Highlights:**
- Creates and pushes annotated Git tag
- Generates GitHub release notes
- Embeds automated bumpversion parsing

---

### `snowflake-deploy-action.yml`

**Description:**  
Specialized workflow to deploy Snowflake RBAC configurations using environment-specific Makefile targets.

**Usage:**  
Invoked via `workflow_call` with necessary environment and version.

**Inputs:**  
- `release_version` – Target version
- `envname` – Target Snowflake environment
- `deploy_options` – CLI deploy flags

**Secrets:**  
- `WPC_PRO_API_SECRET`
- `WPC_PRO_API_USER`
- `WPC_PRO_API_HOST`
- `GITHUB_TOKEN`
- `GCP_SERVICE_ACCOUNT_KEY`

**Highlights:**
- Ensures prod deploys are only run by admins
- Validates semantic version syntax
- Runs tagged deploy with Google auth

---

### `stale.yml`

**Description:**  
Automatically marks and closes stale PRs after inactivity.

**Usage:**  
Runs daily via scheduled cron job.

**Inputs:**  
_None_

**Secrets:**  
_None_

**Highlights:**
- Labels PRs as stale after 15 days
- Closes PRs after 1 additional day
- Skips if comments or updates are made

---

## Contributing

Feel free to open issues or submit pull requests to enhance these reusable workflows.

