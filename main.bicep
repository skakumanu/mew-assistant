// Mew Assistant - Azure Infrastructure (Bicep Template)
// Economical deployment using Azure Free Tier and low-cost options

@description('Base name for all resources')
param appName string = 'mew-assistant'

@description('Unique suffix to ensure globally unique names')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('Location for all resources')
param location string = resourceGroup().location

@description('Environment (dev, staging, prod)')
param environment string = 'dev'

// Variables
var fullAppName = '${appName}-${uniqueSuffix}'
var appServicePlanName = '${fullAppName}-plan'
var webAppName = '${fullAppName}-web'
var postgresServerName = '${fullAppName}-db'
var keyVaultName = '${take(fullAppName, 24)}-kv'
var storageAccountName = '${take(replace(fullAppName, '-', ''), 24)}'
var appInsightsName = '${fullAppName}-insights'

// App Service Plan (Free Tier)
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'F1' // Free tier
    tier: 'Free'
    size: 'F1'
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
  tags: {
    environment: environment
    project: 'mew-assistant'
  }
}

// Web App
resource webApp 'Microsoft.Web/sites@2022-03-01' = {
  name: webAppName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      alwaysOn: false // Free tier doesn't support Always On
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: [
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'true'
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENVIRONMENT'
          value: environment
        }
      ]
    }
    httpsOnly: true
  }
  tags: {
    environment: environment
    project: 'mew-assistant'
  }
}

// PostgreSQL Flexible Server (Basic tier)
resource postgresServer 'Microsoft.DBforPostgreSQL/flexibleServers@2022-12-01' = {
  name: postgresServerName
  location: location
  sku: {
    name: 'Standard_B1ms' // Lowest cost tier
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    administratorLogin: 'mewadmin'
    administratorLoginPassword: 'TempPass123!ChangeMe' // Will be updated via Key Vault
    storage: {
      storageSizeGB: 32 // Minimum storage
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
  tags: {
    environment: environment
    project: 'mew-assistant'
  }
}

// PostgreSQL Database
resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2022-12-01' = {
  parent: postgresServer
  name: 'mewassistant'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Firewall rule to allow Azure services
resource postgresFirewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2022-12-01' = {
  parent: postgresServer
  name: 'AllowAllAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Storage Account (for backups and file uploads)
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS' // Locally redundant storage (cheapest)
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
  tags: {
    environment: environment
    project: 'mew-assistant'
  }
}

// Blob container for backups
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2022-09-01' = {
  parent: storageAccount
  name: 'default'
}

resource backupsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  parent: blobService
  name: 'backups'
  properties: {
    publicAccess: 'None'
  }
}

// Key Vault (for secrets management)
resource keyVault 'Microsoft.KeyVault/vaults@2022-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    enableRbacAuthorization: true
    accessPolicies: []
  }
  tags: {
    environment: environment
    project: 'mew-assistant'
  }
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
  tags: {
    environment: environment
    project: 'mew-assistant'
  }
}

// Outputs
output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output dbHost string = postgresServer.properties.fullyQualifiedDomainName
output dbName string = postgresDatabase.name
output keyVaultName string = keyVault.name
output storageAccountName string = storageAccount.name
output appInsightsKey string = appInsights.properties.InstrumentationKey
output resourceGroupName string = resourceGroup().name
