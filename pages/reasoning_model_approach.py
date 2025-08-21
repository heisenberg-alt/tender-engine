import streamlit as st
from datetime import datetime
import logging
from io import StringIO
from subprocess import run, PIPE
import os
import json
import time
from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentContentFormat, AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

def load_dotenv_from_azd():
    """Load environment variables from AZD environment or fallback to .env file."""
    result = run("azd env get-values", stdout=PIPE, stderr=PIPE, shell=True, text=True, check=False)
    if result.returncode == 0:
        logging.info("Found AZD environment. Loading...")
        load_dotenv(stream=StringIO(result.stdout))
    else:
        logging.info("AZD environment not found. Trying to load from .env file...")
        load_dotenv()

def get_document_intelligence_client():
    """Initialize Azure Document Intelligence client"""
    try:
        # Try the standard environment variable names first
        endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT") or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY") or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if not endpoint or not key:
            st.error("❌ Azure Document Intelligence credentials not configured. Please check your environment variables.")
            st.info("Required environment variables: DOCUMENTINTELLIGENCE_ENDPOINT and DOCUMENTINTELLIGENCE_API_KEY")
            return None
            
        return DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    except Exception as e:
        st.error(f"❌ Failed to initialize Document Intelligence client: {str(e)}")
        return None

def process_document_with_azure_di(file_content, filename):
    """Process document using Azure Document Intelligence with native markdown output"""
    try:
        client = get_document_intelligence_client()
        if not client:
            return None
            
        with st.spinner(f"Processing {filename} with Azure Document Intelligence..."):
            # Use the native markdown output format from Azure Document Intelligence
            poller = client.begin_analyze_document(
                "prebuilt-layout",
                body=file_content,
                output_content_format=DocumentContentFormat.MARKDOWN,
            )
            
            result: AnalyzeResult = poller.result()
            
            # Return the native markdown content from Azure DI
            if result.content:
                return result.content
            else:
                # Return a message if no content is available
                return "No content extracted from the document."
            
    except HttpResponseError as error:
        error_message = f"Azure Document Intelligence API error: {str(error)}"
        if error.error is not None:
            if error.error.code == "InvalidImage":
                error_message = f"Invalid image error: {error.error}"
            elif error.error.code == "InvalidRequest":
                error_message = f"Invalid request error: {error.error}"
        st.error(f"❌ {error_message}")
        return None
    except Exception as e:
        st.error(f"❌ Error processing document: {str(e)}")
        return None

def get_azure_openai_client():
    """Initialize Azure OpenAI client with managed identity authentication"""
    try:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            st.error("❌ Azure OpenAI endpoint not configured. Please set AZURE_OPENAI_ENDPOINT environment variable.")
            return None
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=os.getenv("AZURE_OPENAI_API_KEY"), 
            api_version="2025-04-01-preview"
        )
        
        return client
    except Exception as e:
        st.error(f"❌ Failed to initialize Azure OpenAI client: {str(e)}")
        return None

def analyze_tender_with_reasoning_model(tender_content, company_profiles, system_instructions, model_name, reasoning_effort, confidence_threshold=0.7):
    """
    Analyze tender content using Azure OpenAI reasoning model
    """
    try:
        client = get_azure_openai_client()
        if not client:
            return None
        
        # Convert confidence threshold to percentage for display
        threshold_percentage = int(confidence_threshold * 100)
        
        # Prepare the user message with tender content and company profiles
        user_message = f"""
**TENDER CONTENT:**
{tender_content}

**COMPANY PROFILES TO EVALUATE:**
{company_profiles}

Please analyze the tender requirements and evaluate each company's capability to participate. 
For each company, provide:
1. A matching score from 0% to 100%. A tender can be completely irrelevant to a company's profile, give 0% in this case.
2. A brief justification for the score
3. Recommendations for collaboration opportunities
4. Leave only companies that have a matching score greater than the specified threshold of {threshold_percentage}%.

Format your response as a structured JSON object with "company name", "matching score", "justification", and "recommendations" fields.
"""
        
        # Call Azure OpenAI reasoning model
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "developer", "content": system_instructions},
                {"role": "user", "content": user_message}
            ],
            max_completion_tokens=5000,
            reasoning_effort=reasoning_effort
        )
        
        processing_time = time.time() - start_time
        
        # Extract the response content
        analysis_result = {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": response.usage.model_dump() if response.usage else None,
            "processing_time": round(processing_time, 2),
            "reasoning_tokens": getattr(response.usage, 'reasoning_tokens', 0) if response.usage else 0
        }
        
        return analysis_result
        
    except Exception as e:
        st.error(f"❌ Error calling Azure OpenAI reasoning model: {str(e)}")
        return None

