targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Name of the resource group')
param resourceGroupName string = 'rg-${environmentName}'

@description('Azure OpenAI deployment name for text completion')
param azureOpenAiDeploymentName string = 'gpt-4o'

@description('Azure OpenAI embedding deployment name')
param azureOpenAiEmbeddingDeploymentName string = 'text-embedding-3-small'

@description('Log level for application')
param logLevel string = 'INFO'

// Generate a unique token for resource names
var resourceToken = uniqueString(subscription().id, location, environmentName)
var resourcePrefix = 'tra' // tender-recommender-ai shortened

// Create resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    'azd-env-name': environmentName
  }
}

// Deploy resources to the resource group
module resources 'resources.bicep' = {
  name: 'resources'
  scope: resourceGroup
  params: {
    location: location
    environmentName: environmentName
    resourceToken: resourceToken
    resourcePrefix: resourcePrefix
    azureOpenAiDeploymentName: azureOpenAiDeploymentName
    azureOpenAiEmbeddingDeploymentName: azureOpenAiEmbeddingDeploymentName
    logLevel: logLevel
  }
}

// Outputs
output RESOURCE_GROUP_ID string = resourceGroup.id
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.AZURE_CONTAINER_REGISTRY_ENDPOINT
output COSMOS_DB_ENDPOINT string = resources.outputs.COSMOS_DB_ENDPOINT
output AZURE_OPENAI_ENDPOINT string = resources.outputs.AZURE_OPENAI_ENDPOINT
output AZURE_OPENAI_DEPLOYMENT_NAME string = azureOpenAiDeploymentName
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME string = azureOpenAiEmbeddingDeploymentName
output APPLICATIONINSIGHTS_CONNECTION_STRING string = resources.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output TENDER_RECOMMENDER_WEB_URI string = resources.outputs.TENDER_RECOMMENDER_WEB_URI
