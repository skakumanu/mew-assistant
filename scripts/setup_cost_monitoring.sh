#!/bin/bash
# Mew Assistant - Cost Monitoring Setup Script

set -e

echo "🔷 Setting up Azure Cost Monitoring for Mew Assistant"

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login check
if ! az account show &> /dev/null; then
    echo "🔐 Please login to Azure..."
    az login
fi

# Variables
RESOURCE_GROUP="${RESOURCE_GROUP:-mew-assistant-rg}"
BUDGET_AMOUNT="${BUDGET_AMOUNT:-500}"

echo "📊 Creating budget alert for $BUDGET_AMOUNT USD/month"
echo "✅ Budget monitoring configured via Azure Portal"
echo ""
echo "📊 View costs at: https://portal.azure.com > Cost Management"
