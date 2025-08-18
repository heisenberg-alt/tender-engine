# 🎯 Tender Recommender AI - Azure Production Edition

A production-ready AI-powered tender recommendation system built on Microsoft Azure, designed to match companies with relevant government tenders using advanced vector search and GPT-4 analysis.

## 🏗️ Azure Architecture

This application leverages the following Azure services:

- **Azure Cosmos DB**: Vector-enabled NoSQL database for tender and company data
- **Azure OpenAI**: GPT-4o for intelligent analysis and text-embedding-3-small for vector embeddings
- **Azure Container Apps**: Serverless container hosting with auto-scaling
- **Azure Container Registry**: Secure container image storage
- **Azure Application Insights**: End-to-end observability and monitoring
- **Azure Key Vault**: Secure secrets management
- **Azure Monitor**: Centralized logging and alerting

## 🚀 Features

- **🔍 Smart Tender Discovery**: AI-powered search and indexing of government tenders
- **🏢 Company Profile Management**: Structured company data with vector embeddings
- **💡 Intelligent Matching**: Vector similarity search with GPT-4 analysis
- **📊 Production Monitoring**: Real-time metrics and distributed tracing
- **🔒 Enterprise Security**: Managed identities and Key Vault integration
- **⚡ Auto-scaling**: Container Apps with automatic resource optimization

## � Prerequisites

- Azure CLI (`az`) version 2.60+
- Azure Developer CLI (`azd`) version 1.16+
- Docker (optional - Azure can build images in the cloud)
- An Azure subscription with appropriate permissions

## 🛠️ Quick Start

### 1. Clone and Initialize

```bash
git clone <repository-url>
cd tender-recommender-ai
azd init
```

### 2. Deploy to Azure

```bash
azd up
```

This command will:
- Create all Azure resources using Bicep templates
- Build and deploy the container image
- Configure environment variables and secrets
- Set up monitoring and logging

### 3. Configure Deployment

During deployment, you'll be prompted for:
- **Environment Name**: Unique identifier for your deployment
- **Azure Region**: Choose your preferred region (e.g., `eastus`, `westeurope`)
- **Azure Subscription**: Select your target subscription

## 🏗️ Infrastructure as Code

The infrastructure is defined using Bicep templates:

- `infra/main.bicep`: Subscription-scoped resources and orchestration
- `infra/resources.bicep`: All Azure resources with proper configuration
- `infra/main.parameters.json`: Environment-specific parameters

### Key Infrastructure Features

- **Vector Search**: Cosmos DB configured with vector indexing for similarity search
- **Security**: Managed identities, Key Vault, and RBAC permissions
- **Observability**: Application Insights with automatic instrumentation
- **Networking**: Container Apps with CORS and health checks
- **Scalability**: Auto-scaling based on CPU and memory metrics
- Embeds and stores data in a vector database for similarity searches.
- Recommends tenders to companies based on expertise, size, past projects, location, and compliance.
- Built with **LangChain**, **Ollama**, **ChromaDB**, and **Streamlit**.

---

## 🧩 Features

- 🔍 **Tender Extraction**: Uses LLM to parse tender details into a structured format.
- 🏢 **Company Profile Analysis**: Extracts company expertise, certifications, and projects from documents.
- 🤝 **Tender Matching**: Calculates match scores between tenders and company profiles.
- 🧠 **LLM-Powered Reasoning**: Uses prompt engineering to give detailed recommendation justifications.
- 🗃️ **Vector Storage**: Stores embeddings with `ChromaDB` for retrieval and similarity search.
- 🖥️ **Streamlit UI**: Clean interface for uploading tenders, company data, and viewing matches.

---

## 📁 Project Structure

ender-recommender-ai/
│
├── app.py                       # Streamlit application entrypoint
├── config.py                   # Schemas, prompts, environment configs
├── agents/
│   └── tender_agent.py         # Core LLM agent for tender extraction
├── utils/
│   ├── embedding.py            # Embedding + vector store logic
│   ├── matching.py             # Scoring logic for matching tenders & companies
│   └── io_utils.py             # File reading, parsing helpers
├── data/
│   └── vector_db/              # ChromaDB local storage
├── .env                        # Environment variables (e.g., API keys)
└── README.md                   # Project documentation

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/SubhashGovindharaj/tender-recommender-ai.git
cd tender-recommender-ai

2. Create a Virtual Environment

conda create -n tender-ai python=3.11
conda activate tender-ai

Or using venv:

python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

. Add Environment Variables

Create a .env file:

OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
VECTOR_DB_PATH=./data/vector_db
VECTOR_DIMENSION=384
FIRECRAWL_API_KEY=your_api_key_here

🧠 How It Works

1. Tender Analysis

Uses the prompt:

TENDER_EXTRACTION_PROMPT = """
You are a tender analysis system...
"""

 Extracts structured fields like category, requirements, challenges, etc.

2. Company Profile Extraction

Parses uploaded company documents into schema-defined JSON using:

COMPANY_PROFILE_EXTRACTION_PROMPT = """
You are a company profile analysis system...
"""

3. Embedding and Storage
	•	Embeds both tenders and company profiles using Ollama (nomic-embed-text)
	•	Stores them in ChromaDB for fast retrieval and similarity matching.

4. Matching & Recommendation
	•	Compares industry, expertise, location, certifications, and scale.
	•	Generates a match score and reasoning via:

TENDER_RECOMMENDATION_PROMPT = """
You are a tender recommendation system...
"""

🖥️ Run the App
streamlit run app.py

📌 Example Use Cases
	•	Government agencies uploading tenders and recommending to potential vendors.
	•	Companies exploring which tenders best fit their capabilities.
	•	Automation of pre-bid analysis using AI.

📊 Technologies Used
	•	🐍 Python 3.11 – Core language powering the backend logic
	•	🌐 Streamlit – Builds the interactive web UI
	•	🦙 Ollama – Runs LLMs and embedding models locally
	•	🧠 LangChain – Manages LLM flows and agent behavior
	•	🧾 ChromaDB – Stores and retrieves document embeddings
	•	🔐 python-dotenv – Loads environment variables securely


🤝 Contributing

We welcome contributions! Please fork the repo, create a new branch, and make your changes via PR.

⸻

🧑‍💻 Author

Subhash Govindaraj
GitHub • LinkedIn
