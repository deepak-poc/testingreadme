variable "location" {
  description = "Azure region where all resources will be deployed"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group to create"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}


variable "law_name" {
  description = "Override name for the Log Analytics Workspace"
  type        = string
}

variable "app_insights_name" {
  description = "Override name for the Application Insights instance"
  type        = string
}

variable "service_plan_name" {
  description = "Override name for the Service Plan"
  type        = string
}

