// Mew Assistant - Minimal Azure Infrastructure (Ultra Low Cost)
// Uses App Service Free Tier with SQLite database (can upgrade to PostgreSQL later)

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
var storageAccountName = take(replace(fullAppName, '-', ''), 24)

// App Service Plan (Basic Tier - ~$13/month)
resource appServicePlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
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
      alwaysOn: false
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
        {
          name: 'DATABASE_URL'
          value: 'sqlite:///./mew_assistant.db'
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

// Storage Account (for database backups)
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
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

// Outputs
output webAppName string = webApp.name
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output storageAccountName string = storageAccount.name
output resourceGroupName string = resourceGroup().name
output deploymentCost string = 'Basic tier App Service (~$13/month) + Storage (~$0.02/month) = ~$13-15/month'
