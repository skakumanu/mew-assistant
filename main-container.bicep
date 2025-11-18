// Mew Assistant - Azure Container Instances Deployment (Pay-per-use, ~$10-15/month)
// No quotas needed, scales to zero when not in use

@description('Base name for all resources')
param appName string = 'mew-assistant'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Container image')
param containerImage string = 'mewassistant.azurecr.io/mew-assistant:latest'

// Variables
var containerGroupName = '${appName}-container'
var storageAccountName = take(replace(appName, '-', ''), 24)

// Storage Account
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
  }
}

// File Share for database persistence
resource fileServices 'Microsoft.Storage/storageAccounts/fileServices@2022-09-01' = {
  parent: storageAccount
  name: 'default'
}

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2022-09-01' = {
  parent: fileServices
  name: 'mew-data'
  properties: {
    shareQuota: 5
  }
}

// Container Instance
resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: containerGroupName
  location: location
  properties: {
    containers: [
      {
        name: 'mew-assistant'
        properties: {
          image: 'python:3.11-slim'
          command: [
            '/bin/sh'
            '-c'
            'pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary pydantic-settings && uvicorn app.main:app --host 0.0.0.0 --port 8000'
          ]
          ports: [
            {
              port: 8000
              protocol: 'TCP'
            }
          ]
          environmentVariables: [
            {
              name: 'DATABASE_URL'
              value: 'sqlite:////mnt/data/mew_assistant.db'
            }
            {
              name: 'ENVIRONMENT'
              value: 'production'
            }
          ]
          resources: {
            requests: {
              cpu: 1
              memoryInGB: 1
            }
          }
          volumeMounts: [
            {
              name: 'data-volume'
              mountPath: '/mnt/data'
            }
          ]
        }
      }
    ]
    osType: 'Linux'
    ipAddress: {
      type: 'Public'
      ports: [
        {
          port: 8000
          protocol: 'TCP'
        }
      ]
      dnsNameLabel: appName
    }
    restartPolicy: 'Always'
    volumes: [
      {
        name: 'data-volume'
        azureFile: {
          shareName: fileShare.name
          storageAccountName: storageAccount.name
          storageAccountKey: storageAccount.listKeys().keys[0].value
        }
      }
    ]
  }
}

// Outputs
output containerUrl string = 'http://${containerGroup.properties.ipAddress.fqdn}:8000'
output storageAccountName string = storageAccount.name
output estimatedCost string = 'Container Instances (~$10-15/month) + Storage (~$1/month) = ~$11-16/month'
