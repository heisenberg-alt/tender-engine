# Tender AI - Architecture Diagram

```mermaid
graph TB
    subgraph "Internet"
        User[👤 User]
        TEDAPI[🇪🇺 EU TED API<br/>Official Tender Data]
    end

    subgraph "Azure Cloud Platform"
        subgraph "Container Services"
            ACA[🚀 Azure Container Apps<br/>Streamlit Application<br/>Auto-scaling]
            ACR[📦 Azure Container Registry<br/>Container Images]
        end

        subgraph "AI & Analytics"
            AOAI[🧠 Azure OpenAI<br/>• GPT-4o (Analysis)<br/>• text-embedding-3-small]
            COSMOS[🌍 Azure Cosmos DB<br/>• Vector Database<br/>• Tender & Company Data<br/>• Similarity Search]
        end

        subgraph "Security & Management"
            KV[🔒 Azure Key Vault<br/>API Keys & Secrets]
            MI[🔐 Managed Identity<br/>Passwordless Auth]
        end

        subgraph "Monitoring & Observability"
            AI[📊 Application Insights<br/>Performance Metrics]
            MON[📈 Azure Monitor<br/>Logging & Alerting]
            LA[📋 Log Analytics<br/>Centralized Logs]
        end

        subgraph "Infrastructure"
            RG[🏗️ Resource Group<br/>tender-ai-prod]
            VNET[🌐 Virtual Network<br/>Secure Networking]
        end
    end

    %% User Interactions
    User -->|Browse & Search| ACA
    User -->|View Recommendations| ACA

    %% Data Flow
    ACA -->|Crawl Tenders| TEDAPI
    ACA -->|Generate Embeddings| AOAI
    ACA -->|Store/Query Vectors| COSMOS
    ACA -->|Analyze Matches| AOAI
    
    %% Security & Secrets
    ACA -->|Retrieve Secrets| KV
    MI -->|Access Control| KV
    MI -->|Database Auth| COSMOS
    MI -->|AI Service Auth| AOAI

    %% Container Management
    ACA -->|Pull Images| ACR

    %% Monitoring
    ACA -->|Telemetry| AI
    ACA -->|Logs| MON
    AI -->|Detailed Logs| LA
    MON -->|Metrics| LA
    COSMOS -->|Database Metrics| MON
    AOAI -->|API Metrics| MON

    %% Infrastructure
    ACA -.->|Hosted in| RG
    COSMOS -.->|Hosted in| RG
    AOAI -.->|Hosted in| RG
    KV -.->|Hosted in| RG
    ACR -.->|Hosted in| RG
    VNET -.->|Network Security| ACA

    %% Styling
    classDef azure fill:#0078d4,stroke:#ffffff,stroke-width:2px,color:#ffffff
    classDef ai fill:#ff6b35,stroke:#ffffff,stroke-width:2px,color:#ffffff
    classDef data fill:#00bcf2,stroke:#ffffff,stroke-width:2px,color:#ffffff
    classDef security fill:#68217a,stroke:#ffffff,stroke-width:2px,color:#ffffff
    classDef monitor fill:#ffb900,stroke:#ffffff,stroke-width:2px,color:#ffffff
    classDef external fill:#107c10,stroke:#ffffff,stroke-width:2px,color:#ffffff

    class ACA,ACR azure
    class AOAI,AI ai
    class COSMOS,LA data
    class KV,MI security
    class MON monitor
    class User,TEDAPI external
```

## Data Flow Description

### 1. Tender Discovery & Processing
```
EU TED API → Azure Container Apps → Azure OpenAI (Embeddings) → Cosmos DB
```

### 2. Company Profile Management
```
User Input → Streamlit UI → Azure OpenAI (Embeddings) → Cosmos DB
```

### 3. Intelligent Matching
```
Cosmos DB (Vector Search) → Azure OpenAI (GPT-4o Analysis) → Streamlit UI → User
```

### 4. Security & Monitoring
```
Managed Identity → Key Vault → All Services
All Services → Application Insights → Log Analytics → Azure Monitor
```

## Architecture Principles

- **🔒 Security First**: Managed identities and Key Vault for passwordless authentication
- **📊 Observability**: End-to-end monitoring with Application Insights and Azure Monitor  
- **⚡ Scalability**: Container Apps with automatic scaling based on demand
- **🌐 Global Reach**: Multi-region deployment capability with Cosmos DB
- **🧠 AI-Native**: Vector search and GPT-4o for intelligent tender matching
- **💰 Cost Optimized**: Pay-per-use serverless containers and AI services
