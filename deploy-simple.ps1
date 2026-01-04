# Simple Azure Container App Deployment for Mew Assistant
# This creates the minimal infrastructure needed for GitHub Actions

param(
    [string]$ResourceGroup = "mew-assistant-rg",
    [string]$Location = "westus2",
    [string]$AppName = "mew-assistant-prod"
)

Write-Host "Creating Azure Container App infrastructure..." -ForegroundColor Cyan

# Create Container Apps environment
Write-Host "`n1. Creating Container Apps environment..." -ForegroundColor Yellow
$envName = "mew-env-prod"
az containerapp env create `
    --name $envName `
    --resource-group $ResourceGroup `
    --location $Location

# Create Container Registry
Write-Host "`n2. Creating Azure Container Registry..." -ForegroundColor Yellow
$acrName = "mewassistantacr"  # Must be globally unique, alphanumeric only
az acr create `
    --name $acrName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Basic `
    --admin-enabled true

# Get ACR credentials
$acrPassword = az acr credential show --name $acrName --query "passwords[0].value" -o tsv
$acrServer = "$acrName.azurecr.io"

# Build and push initial image
Write-Host "`n3. Building and pushing Docker image..." -ForegroundColor Yellow
az acr build `
    --registry $acrName `
    --image mew-assistant:latest `
    --file Dockerfile `
    .

# Create Container App
Write-Host "`n4. Creating Container App..." -ForegroundColor Yellow
az containerapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --environment $envName `
    --image "$acrServer/mew-assistant:latest" `
    --target-port 8000 `
    --ingress external `
    --registry-server $acrServer `
    --registry-username $acrName `
    --registry-password $acrPassword `
    --env-vars `
        "ENVIRONMENT=production" `
        "DATABASE_URL=sqlite:///./mew_prod.db" `
    --cpu 0.5 `
    --memory 1.0Gi `
    --min-replicas 0 `
    --max-replicas 2

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "`nApp URL:" -ForegroundColor Cyan
az containerapp show --name $AppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv

Write-Host "`n📋 GitHub Secrets needed:" -ForegroundColor Yellow
Write-Host "ACR_NAME: $acrName"
Write-Host "RESOURCE_GROUP: $ResourceGroup"
Write-Host "POSTGRES_SERVER: (not created - using SQLite for now)"
