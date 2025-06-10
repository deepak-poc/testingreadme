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
This reusable workflow automates the build process for SAMDA projects. It supports dynamic build file selection, injects secure secrets, authenticates to GCP, and integrates reusable templates via Git submodules.

### Usage
To use this workflow, call it from another repository using `workflow_call` and provide the required inputs and secrets.

```
jobs:
  build:
    uses: charlesschwab/samda-action-workflows/.github/workflows/build-action.yml@v1
    with:
      build_file: 'makefile.linux'
      build_options: 'setup'
    secrets: inherit
```

### Inputs

| Name            | Description                                | Required | Example          |
| --------------- | ------------------------------------------ | -------- | ---------------- |
| `build_file`    | Makefile used for building the application | Yes    | `makefile.linux` |
| `build_options` | Additional build options/targets           | No     | `setup`      |


### Secrets

| Name                      | Description                                        |
| ------------------------- | -------------------------------------------------- |
| `WPC_PRO_HOST`            | Hostname for secure platform-related access        |
| `WPC_PRO_API_USER`        | API user for backend integration                   |
| `WPC_PRO_API_SECRET`      | API secret key                                     |
| `GITHUB_TOKEN`            | Default GitHub token                               |
| `BASIC_APP_ID`            | App ID for generating temporary GitHub App token   |
| `BASIC_APP_KEY`           | Private key for GitHub App authentication          |
| `GCP_SERVICE_ACCOUNT_KEY` | GCP credentials for authentication                 |
| `PROGET_CA_CERT`          | Internal CA cert used during build (for pre-setup) |

### Highlights

- Uses GitHub App authentication for secure token generation.
- Dynamically loads reusable templates via Git submodules.
-  Executes customizable Makefile-based builds with passed options.
  
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
This reusable workflow automates the release process for SAMDA projects. It handles version extraction, tagging, pre-release validation deployments, and creates an official GitHub release. It is designed to ensure consistency and automation in releasing new application versions.

**Usage:**  
Triggered after merge to `main`.
```
jobs:
  release:
    uses: charlesschwab/samda-action-workflows/.github/workflows/release-action.yml@v1
    with:
      release_version: '1.2.3'
    secrets: inherit
```

**Inputs:**  

| Name              | Description                                                                           | Required | Example |
| ----------------- | ------------------------------------------------------------------------------------- | -------- | ------- |
| `release_version` | Release version to process (optional, extracted from `.bumpversion.cfg` if not given) | No     | `1.2.3` |


**Secrets:**  
| Name                      | Description                             |
| ------------------------- | --------------------------------------- |
| `GITHUB_TOKEN`            | GitHub token for pushing tags           |
| `GCP_SERVICE_ACCOUNT_KEY` | GCP credentials in JSON format for auth |


**Highlights:**
- Extracts version from .bumpversion.cfg
- Tags the commit as main-<version> and pushes to the repo
- Creates a GitHub release with release notes

---

### `snowflake-deploy-action.yml`

**Description:**  
This reusable workflow automates deployment to Snowflake environments in SAMDA projects. It performs semantic version validation, checks user permissions for production deployments, and executes the Snowflake deploy targets via make.

**Usage:**  
Invoked via `workflow_call` with necessary environment and version.
```
jobs:
  deploy:
    uses: charlesschwab/samda-action-workflows/.github/workflows/snowflake-deploy-action.yml@v1
    with:
      release_version: '1.2.3'
      envname: 'sandbox'
      deploy_options: 'full'
    secrets: inherit

```

**Inputs:**  
| Name              | Description                                   | Required | Example   |
| ----------------- | --------------------------------------------- | -------- | --------- |
| `release_version` | Semantic version to deploy                    |  Yes    | `1.2.3`   |
| `envname`         | Target environment (e.g., dev, prod, sandbox) |  Yes    | `sandbox` |
| `deploy_options`  | Extra flags/options passed to makefile        |  No     | `full` |

**Secrets:**  
| Name                      | Description                             |
| ------------------------- | --------------------------------------- |
| `GCP_SERVICE_ACCOUNT_KEY` | GCP service account credentials in JSON |
| `WPC_PRO_HOST`            | Snowflake host name for connection      |
| `WPC_PRO_API_USER`        | API username used for deployment        |
| `WPC_PRO_API_SECRET`      | API secret key                          |
| `GITHUB_TOKEN`            | GitHub token for auth operations        |


**Highlights:**
- Prevents unauthorized deployments to prod (enforced via GitHub actor check).
- Validates semantic version syntax
- Runs the Snowflake deployment using makefile.linux with passed options.

---

### `stale.yml`

**Description:**  
This reusable workflow automatically monitors and flags stale pull requests. It runs on a daily schedule, and marks PRs as stale if they’ve had no activity for 15 days, helping maintain an active and clean development workflow.

**Usage:**  
This workflow runs automatically based on a cron schedule. It is not meant to be manually triggered or called via workflow_call.

**Inputs:**  
This workflow does not require any inputs.

**Secrets:**  
_None_

**Highlights:**
- Automatically detects and marks stale PRs after 15 days of inactivity.
- Adds a "Stale" label and comments on the PR with a warning message.
- Closes stale PRs 1 day after being marked stale.
- Skips if comments or updates are made

---

## Contributing

Feel free to open issues or submit pull requests to enhance these reusable workflows.

