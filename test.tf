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


resource "azurerm_linux_function_app" "function_app" {
  name                       = var.function_app_name
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.asp.id
  storage_account_name       = azurerm_storage_account.function_sa.name
  storage_account_access_key = azurerm_storage_account.function_sa.primary_access_key
  virtual_network_subnet_id  = azurerm_subnet.function_subnet.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    # Blob trigger source: primary-sa / file-ingest
    PRIMARY_SA_CONNECTION_STRING = azurerm_storage_account.primary_sa.primary_connection_string

    # Destination: scanner-sa / scanner
    SCANNER_SA_CONNECTION_STRING = azurerm_storage_account.scanner_sa.primary_connection_string

    FUNCTIONS_WORKER_RUNTIME = "python"
    AzureWebJobsStorage      = azurerm_storage_account.function_sa.primary_connection_string

    # Oryx installs packages server-side during zip deploy
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
    ENABLE_ORYX_BUILD              = "true"
  }
}


# ===========================================================================
# Event Grid — Custom Topic
# ===========================================================================
resource "azurerm_eventgrid_topic" "main" {
  name                = var.eventgrid_topic_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

resource "azurerm_eventgrid_event_subscription" "custom_topic_scan_result" {
  name  = var.sub_custom_scan_name
  scope = azurerm_eventgrid_topic.main.id

  included_event_types = ["Microsoft.Security.MalwareScanningResult"]

  azure_function_endpoint {
    function_id                       = "${azurerm_linux_function_app.main.id}/functions/scan_handler_result_resolver"
    max_events_per_batch              = 1
    preferred_batch_size_in_kilobytes = 64
  }

  retry_policy {
    max_delivery_attempts = 30
    event_time_to_live    = 1440
  }
}

resource "azurerm_monitor_diagnostic_setting" "event_grid_topic" {
  name                       = var.diag_egt_name
  target_resource_id         = azurerm_eventgrid_topic.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log { category = "DeliveryFailures" }
  enabled_log { category = "PublishFailures" }
}

# ===========================================================================
# Event Grid — System Topic on Scanning Storage
# ===========================================================================
resource "azurerm_eventgrid_system_topic" "scanning_storage" {
  name                   = var.eg_system_scanning_name
  location               = var.location
  resource_group_name    = var.resource_group_name
  source_resource_id     = azurerm_storage_account.scanning.id
  topic_type             = "Microsoft.Storage.StorageAccounts"
  tags                   = var.tags
}

resource "azurerm_eventgrid_system_topic_event_subscription" "malware_scan_result" {
  name                = var.sub_defender_name
  system_topic        = azurerm_eventgrid_system_topic.scanning_storage.name
  resource_group_name = var.resource_group_name

  included_event_types = ["Microsoft.Security.MalwareScanningResult"]

  azure_function_endpoint {
    function_id                       = "${azurerm_linux_function_app.main.id}/functions/scan_handler_result_resolver"
    max_events_per_batch              = 1
    preferred_batch_size_in_kilobytes = 64
  }

  retry_policy {
    max_delivery_attempts = 30
    event_time_to_live    = 1440
  }
}

resource "azurerm_monitor_diagnostic_setting" "system_topic" {
  name                       = var.diag_scanning_st_name
  target_resource_id         = azurerm_eventgrid_system_topic.scanning_storage.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log { category = "DeliveryFailures" }
}

# ===========================================================================
# Event Grid — System Topic on Primary Storage
# ===========================================================================
resource "azurerm_eventgrid_system_topic" "primary_storage" {
  name                   = var.eg_system_primary_name
  location               = var.location
  resource_group_name    = var.resource_group_name
  source_resource_id     = azurerm_storage_account.primary.id
  topic_type             = "Microsoft.Storage.StorageAccounts"
  tags                   = var.tags
}

resource "azurerm_eventgrid_system_topic_event_subscription" "blob_ingest" {
  name                = var.sub_ingest_name
  system_topic        = azurerm_eventgrid_system_topic.primary_storage.name
  resource_group_name = var.resource_group_name

  included_event_types = ["Microsoft.Storage.BlobCreated"]

  subject_filter {
    subject_begins_with = "/blobServices/default/containers/ingest-files/"
  }

  azure_function_endpoint {
    function_id                       = "${azurerm_linux_function_app.main.id}/functions/scan_handler_ingest_function"
    max_events_per_batch              = 1
    preferred_batch_size_in_kilobytes = 64
  }

  retry_policy {
    max_delivery_attempts = 30
    event_time_to_live    = 1440
  }
}
