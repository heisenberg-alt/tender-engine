import streamlit as st
import pandas as pd
import os
import logging
from typing import Dict, List, Any
from datetime import datetime
from openai import AzureOpenAI

# Import Azure-based components
from agents.tender_agent import TenderAgent
from agents.company_agent import CompanyAgent
from vectorstore.cosmos_vector_store import CosmosDBVectorStore
from llm.azure_recommender_llm import AzureRecommenderLLM
from utils.config import load_config

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log')
        ]
    )

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

@st.cache_resource
def initialize_azure_components():
    """Initialize Azure components with caching"""
    try:
        config = load_config()
        
        # Initialize Azure OpenAI client
        openai_client = AzureOpenAI(
            api_key=config["AZURE_OPENAI_API_KEY"],
            api_version=config["AZURE_OPENAI_API_VERSION"],
            azure_endpoint=config["AZURE_OPENAI_ENDPOINT"]
        )
        
        # Initialize Cosmos DB vector store
        vector_store = CosmosDBVectorStore(
            cosmos_endpoint=config["COSMOS_DB_ENDPOINT"],
            cosmos_key=config["COSMOS_DB_KEY"],
            database_name=config["COSMOS_DB_DATABASE_NAME"],
            openai_client=openai_client,
            embedding_deployment=config["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]
        )
        
        # Initialize recommender LLM
        recommender = AzureRecommenderLLM(
            vector_store=vector_store,
            azure_openai_client=openai_client,
            deployment_name=config["AZURE_OPENAI_DEPLOYMENT_NAME"]
        )
        
        # Initialize agents
        tender_agent = TenderAgent(vector_store, recommender, config)
        company_agent = CompanyAgent(vector_store=vector_store)
        
        logger.info("Successfully initialized all Azure components")
        
        return {
            'config': config,
            'vector_store': vector_store,
            'recommender': recommender,
            'tender_agent': tender_agent,
            'company_agent': company_agent,
            'openai_client': openai_client
        }
        
    except Exception as e:
        logger.error(f"Error initializing Azure components: {str(e)}")
        st.error(f"Failed to initialize Azure components: {str(e)}")
        return None

# Set page config at the very beginning
st.set_page_config(page_title="Tender Recommender AI", layout="wide")

# Custom CSS styles to enhance the UI
st.markdown("""
    <style>
    body {
        background-color: #F4F7FB;
        color: #333;
        font-family: "Arial", sans-serif;
    }
    .stApp {
        background-color: #F4F7FB;
    }
    .sidebar .sidebar-content {
        background-color: #2D3E50;
        color: #FFF;
    }
    .sidebar .sidebar-header {
        color: #fff;
        font-size: 1.5rem;
        padding-bottom: 10px;
        border-bottom: 2px solid #efefef;
    }
    .stButton>button {
        background-color: #1E90FF;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1C75BB;
    }
    .stSelectbox, .stTextInput, .stSlider, .stMultiselect {
        border-radius: 5px;
        background-color: #fff;
        border: 1px solid #dcdcdc;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    }
    .stExpanderHeader {
        color: #1E90FF;
    }
    .stDataFrame {
        border-radius: 10px;
        background-color: #ffffff;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
    }
    .stAlert {
        background-color: #FFEB3B;
    }
    .stMarkdown {
        font-size: 1.2rem;
    }
    .stSpinner {
        background-color: #fff;
        color: #1E90FF;
    }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🎯 Tender Recommender AI - Azure Edition")
    
    # Initialize Azure components
    components = initialize_azure_components()
    if not components:
        st.error("Failed to initialize application. Please check your Azure configuration.")
        return
    
    config = components['config']
    vector_store = components['vector_store']
    recommender = components['recommender']
    tender_agent = components['tender_agent']
    company_agent = components['company_agent']
    
    # Show configuration status
    with st.expander("🔧 Azure Configuration Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Azure Services:**")
            st.write(f"✅ Cosmos DB: {config['COSMOS_DB_ENDPOINT'][:50]}...")
            st.write(f"✅ OpenAI: {config['AZURE_OPENAI_ENDPOINT'][:50]}...")
            st.write(f"✅ GPT Model: {config['AZURE_OPENAI_DEPLOYMENT_NAME']}")
        
        with col2:
            st.write("**Tender APIs:**")
            eu_ted_status = "✅ Configured" if config.get('EU_TED_API_KEY') else "⚠️ Not configured"
            swiss_status = "⚠️ Not implemented" if not config.get('SWISS_TENDER_API_KEY') else "✅ Configured"
            st.write(f"EU TED API: {eu_ted_status}")
            st.write(f"Swiss API: {swiss_status}")
            
        with col3:
            st.write("**Monitoring:**")
            ai_status = "✅ Enabled" if config.get('APPLICATIONINSIGHTS_CONNECTION_STRING') else "⚠️ Not configured"
            st.write(f"App Insights: {ai_status}")
            st.write(f"Log Level: {config['LOG_LEVEL']}")
    
    # Sidebar for actions
    with st.sidebar:
        st.header("🚀 Actions")
        action = st.radio(
            "Choose an action:",
            ["🔍 Search & Index Tenders", "🏢 Add Company Profile", "💡 Get Recommendations", "📊 View Data"]
        )
    
    if action == "🔍 Search & Index Tenders":
        st.header("Search and Index EU Tenders")
        
        with st.form("tender_search_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                search_query = st.text_input(
                    "Search Query", 
                    value="renewable energy infrastructure",
                    help="Enter keywords to search for relevant tenders in EU TED database"
                )
                max_results = st.slider("Maximum Results", 1, 50, 10)
                days_back = st.slider("Days Back", 7, 90, 30, help="How many days back to search")
                
            with col2:
                # EU Country selection
                eu_countries = [
                    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
                    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
                    "PL", "PT", "RO", "SK", "SI", "ES", "SE"
                ]
                selected_countries = st.multiselect(
                    "EU Countries (optional)",
                    options=eu_countries,
                    help="Select specific EU countries or leave empty for all"
                )
                
                # CPV Code categories
                cpv_categories = {
                    "Construction": ["45000000"],
                    "IT/Software": ["48000000", "72000000"],
                    "Healthcare": ["33000000"],
                    "Energy": ["31000000", "09000000"],
                    "Transport": ["34000000", "60000000"],
                    "Food/Agriculture": ["15000000", "03000000"],
                    "Environmental": ["90000000"],
                    "Education": ["80000000"]
                }
                
                selected_sectors = st.multiselect(
                    "Sectors (optional)",
                    options=list(cpv_categories.keys()),
                    help="Select sectors to filter by CPV codes"
                )
                
                # Convert selected sectors to CPV codes
                cpv_codes = []
                for sector in selected_sectors:
                    cpv_codes.extend(cpv_categories[sector])
            
            submit_button = st.form_submit_button("🔍 Search EU TED Tenders")
            
            if submit_button and search_query:
                with st.spinner("Searching EU TED database and indexing tenders..."):
                    try:
                        results = tender_agent.search_and_index_tenders(
                            query=search_query,
                            max_results=max_results,
                            country_codes=selected_countries if selected_countries else None,
                            cpv_codes=cpv_codes if cpv_codes else None,
                            days_back=days_back
                        )
                        
                        if results:
                            st.success(f"✅ Successfully indexed {len(results)} tenders from EU TED!")
                            
                            # Display results in a nice format
                            for i, result in enumerate(results, 1):
                                with st.expander(f"Tender {i}: {result.get('title', 'N/A')}", expanded=False):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.write(f"**Description:** {result.get('description', 'N/A')[:300]}...")
                                        st.write(f"**Organization:** {result.get('organization', 'N/A')}")
                                        st.write(f"**Source:** {result.get('source', 'N/A')}")
                                        st.write(f"**Location:** {result.get('location', 'N/A')}")
                                        if result.get('cpv_codes'):
                                            st.write(f"**CPV Codes:** {', '.join(result['cpv_codes'][:3])}")
                                        if result.get('sector'):
                                            st.write(f"**Sector:** {result['sector']}")
                                    
                                    with col2:
                                        if result.get('estimated_value'):
                                            currency = result.get('currency', 'EUR')
                                            st.metric("Estimated Value", f"{result['estimated_value']:,.0f} {currency}")
                                        if result.get('deadline'):
                                            st.write(f"**Deadline:** {result['deadline']}")
                                        if result.get('complexity_score'):
                                            st.metric("Complexity", f"{result['complexity_score']:.1%}")
                                        
                                        # Link to original tender
                                        if result.get('source_url'):
                                            st.markdown(f"[📋 View Original]({result['source_url']})")
                        else:
                            st.warning("No tenders found for the given query.")
                            st.info("💡 Try different keywords or expand the date range.")
                            
                    except Exception as e:
                        st.error(f"Error searching tenders: {str(e)}")
                        logger.error(f"Error in tender search: {str(e)}")
    
    elif action == "🏢 Add Company Profile":
        st.header("Add Company Profile")
        
        with st.form("company_profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input("Company Name", placeholder="e.g., TechCorp Solutions")
                company_description = st.text_area("Description", placeholder="Brief description of the company...")
                company_location = st.text_input("Location", placeholder="e.g., San Francisco, CA")
                company_size = st.selectbox("Company Size", ["Small", "Medium", "Large"])
            
            with col2:
                industries = st.text_area("Industries", placeholder="e.g., Technology, Renewable Energy").split(',')
                services = st.text_area("Services", placeholder="e.g., Software Development, Consulting").split(',')
                expertise = st.text_area("Expertise", placeholder="e.g., AI/ML, Cloud Computing").split(',')
            
            submit_company = st.form_submit_button("➕ Add Company Profile")
            
            if submit_company and company_name:
                with st.spinner("Adding company profile..."):
                    try:
                        company_data = {
                            "name": company_name,
                            "description": company_description,
                            "industry": [i.strip() for i in industries if i.strip()],
                            "services": [s.strip() for s in services if s.strip()],
                            "expertise": [e.strip() for e in expertise if e.strip()],
                            "location": company_location,
                            "size": company_size
                        }
                        
                        company_id = company_agent.add_company_profile(company_data)
                        st.success(f"✅ Company profile added successfully! ID: {company_id}")
                        
                        # Show the added profile
                        st.json(company_data)
                        
                    except Exception as e:
                        st.error(f"Error adding company profile: {str(e)}")
                        logger.error(f"Error adding company: {str(e)}")
    
    elif action == "💡 Get Recommendations":
        st.header("AI-Powered Recommendations")
        
        tab1, tab2 = st.tabs(["🏢 Tenders for Company", "🎯 Companies for Tender"])
        
        with tab1:
            st.subheader("Find Tenders for Your Company")
            
            # Get available companies
            companies = vector_store.get_all_companies(limit=50)
            
            if companies:
                company_options = {f"{comp['name']} ({comp['location']})": comp for comp in companies}
                selected_company_name = st.selectbox("Select Company", list(company_options.keys()))
                
                if selected_company_name and st.button("🔍 Find Matching Tenders"):
                    selected_company = company_options[selected_company_name]
                    
                    with st.spinner("Analyzing tenders and generating recommendations..."):
                        try:
                            recommendations = recommender.recommend_tenders_for_company(
                                company_profile=selected_company,
                                max_recommendations=5
                            )
                            
                            if recommendations:
                                st.success(f"Found {len(recommendations)} recommended tenders!")
                                
                                for i, rec in enumerate(recommendations, 1):
                                    tender = rec['tender']
                                    analysis = rec['analysis']
                                    
                                    with st.expander(f"🎯 Recommendation {i}: {tender.get('title', 'N/A')}", expanded=i==1):
                                        # Match score
                                        match_score = analysis.get('match_score', 0)
                                        st.metric(
                                            "Match Score", 
                                            f"{match_score:.1%}",
                                            delta=f"Vector Similarity: {rec.get('vector_similarity', 0):.3f}"
                                        )
                                        
                                        # Tender details
                                        col1, col2 = st.columns([2, 1])
                                        
                                        with col1:
                                            st.write(f"**Organization:** {tender.get('organization', 'N/A')}")
                                            st.write(f"**Description:** {tender.get('description', 'N/A')[:300]}...")
                                            st.write(f"**Location:** {tender.get('location', 'N/A')}")
                                        
                                        with col2:
                                            if tender.get('estimated_value'):
                                                st.metric("Value", f"${tender['estimated_value']:,.0f}")
                                            st.write(f"**Deadline:** {tender.get('deadline', 'N/A')}")
                                        
                                        # AI Analysis
                                        st.write("**🤖 AI Analysis:**")
                                        st.info(analysis.get('reasoning', 'No analysis available'))
                                        
                                        if analysis.get('key_strengths'):
                                            st.write("**✅ Key Strengths:**")
                                            for strength in analysis['key_strengths']:
                                                st.write(f"• {strength}")
                                        
                                        if analysis.get('potential_challenges'):
                                            st.write("**⚠️ Potential Challenges:**")
                                            for challenge in analysis['potential_challenges']:
                                                st.write(f"• {challenge}")
                                        
                                        st.write(f"**💭 Recommendation:** {analysis.get('recommendation', 'N/A')}")
                            else:
                                st.warning("No suitable tender recommendations found.")
                                
                        except Exception as e:
                            st.error(f"Error generating recommendations: {str(e)}")
                            logger.error(f"Error in recommendations: {str(e)}")
            else:
                st.warning("No companies found. Please add some company profiles first.")
        
        with tab2:
            st.subheader("Find Companies for Tender")
            
            # Get available tenders
            tenders = vector_store.get_all_tenders(limit=50)
            
            if tenders:
                tender_options = {f"{tender['title'][:60]}... ({tender.get('location', 'N/A')})": tender for tender in tenders}
                selected_tender_name = st.selectbox("Select Tender", list(tender_options.keys()))
                
                if selected_tender_name and st.button("🔍 Find Suitable Companies"):
                    selected_tender = tender_options[selected_tender_name]
                    
                    with st.spinner("Analyzing companies and generating recommendations..."):
                        try:
                            recommendations = recommender.recommend_companies_for_tender(
                                tender_data=selected_tender,
                                max_recommendations=5
                            )
                            
                            if recommendations:
                                st.success(f"Found {len(recommendations)} recommended companies!")
                                
                                for i, rec in enumerate(recommendations, 1):
                                    company = rec['company']
                                    analysis = rec['analysis']
                                    
                                    with st.expander(f"🏢 Recommendation {i}: {company.get('name', 'N/A')}", expanded=i==1):
                                        # Match score
                                        match_score = analysis.get('match_score', 0)
                                        st.metric(
                                            "Suitability Score", 
                                            f"{match_score:.1%}",
                                            delta=f"Vector Similarity: {rec.get('vector_similarity', 0):.3f}"
                                        )
                                        
                                        # Company details
                                        col1, col2 = st.columns([2, 1])
                                        
                                        with col1:
                                            st.write(f"**Description:** {company.get('description', 'N/A')}")
                                            st.write(f"**Industries:** {', '.join(company.get('industry', []))}")
                                            st.write(f"**Services:** {', '.join(company.get('services', []))}")
                                            st.write(f"**Location:** {company.get('location', 'N/A')}")
                                        
                                        with col2:
                                            st.write(f"**Size:** {company.get('size', 'N/A')}")
                                            if company.get('expertise'):
                                                st.write(f"**Expertise:** {', '.join(company['expertise'][:3])}")
                                        
                                        # AI Analysis
                                        st.write("**🤖 AI Analysis:**")
                                        st.info(analysis.get('reasoning', 'No analysis available'))
                                        
                                        if analysis.get('key_strengths'):
                                            st.write("**✅ Key Strengths:**")
                                            for strength in analysis['key_strengths']:
                                                st.write(f"• {strength}")
                                        
                                        if analysis.get('potential_challenges'):
                                            st.write("**⚠️ Potential Challenges:**")
                                            for challenge in analysis['potential_challenges']:
                                                st.write(f"• {challenge}")
                                        
                                        st.write(f"**💭 Recommendation:** {analysis.get('recommendation', 'N/A')}")
                            else:
                                st.warning("No suitable company recommendations found.")
                                
                        except Exception as e:
                            st.error(f"Error generating recommendations: {str(e)}")
                            logger.error(f"Error in recommendations: {str(e)}")
            else:
                st.warning("No tenders found. Please search and index some tenders first.")
    
    elif action == "📊 View Data":
        st.header("Data Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Tenders")
            tenders = vector_store.get_all_tenders(limit=100)
            st.metric("Total Tenders", len(tenders))
            
            if tenders:
                # Create DataFrame for display
                tender_df = pd.DataFrame([
                    {
                        'Title': t.get('title', 'N/A')[:50] + '...',
                        'Organization': t.get('organization', 'N/A'),
                        'Location': t.get('location', 'N/A'),
                        'Value': f"${t.get('estimated_value', 0):,.0f}" if t.get('estimated_value') else 'N/A',
                        'Deadline': t.get('deadline', 'N/A')
                    }
                    for t in tenders[:20]  # Show first 20
                ])
                st.dataframe(tender_df, use_container_width=True)
        
        with col2:
            st.subheader("🏢 Companies")
            companies = vector_store.get_all_companies(limit=100)
            st.metric("Total Companies", len(companies))
            
            if companies:
                # Create DataFrame for display
                company_df = pd.DataFrame([
                    {
                        'Name': c.get('name', 'N/A'),
                        'Industry': ', '.join(c.get('industry', [])[:2]),
                        'Location': c.get('location', 'N/A'),
                        'Size': c.get('size', 'N/A')
                    }
                    for c in companies[:20]  # Show first 20
                ])
                st.dataframe(company_df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 **Tender Recommender AI** - Powered by Azure AI Services | Built with Streamlit")
    
if __name__ == "__main__":
    main()