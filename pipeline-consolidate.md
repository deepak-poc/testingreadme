## Pre-requisite

_**Please make sure you have the values ready for the variables listed below.**_

| Job Name                           | Input Name        | Type   | Required | Description                                                           | Example          |
| ---------------------------------- | ----------------- | ------ | -------- | --------------------------------------------------------------------- | ---------------- |
| `cd-workflow`                      | `release_version` | string | Yes    | Semantic version to deploy                                            | `1.0.1`          |
|                                    | `envname`         | string | Yes    | Target environment (`dev`, `prod`, etc.)                              | `sandbox`        |
|                                    | `deploy_options`  | string | No     | Extra parameters passed to the script                                 | `full`        |
|                                    | `snowflake_deployment_file` | string | No     |  Snaowflake deployment Python File Name                      | `snow_sql_execute`        |
| `build-feature`                 | `build_file`      | string |  Yes    | Makefile to use for the build                                         | `makefile.linux` |
|                                    | `build_options`   | string |  No     | Additional make options or targets                                    | `setup`      |
| `build-main`                 | `build_file`      | string |  Yes    | Makefile to use for the build                                         | `makefile.linux` |
|                                    | `build_options`   | string |  No     | Additional make options or targets                                    | `setup`      |

_**Please make sure you have the secrets created with the secrets names listed below.**_

| Secret Name               |  Purpose / Description                                              |
| ------------------------- | ---------------------------------------------------------------------| 
| `GITHUB_TOKEN`            |GitHub default token for actions, PRs, tagging, etc.                  |
| `GCP_SERVICE_ACCOUNT_KEY` |  GCP JSON key for authenticating with Google Cloud SDK               |
| `WPC_PRO_HOST`            |  Internal host for Snowflake or WPC system                           |
| `WPC_PRO_API_USER`        |  API username for authenticated access                               |
| `WPC_PRO_API_SECRET`      | API secret key                                                       |
| `BASIC_APP_ID`            |  GitHub App ID for token generation (for secure submodule checkout)  |
| `BASIC_APP_KEY`           |  GitHub App private key for token generation                         |
| `PROGET_CA_CERT`          | Internal CA certificate used during build setup                      |

_**Please make sure you have the emvironment repo variable created with the variable names listed below.**_

| Repository Variable               |  Purpose / Description                                              |
| ------------------------- | ---------------------------------------------------------------------| 
| `GCP_PROJECT_NAME`            | GCP PROJECT ID                 |

