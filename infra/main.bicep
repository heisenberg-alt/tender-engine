targetScope = 'resourceGroup'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Azure OpenAI deployment name for text completion')
param azureOpenAiDeploymentName string = 'gpt-4o'

@description('Azure OpenAI mini deployment name for lighter tasks')
param azureOpenAigpt5MiniDeploymentName string = 'gpt-4o-mini'

@description('Azure OpenAI o4-mini deployment name for reasoning tasks')
param azureOpenAio4MiniDeploymentName string = 'gpt-35-turbo'

@description('Azure OpenAI embedding deployment name')
param azureOpenAiEmbeddingDeploymentName string = 'text-embedding-3-small'

@description('Log level for application')
param logLevel string = 'INFO'

// Generate a unique token for resource names
var resourceToken = uniqueString(resourceGroup().id, location, environmentName)
var resourcePrefix = 'tra' // tender-recommender-ai shortened

// Deploy resources to the current resource group
module resources 'resources.bicep' = {
  name: 'resources'
  params: {
    location: location
    environmentName: environmentName
    resourceToken: resourceToken
    resourcePrefix: resourcePrefix
    azureOpenAiDeploymentName: azureOpenAiDeploymentName
    azureOpenAigpt5MiniDeploymentName: azureOpenAigpt5MiniDeploymentName
    azureOpenAio4MiniDeploymentName: azureOpenAio4MiniDeploymentName
    azureOpenAiEmbeddingDeploymentName: azureOpenAiEmbeddingDeploymentName
    logLevel: logLevel
  }
}

// Outputs
output RESOURCE_GROUP_ID string = resourceGroup().id
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.AZURE_CONTAINER_REGISTRY_ENDPOINT
output COSMOS_DB_ENDPOINT string = resources.outputs.COSMOS_DB_ENDPOINT
output AZURE_OPENAI_ENDPOINT string = resources.outputs.AZURE_OPENAI_ENDPOINT
output AZURE_OPENAI_API_KEY string = resources.outputs.AZURE_OPENAI_API_KEY
output AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT string = resources.outputs.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
output AZURE_DOCUMENT_INTELLIGENCE_KEY string = resources.outputs.AZURE_DOCUMENT_INTELLIGENCE_KEY
output AZURE_OPENAI_DEPLOYMENT_NAME string = azureOpenAiDeploymentName
output AZURE_OPENAI_GPT5MINI_DEPLOYMENT_NAME string = azureOpenAigpt5MiniDeploymentName
output AZURE_OPENAI_o4_MINI_DEPLOYMENT_NAME string = azureOpenAio4MiniDeploymentName
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME string = azureOpenAiEmbeddingDeploymentName
output APPLICATIONINSIGHTS_CONNECTION_STRING string = resources.outputs.APPLICATIONINSIGHTS_CONNECTION_STRING
output TENDER_RECOMMENDER_WEB_URI string = resources.outputs.TENDER_RECOMMENDER_WEB_URI
