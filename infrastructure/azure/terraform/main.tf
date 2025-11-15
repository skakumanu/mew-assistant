terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "environment" {
  default = "dev"
}

variable "location" {
  default = "eastus"
}

variable "project_name" {
  default = "mew-assistant"
}

resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.location
}

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}-${var.environment}-kv"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

resource "azurerm_storage_account" "backups" {
  name                     = "${var.project_name}${var.environment}st"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
}

resource "azurerm_storage_container" "backups" {
  name                  = "mew-backups"
  storage_account_name  = azurerm_storage_account.backups.name
  container_access_type = "private"
}

data "azurerm_client_config" "current" {}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "storage_connection_string" {
  value     = azurerm_storage_account.backups.primary_connection_string
  sensitive = true
}
