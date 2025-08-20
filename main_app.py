import streamlit as st

# Configure the page
st.set_page_config(
    page_title="Tender Recommendation Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create the main navigation
st.title("🎯 Tender Recommendation Engine")
st.markdown("### AI-Powered Tender Analysis & Company Matching")

# Sidebar navigation
with st.sidebar:
    st.title("📋 Navigation")
    page = st.selectbox(
        "Choose Approach",
        ["Vector Approach", "Reasoning Model Approach"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 🔧 About the Approaches")
    
    if page == "Vector Approach":
        st.info("""
        **Vector Approach**
        - Traditional vector-based matching
        - Company profile management
        - Tender search and filtering
        - Dashboard with metrics
        """)
    else:
        st.info("""
        **Reasoning Model Approach**
        - AI-powered document analysis
        - Azure Document Intelligence
        - Advanced reasoning capabilities
        - JSON-based company evaluation
        """)

# Import and display the selected page
if page == "Vector Approach":
    from pages import vector_approach
    vector_approach.show_page()
elif page == "Reasoning Model Approach":
    from pages import reasoning_model_approach
    reasoning_model_approach.show_page()
