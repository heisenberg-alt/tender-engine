import streamlit as st
import pandas as pd
import os
from agents.tender_agent import TenderAgent
from agents.company_agent import CompanyAgent
from vectorstore.chromadb_store import ChromaDBStore
from llm.recommender_llm import RecommenderLLM
from utils.config import load_config
from datetime import datetime

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
    st.title("Tender Recommender AI")
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    vector_store = ChromaDBStore(config["VECTOR_DB_PATH"], config["VECTOR_DIMENSION"])
    
    # Fix: Get API key with fallback options
    api_key = config.get("FIRECRAWL_API_KEY", config.get("API_KEY", ""))
    
    # Pass the API key directly to TenderAgent
    tender_agent = TenderAgent(api_key, vector_store)
    company_agent = CompanyAgent(vector_store=vector_store)
    recommender = RecommenderLLM(vector_store, config)
    
    # Sidebar for actions
    with st.sidebar:
        st.header("Actions")
        action = st.radio(
            "Select Action",
            ["Available Tenders", "Search New Tenders", "Upload Company Profile", "Get Recommendations"],
            index=0
        )
    
    # Default view: Show all available tenders
    if action == "Available Tenders":
        st.header("Available Tenders")
        
        # Get all tenders from vector store
        all_tenders = vector_store.get_all_tenders()
        
        if all_tenders:
            # Create DataFrame for better display
            tender_list = []
            for tender in all_tenders:
                # Convert deadline to datetime for sorting
                deadline_date = None
                try:
                    if tender.get("deadline"):
                        deadline_date = datetime.fromisoformat(tender["deadline"])
                except ValueError:
                    pass
                
                tender_list.append({
                    "ID": tender.get("id", ""),
                    "Title": tender.get("title", ""),
                    "Organization": tender.get("organization", ""),
                    "Location": tender.get("location", ""),
                    "Deadline": deadline_date,
                    "Value": f"{tender.get('estimated_value', 'N/A')} {tender.get('currency', '')}",
                    "Category": ", ".join(tender.get("category", [])) if isinstance(tender.get("category"), list) else tender.get("category", ""),
                    "Source": tender.get("source", "")
                })
            
            # Create DataFrame and sort by deadline
            tenders_df = pd.DataFrame(tender_list)
            if not tenders_df.empty and "Deadline" in tenders_df.columns:
                tenders_df = tenders_df.sort_values(by="Deadline", ascending=True)
            
            # Add filter options
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_categories = st.multiselect(
                    "Filter by Category",
                    options=list(set([cat for tender in tender_list for cat in tender.get("Category", "").split(", ") if cat]))
                )
            
            with col2:
                filter_locations = st.multiselect(
                    "Filter by Location",
                    options=list(set([tender.get("Location", "") for tender in tender_list if tender.get("Location")]))
                )
                
            with col3:
                show_expired = st.checkbox("Show Expired Tenders", value=False)
            
            # Apply filters
            filtered_df = tenders_df.copy()
            
            if filter_categories:
                filtered_df = filtered_df[filtered_df["Category"].apply(lambda x: any(cat in x for cat in filter_categories))]
                
            if filter_locations:
                filtered_df = filtered_df[filtered_df["Location"].isin(filter_locations)]
                
            if not show_expired:
                current_date = datetime.now()
                filtered_df = filtered_df[filtered_df["Deadline"].apply(lambda x: x > current_date if x is not None else True)]
            
            # Display tender list
            st.dataframe(filtered_df, use_container_width=True)
            
            # Display selected tender details
            if st.session_state.get("selected_tender_id"):
                selected_tender = next((t for t in all_tenders if t.get("id") == st.session_state.selected_tender_id), None)
                if selected_tender:
                    with st.expander("Selected Tender Details", expanded=True):
                        st.subheader(selected_tender.get("title", "No Title"))
                        st.write(f"**Organization:** {selected_tender.get('organization', 'N/A')}")
                        st.write(f"**Deadline:** {selected_tender.get('deadline', 'N/A')}")
                        st.write(f"**Value:** {selected_tender.get('estimated_value', 'N/A')} {selected_tender.get('currency', '')}")
                        st.write(f"**Location:** {selected_tender.get('location', 'N/A')}")
                        st.write(f"**Category:** {', '.join(selected_tender.get('category', []))}")
                        st.write(f"**Source:** {selected_tender.get('source', 'N/A')}")
                        st.write(f"**Source URL:** {selected_tender.get('source_url', 'N/A')}")
                        
                        st.subheader("Description")
                        st.write(selected_tender.get("description", "No description available"))
                        
                        if selected_tender.get("attachments"):
                            st.subheader("Attachments")
                            for attachment in selected_tender.get("attachments", []):
                                st.write(f"- [{attachment.get('name', 'Document')}]({attachment.get('url', '#')})")
            
            # Allow user to select a tender for more details
            selected_id = st.selectbox(
                "Select tender for detailed view",
                options=[tender.get("id", "") for tender in all_tenders],
                format_func=lambda x: next((t.get("title", "No Title") for t in all_tenders if t.get("id") == x), "")
            )
            
            if selected_id:
                st.session_state.selected_tender_id = selected_id
                st.experimental_rerun()
                
        else:
            st.info("No tenders found in database. Please use 'Search New Tenders' to add tenders.")
            
            # Quick search button
            if st.button("Search for new tenders now"):
                st.session_state.action = "Search New Tenders"
                st.experimental_rerun()
    
    elif action == "Search New Tenders":
        st.header("Search & Index New Tenders")
        
        col1, col2 = st.columns(2)
        with col1:
            search_query = st.text_input("Search Keywords", "construction tender government")
            max_results = st.number_input("Maximum Results", min_value=1, max_value=50, value=5)
        
        with col2:
            countries = st.multiselect("Countries", ["USA", "UK", "EU", "Canada", "Australia", "Global"])
            date_range = st.slider("Date Range (days)", min_value=1, max_value=90, value=30)
        
        if st.button("Search & Index Tenders"):
            with st.spinner("Searching for tenders..."):
                # Convert countries list to proper format for the API
                country_codes = []
                if countries:
                    country_codes = countries
                
                results = tender_agent.search_and_store_tenders(
                    keywords=search_query.split(),
                    countries=country_codes,
                    max_results=max_results
                )
                
                if results:
                    st.success(f"Successfully indexed {results} tenders")
                    
                    # Show all tenders after indexing
                    st.session_state.action = "Available Tenders"
                    st.experimental_rerun()
                else:
                    st.warning("No tenders found matching your criteria")
    
    elif action == "Upload Company Profile":
        st.header("Upload Company Profile")
        
        profile_tab, manual_tab = st.tabs(["Upload Profile", "Manual Entry"])
        
        with profile_tab:
            uploaded_file = st.file_uploader("Upload company profile document", type=["pdf", "docx", "txt"])
            company_name = st.text_input("Company Name")
            
            if uploaded_file and company_name:
                if st.button("Process Company Profile"):
                    with st.spinner("Processing company profile..."):
                        # Save uploaded file temporarily
                        temp_path = os.path.join("data/temp/", uploaded_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.read())
                        
                        # Process company info and upload to the vector store
                        company_agent.process_company_profile(temp_path, company_name)
                        st.success("Company profile uploaded and indexed successfully!")
            else:
                st.warning("Please upload a file and enter the company name.")
        
        with manual_tab:
            st.markdown("You can manually enter company information here.")
            manual_company_name = st.text_input("Company Name (Manual)")
            manual_profile_desc = st.text_area("Company Description")
            
            if st.button("Submit Manually"):
                if manual_company_name and manual_profile_desc:
                    with st.spinner("Saving company info..."):
                        company_agent.add_company_profile(manual_company_name, manual_profile_desc)
                        st.success("Company profile saved manually!")
    
    elif action == "Get Recommendations":
        st.header("Get Tender Recommendations")
        
        query = st.text_input("Enter your query or company profile", "")
        if query:
            with st.spinner("Getting recommendations..."):
                recommendations = recommender.get_recommendations(query)
                
                if recommendations:
                    st.success(f"Found {len(recommendations)} recommendations.")
                    st.write(recommendations)
                else:
                    st.warning("No recommendations found.")
    
if __name__ == "__main__":
    main()