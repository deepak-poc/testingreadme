data "azurerm_client_config" "current" {}

# ===========================================================================
# Log Analytics Workspace
# Central log sink for all diagnostic settings
# ===========================================================================
resource "azurerm_log_analytics_workspace" "main" {
  name                = var.law_name
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

# ===========================================================================
# Function App — Application Insights (workspace-based)
# ===========================================================================
resource "azurerm_application_insights" "main" {
  name                = var.app_insights_name
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "other"
  tags                = var.tags
}

# ===========================================================================
# Function App — App Service Plan (Linux Elastic Premium)
# EP1 required for VNet integration; switch back to Y1 only if VNet is removed
# ===========================================================================
resource "azurerm_service_plan" "main" {
  name                = var.service_plan_name
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "EP1"
  tags                = var.tags
}

