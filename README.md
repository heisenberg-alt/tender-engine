# 🧠 Tender Recommender AI

> An intelligent AI-powered system to analyze tenders and company profiles, then recommend relevant opportunities using LLMs, embeddings, and structured matching.

---

## 🚀 Overview

Tender Recommender AI is an end-to-end system that:
- Extracts key information from tender documents and company profiles using Large Language Models (LLMs).
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

Tool
Purpose
Python 3.11
Core language
Streamlit
UI and interaction layer
Ollama
LLM & embedding model runtime
ChromaDB
Vector database
LangChain
LLM orchestration
dotenv
Environment config loader

🤝 Contributing

We welcome contributions! Please fork the repo, create a new branch, and make your changes via PR.

⸻

🧑‍💻 Author

Subhash Govindaraj
GitHub • LinkedIn
