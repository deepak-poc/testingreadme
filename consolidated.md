| Workflow File           | Input Name        | Description                                  | Required | Example       |
| ----------------------- | ----------------- | -------------------------------------------- | -------- | ------------- |
| **validate-action.yml** | `release_version` | Semantic version tag for deployment          | Yes    | `1.0.1`       |
|                         | `envname`         | Target environment (e.g., `dev`, `prod`)     | Yes    | `sandbox`     |
|                         | `deploy_script`   | Script path used for deployment execution    | No     | `makefile.linux` |
|                         | `deploy_options`  | Extra parameters passed to the deploy script | No     | `full`     |
