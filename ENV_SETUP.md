# Environment Setup Guide

## Required Environment Variables

Before running the application, you need to set up the following environment variables. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Azure Configuration
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI service endpoint
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key  
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Name of your GPT deployment (default: gpt-4o)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`: Name of your embedding deployment (default: text-embedding-3-small)

### Cosmos DB Configuration
- `COSMOS_DB_ENDPOINT`: Your Azure Cosmos DB endpoint
- `COSMOS_DB_KEY`: Your Azure Cosmos DB primary key
- `COSMOS_DB_DATABASE_NAME`: Database name (default: tender-recommender)

### Tender API Configuration
- `EU_TED_API_KEY`: Your EU TED API key for accessing European tender data
- `SWISS_TENDER_API_KEY`: (Optional) Swiss tender API key for future integration

### Optional Configuration
- `AZURE_KEY_VAULT_URL`: For production deployments using Azure Key Vault
- `RAW_TENDERS_DIR`: Directory for storing raw tender data (default: data/raw_tenders)

## Security Notes

⚠️ **Important**: Never commit your `.env` file to version control. It contains sensitive API keys and credentials.

- The `.env` file is already included in `.gitignore`
- Use `.env.example` as a template for required variables
- For production deployments, use Azure Key Vault to manage secrets securely