def show_page():
    """
    Reasoning Model Approach page with file uploader and text input field
    """
    # Load environment variables
    load_dotenv_from_azd()
    
    st.header("🧠 Reasoning Model Approach")
    st.markdown("Advanced AI-powered document analysis using Azure Document Intelligence and OpenAI reasoning models.")
    
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📁 Tender Upload")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['txt', 'pdf', 'docx', 'csv', 'json'],
            accept_multiple_files=True,
            help="Supported formats: TXT, PDF, DOCX, CSV, JSON"
        )
        # Text display field for processed tender content
        st.subheader("📄 Processed Tender Content")
        
        # Check for uploaded files
        has_uploaded_files = uploaded_files is not None and len(uploaded_files) > 0
        has_processed_docs = 'processed_documents' in st.session_state and len(st.session_state.processed_documents) > 0
        
        if has_uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")
            
            # Process each uploaded file
            for file_idx, uploaded_file in enumerate(uploaded_files):
                with st.expander(f"📄 {uploaded_file.name} - Processing Results", expanded=True):
                    
                    # File details
                    file_details = {
                        "Filename": uploaded_file.name,
                        "File size": f"{uploaded_file.size} bytes",
                        "File type": uploaded_file.type
                    }
                    
                    col_details, col_process = st.columns([1, 1])
                    
                    with col_details:
                        st.json(file_details)
                    
                    with col_process:
                        # Process button for each file
                        if st.button(f"🤖 Process with Azure DI", key=f"process_{file_idx}"):
                            # Read file content into buffer
                            file_content = uploaded_file.read()
                            uploaded_file.seek(0)  # Reset file pointer
                            
                            # Process with Azure Document Intelligence
                            markdown_result = process_document_with_azure_di(file_content, uploaded_file.name)
                            
                            if markdown_result:
                                # Store result in session state for persistence
                                if 'processed_documents' not in st.session_state:
                                    st.session_state.processed_documents = {}
                                st.session_state.processed_documents[uploaded_file.name] = markdown_result
                                st.success("✅ Document processed successfully!")
                            else:
                                st.error("❌ Failed to process document with Azure Document Intelligence")
                    
                    # Display processed content if available
                    if 'processed_documents' in st.session_state and uploaded_file.name in st.session_state.processed_documents:
                        st.subheader("📄 Extracted Content (Markdown)")
                        
                        # Create tabs for different views
                        tab_markdown, tab_preview = st.tabs(["📝 Raw Markdown", "👀 Preview"])
                        
                        with tab_markdown:
                            # Display raw markdown in a text area for editing
                            markdown_content = st.text_area(
                                "Processed content (editable):",
                                value=st.session_state.processed_documents[uploaded_file.name],
                                height=400,
                                key=f"markdown_{file_idx}"
                            )
                            
                            # Update session state if user edits
                            st.session_state.processed_documents[uploaded_file.name] = markdown_content
                            
                            # Download button for markdown
                            st.download_button(
                                label="💾 Download Markdown",
                                data=markdown_content,
                                file_name=f"{uploaded_file.name}_processed.md",
                                mime="text/markdown"
                            )
                        
                        with tab_preview:
                            # Display rendered markdown
                            st.markdown(st.session_state.processed_documents[uploaded_file.name])
                    
                    # Show basic preview for text files (fallback)
                    elif uploaded_file.type == "text/plain":
                        try:
                            content = str(uploaded_file.read(), "utf-8")
                            uploaded_file.seek(0)  # Reset file pointer
                            st.text_area("File Preview:", content[:500] + "..." if len(content) > 500 else content, height=100)
                        except:
                            st.warning("Unable to preview file content")
        
        # Show placeholder when no files are uploaded
        if not has_uploaded_files:
            # Show placeholder when no files are uploaded
            st.info("👆 Upload files above to see processed content here")
            st.text_area(
                "Processed document content will appear here...",
                value="",
                height=200,
                disabled=True,
                help="Upload documents and process them with Azure Document Intelligence to see extracted content"
            )
    
    with col2:
        st.subheader("💭 Company Profiles Input")
        
        # Initialize session state for company profile JSON if not exists
        if 'company_profile_json' not in st.session_state:
            st.session_state.company_profile_json = ""
        
        # Text input field
        company_profile_json = st.text_area(
            label="Company Profile JSON",
            value=st.session_state.company_profile_json,
            placeholder="use your Excel Copilot to convert the company profile table into JSON...",
            height=550,
            help="Provide specific questions or instructions for the AI reasoning model",
            key="company_profile_input"
        )
        
        # Update session state when user types
        st.session_state.company_profile_json = company_profile_json
        
        # add options to tune reasoning model api call parameters
        st.subheader("⚙️ Analysis Configuration")

        developer_message = st.text_area(
            label="System Instructions",
            height=200,
            value="""You are an AI reasoning model designed to analyze a public tender and select companies that are qualified to participate. You will be given the tender content in Markdown format and a list of companies to evaluate with. 
Your objective is to output a subset list of companies that are capable of participating, or collaborate with each other to participate the tender process.  
Your output should include a matching score from 0% to 100% for each company, and a brief justification for the score.""",
            help="Provide specific instructions for the AI reasoning model"
        )
        
        model_selection = st.selectbox(
            "Model Selection:",
            ["o4-mini", "gpt-5-mini"]
        )

        reasoning_effort = st.selectbox(
            "Reasoning Effort:",
            ["low", "medium", "high"]
        )
        
        confidence_threshold = st.slider(
            "Confidence Threshold:",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Minimum confidence level for AI responses"
        )
        
        # Process button
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Process with AI", type="primary", use_container_width=True):
                if uploaded_files and company_profile_json:
                    # Validate company profile JSON
                    if company_profile_json:
                        try:
                            json.loads(company_profile_json)
                        except json.JSONDecodeError:
                            st.error("❌ Invalid JSON format in Company Profile. Please check your JSON syntax.")
                            st.stop()
                    
                    # Collect all processed tender content
                    all_tender_content = ""
                    if 'processed_documents' in st.session_state and st.session_state.processed_documents:
                        for filename, content in st.session_state.processed_documents.items():
                            all_tender_content += f"\n\n--- {filename} ---\n{content}"
                    else:
                        st.warning("⚠️ No processed tender documents found. Please process documents with Azure DI first.")
                        st.stop()
                    
                    # Use company profiles or fallback message
                    company_data = company_profile_json if company_profile_json else "No company profiles provided for evaluation."
                    
                    with st.spinner("🤖 Analyzing tender with Azure OpenAI reasoning model..."):
                        # Call the reasoning model
                        analysis_result = analyze_tender_with_reasoning_model(
                            tender_content=all_tender_content,
                            company_profiles=company_data,
                            system_instructions=developer_message,
                            model_name=model_selection,
                            reasoning_effort=reasoning_effort,
                            confidence_threshold=confidence_threshold
                        )
                        
                        if analysis_result:
                            st.success("✅ AI Analysis completed!")
                            
                            # Store results in session state for persistence
                            st.session_state.ai_analysis_result = analysis_result
                            
                            # Display results
                            st.subheader("📊 AI Analysis Results")
                            
                            # Create tabs for different result views
                            result_tab1, result_tab2, result_tab3 = st.tabs(["📝 Analysis Report", "📊 Model Metrics", "🔧 Technical Details"])
                            
                            with result_tab1:
                                st.markdown("**AI-Generated Analysis:**")
                                st.markdown(analysis_result["content"])
                                
                                # Download button for the analysis
                                st.download_button(
                                    label="💾 Download Analysis Report",
                                    data=analysis_result["content"],
                                    file_name=f"tender_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                    mime="text/markdown"
                                )
                            
                            with result_tab2:
                                st.markdown("**Processing Metrics:**")
                                metric_col1, metric_col2, metric_col3 = st.columns(3)
                                
                                with metric_col1:
                                    st.metric("Processing Time", f"{analysis_result['processing_time']}s")
                                
                                with metric_col2:
                                    st.metric("Documents Analyzed", len(st.session_state.processed_documents))
                                
                                with metric_col3:
                                    if analysis_result.get('reasoning_tokens', 0) > 0:
                                        st.metric("Reasoning Tokens", f"{analysis_result['reasoning_tokens']:,}")
                                    else:
                                        st.metric("Model Used", analysis_result['model'])
                                
                                # Token usage details if available
                                if analysis_result.get('usage'):
                                    st.markdown("**Token Usage:**")
                                    usage_data = analysis_result['usage']
                                    usage_col1, usage_col2, usage_col3 = st.columns(3)
                                    
                                    with usage_col1:
                                        if 'prompt_tokens' in usage_data:
                                            st.metric("Prompt Tokens", f"{usage_data['prompt_tokens']:,}")
                                    
                                    with usage_col2:
                                        if 'completion_tokens' in usage_data:
                                            st.metric("Completion Tokens", f"{usage_data['completion_tokens']:,}")
                                    
                                    with usage_col3:
                                        if 'total_tokens' in usage_data:
                                            st.metric("Total Tokens", f"{usage_data['total_tokens']:,}")
                            
                            with result_tab3:
                                st.markdown("**Configuration Used:**")
                                config_info = {
                                    "Model": analysis_result['model'],
                                    "Reasoning Effort": reasoning_effort,
                                    "Processing Time": f"{analysis_result['processing_time']} seconds",
                                    "Documents Processed": list(st.session_state.processed_documents.keys()) if 'processed_documents' in st.session_state else []
                                }
                                st.json(config_info)
                                
                                # Raw response data
                                with st.expander("🔍 Raw API Response", expanded=False):
                                    st.json(analysis_result)
                        else:
                            st.error("❌ Failed to process with AI reasoning model. Please check your Azure OpenAI configuration.")
                
                elif not uploaded_files:
                    st.warning("⚠️ Please upload at least one document before processing.")
                elif not company_profile_json:
                    st.warning("⚠️ Please provide company profile data.")
        
        with col_btn2:
            if st.button("🔄 Clear All", use_container_width=True):
                # Clear processed documents from session state
                if 'processed_documents' in st.session_state:
                    del st.session_state.processed_documents
                # Clear AI analysis results from session state
                if 'ai_analysis_result' in st.session_state:
                    del st.session_state.ai_analysis_result
                # Clear company profile JSON input
                st.session_state.company_profile_json = ""
                st.rerun()

    # Info sidebar for this approach
    with st.sidebar:
        st.markdown("---")
        st.header("🧠 AI Configuration")
        st.info("Using Azure Document Intelligence + OpenAI Reasoning Models")
        
        st.header("📊 System Status")
        # Check environment variables and display status
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        di_endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
        
        if endpoint:
            st.success("✅ Azure OpenAI: Configured")
        else:
            st.error("❌ Azure OpenAI: Not configured")
            
        if di_endpoint:
            st.success("✅ Document Intelligence: Configured")
        else:
            st.error("❌ Document Intelligence: Not configured")
        
        st.header("🔧 Features")
        st.write("• Multi-format document upload")
        st.write("• Azure DI markdown extraction")
        st.write("• JSON company profile input")
        st.write("• Configurable reasoning models")
        st.write("• Detailed analysis reports")

    # Footer
    st.markdown("---")
    st.markdown("*Reasoning Model Approach - Advanced AI Analysis*")
