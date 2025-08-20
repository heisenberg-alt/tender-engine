import streamlit as st
import pandas as pd
from datetime import datetime

def show_page():
    """
    Vector Approach page - Traditional tender recommendation system
    """
    st.header("📊 Vector Approach")
    st.markdown("Traditional vector-based tender matching and company profile management")

    # Mock data for demonstration
    mock_tenders = [
        {
            "id": "T001",
            "title": "Software Development Services",
            "description": "Development of enterprise software solutions",
            "value": "$50,000 - $100,000",
            "deadline": "2024-03-15",
            "industry": "Technology"
        },
        {
            "id": "T002", 
            "title": "Marketing Campaign Management",
            "description": "Digital marketing and campaign strategy",
            "value": "$25,000 - $50,000",
            "deadline": "2024-02-28",
            "industry": "Marketing"
        },
        {
            "id": "T003",
            "title": "Infrastructure Consulting",
            "description": "Cloud infrastructure assessment and migration",
            "value": "$75,000 - $150,000",
            "deadline": "2024-04-01",
            "industry": "Technology"
        }
    ]

    # Dashboard Section
    st.subheader("🏠 Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Available Tenders", "12", "3")
    
    with col2:
        st.metric("Recommended for You", "5", "2")
    
    with col3:
        st.metric("Application Deadline", "5 days", "-1")
    
    st.subheader("Recent Tenders")
    df = pd.DataFrame(mock_tenders)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Tender Search Section
    with st.expander("🔍 Tender Search", expanded=False):
        st.subheader("Search Tenders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            industry_filter = st.selectbox("Industry", ["All", "Technology", "Marketing", "Healthcare", "Finance"])
            
        with col2:
            value_range = st.selectbox("Value Range", ["All", "$0-$25k", "$25k-$50k", "$50k-$100k", "$100k+"])
        
        search_query = st.text_input("Search keywords")
        
        if st.button("Search Tenders"):
            st.success("Search completed! Found 8 matching tenders.")
            filtered_df = df
            if industry_filter != "All":
                filtered_df = df[df['industry'] == industry_filter]
            st.dataframe(filtered_df, use_container_width=True)

    st.markdown("---")
    
    # Company Profile Section
    with st.expander("🏢 Company Profile", expanded=False):
        st.subheader("Company Profile")
        
        with st.form("company_profile"):
            company_name = st.text_input("Company Name", "Your Company Ltd.")
            industry = st.selectbox("Primary Industry", ["Technology", "Marketing", "Healthcare", "Finance", "Other"])
            company_size = st.selectbox("Company Size", ["1-10", "11-50", "51-200", "201-1000", "1000+"])
            specialties = st.text_area("Specialties and Keywords", "Software development, cloud computing, AI/ML")
            
            if st.form_submit_button("Update Profile"):
                st.success("Profile updated successfully!")

    # Info sidebar for this approach
    with st.sidebar:
        st.markdown("---")
        st.header("🚀 Azure Deployment Info")
        st.info("This app is successfully running on Azure Container Apps!")
        
        st.header("📊 System Status")
        st.success("✅ Application: Running")
        st.success("✅ Database: Simulated")
        st.success("✅ AI Engine: Mock Mode")
        
        st.header("🔧 Environment")
        st.write(f"**Deployed at:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.write("**Platform:** Azure Container Apps")
        st.write("**Region:** West Europe")

    # Footer
    st.markdown("---")
    st.markdown("*Vector Approach - Traditional Tender Matching*")
