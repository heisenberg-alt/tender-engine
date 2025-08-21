# AI Reasoning Model - Standalone Application

A standalone Streamlit application for intelligent document analysis powered by Azure Document Intelligence.

## Features

🔹 **Document Processing** with Azure Document Intelligence  
🔹 **Text Extraction** from multiple file formats  
🔹 **Native Markdown Output** using Azure's latest API  
🔹 **URL-based Document Processing**  
🔹 **Interactive Results** with markdown preview and editing  
🔹 **Multiple File Upload Support**  

## Supported File Types

- Text files (.txt)
- PDF documents (.pdf)
- Word documents (.docx)
- CSV data files (.csv)
- JSON files (.json)

## Setup

### Prerequisites

1. **Azure Document Intelligence Service**: Create an Azure Document Intelligence resource in the Azure Portal
2. **Python 3.8+**: Ensure you have Python installed
3. **Environment Variables**: Configure the required environment variables

### Environment Variables

Set one of the following sets of environment variables:

**Option 1 (Recommended - Azure SDK Standard):**
```bash
DOCUMENTINTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
DOCUMENTINTELLIGENCE_API_KEY=your-api-key
```

**Option 2 (Alternative):**
```bash
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-api-key
```

### Installation

1. Install dependencies:
```bash
pip install streamlit azure-ai-documentintelligence python-dotenv
```

2. Run the application:
```bash
streamlit run reasoning_model.py
```

## Usage

### Document Upload
1. **File Upload**: Use the "Upload Files" tab to select and upload documents
2. **URL Processing**: Use the "Process from URL" tab to analyze documents from public URLs
3. **Process Documents**: Click "Process with Azure DI" to extract content using Azure Document Intelligence

### Document Analysis
1. **Review Content**: Check the extracted markdown content in the preview tabs
2. **Edit Content**: Modify the extracted content in the raw markdown editor
3. **Download Results**: Save the processed content as markdown files

### AI Reasoning
1. **Enter Prompt**: Provide questions or instructions for analysis
2. **Select Analysis Type**: Choose from predefined analysis types
3. **Adjust Settings**: Set confidence thresholds and other parameters
4. **Process with AI**: Run the reasoning analysis (placeholder implementation)

## Azure Document Intelligence Features

- **Layout Analysis**: Extract text, tables, and document structure
- **Native Markdown Output**: Get properly formatted markdown directly from Azure
- **Multi-page Support**: Process documents with multiple pages
- **Table Detection**: Automatically detect and extract table data
- **Key-Value Pairs**: Identify form fields and their values
- **URL Processing**: Analyze documents from public URLs

## API Integration

This application follows the Azure SDK for Python best practices and uses the latest Document Intelligence API features:

- Native markdown content format output
- Proper error handling with specific error codes
- Support for both file uploads and URL-based document processing
- Environment variable configuration following Azure standards

## Example Usage

### Processing a PDF from URL
```python
# The app can process documents from public URLs
url = "https://example.com/document.pdf"
# Results will be displayed in native markdown format
```

### File Upload Processing
```python
# Upload files through the Streamlit interface
# Supported formats: PDF, DOCX, TXT, CSV, JSON
# Results are converted to markdown for easy viewing and editing
```

## Troubleshooting

### Common Issues

1. **Environment Variables Not Found**
   - Ensure environment variables are set correctly
   - Check both standard and alternative variable names

2. **Azure API Errors**
   - Verify your Azure Document Intelligence endpoint and key
   - Check that your Azure resource is active and has available quota

3. **File Processing Errors**
   - Ensure files are in supported formats
   - Check file size limits (varies by Azure tier)
   - Verify URLs are publicly accessible for URL processing

### Error Codes

The application handles specific Azure Document Intelligence error codes:
- `InvalidImage`: Issues with image-based documents
- `InvalidRequest`: Problems with request format or parameters

## Architecture

The application is built with:
- **Streamlit**: Web application framework
- **Azure Document Intelligence SDK**: Document processing
- **Native Azure Markdown Output**: Latest API features
- **Session State Management**: Persistent document storage
- **Error Handling**: Comprehensive error management

## Contributing

This is a standalone application extracted from the larger tender-engine project. For modifications:

1. Follow Azure SDK best practices
2. Maintain compatibility with the latest Document Intelligence API
3. Ensure proper error handling for all Azure operations
4. Test with various document types and formats

## License

This project follows the same license as the parent tender-engine project.
