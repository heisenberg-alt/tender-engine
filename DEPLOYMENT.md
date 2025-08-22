# Resource Group Deployment Guide

This Bicep template has been modified to deploy to resource group scope instead of subscription scope.

## Prerequisites

1. **Resource Group**: You must have an existing resource group where you want to deploy the resources
2. **Permissions**: You need to be an **Owner** or **Contributor** of the resource group (not subscription level)

## Deployment Instructions

### Option 1: Using Azure Developer CLI (azd)

1. First, create a resource group in Azure portal or Azure CLI:
   ```bash
   az group create --name rg-tender-engine --location swedencentral
   ```

2. Deploy using azd with resource group targeting:
   ```bash
   azd init
   azd provision --resource-group rg-tender-engine
   azd deploy
   ```

### Option 2: Using Azure CLI

1. Create resource group:
   ```bash
   az group create --name rg-tender-engine --location swedencentral
   ```

2. Deploy the Bicep template to the resource group:
   ```bash
   az deployment group create \
     --resource-group rg-tender-engine \
     --template-file infra/main.bicep \
     --parameters @infra/main.parameters.json \
     --parameters environmentName=tender-engine \
     --parameters location=swedencentral
   ```

## Key Changes Made

1. **Target Scope**: Changed from `targetScope = 'subscription'` to `targetScope = 'resourceGroup'`
2. **Resource Group**: Removed resource group creation since it must exist beforehand
3. **Unique Token**: Changed from `subscription().id` to `resourceGroup().id` for resource naming
4. **Outputs**: Updated to use `resourceGroup().id` instead of created resource group reference

## Permissions Required

- **Resource Group Owner** or **Contributor** role
- **Storage Blob Data Contributor** (for deployment artifacts)
- Access to create Azure OpenAI, Container Apps, and other resources within the resource group

This configuration eliminates the need for subscription-level permissions and works with resource group-level access only.
