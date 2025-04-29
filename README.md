# Tender Recommender AI

An intelligent system that helps businesses find and recommend relevant government tenders based on their company profile and historical bidding patterns.

![Tender Recommender AI](https://github.com/SubhashGovindharaj/tender-recommender-ai/raw/main/assets/header-image.png)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Data Sources](#data-sources)
- [Machine Learning Model](#machine-learning-model)
- [API Documentation](#api-documentation)
- [Frontend Application](#frontend-application)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## 🔍 Overview

Tender Recommender AI is a sophisticated platform designed to bridge the gap between businesses and government procurement opportunities. By leveraging advanced machine learning algorithms, the system analyzes a company's profile, past bidding history, and success rates to recommend the most relevant and promising government tenders. This solution aims to increase the efficiency of the tender discovery process, enhance bid success rates, and optimize resource allocation for businesses of all sizes.

## ✨ Features

- **Personalized Tender Recommendations**: AI-powered suggestions based on company profile and past bidding history
- **Tender Matching Score**: Numerical score indicating the relevance of a tender to your business
- **Success Probability Estimation**: Predictive analytics to estimate the likelihood of winning a specific tender
- **Company Profile Analysis**: In-depth analysis of your business capabilities and strengths
- **Tender Filtering System**: Advanced filtering options based on multiple parameters
- **Email Notifications**: Customizable alerts for new relevant tenders
- **Interactive Dashboard**: Visual representation of tender opportunities and insights
- **Bid History Tracking**: Monitor and analyze past bidding patterns and outcomes
- **Competitor Analysis**: Understanding of market competition for specific tender types
- **Document Management**: Storage and organization of tender-related documents

## 🏗️ System Architecture

The Tender Recommender AI consists of the following components:

1. **Data Collection Layer**
   - Web scrapers for government tender portals
   - API integrations with tender databases
   - Historical bid database

2. **Processing Layer**
   - Data preprocessing and cleaning
   - Text analysis and natural language processing
   - Feature extraction

3. **AI/ML Layer**
   - Recommendation engine
   - Classification models
   - Success probability prediction

4. **Application Layer**
   - REST API services
   - User authentication and management
   - Notification system

5. **User Interface Layer**
   - Web application
   - Mobile responsive design
   - Visualization components

## 💻 Installation

### Prerequisites

- Python 3.8+
- Node.js 14+
- MongoDB 4.4+
- Redis (for caching)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/SubhashGovindharaj/tender-recommender-ai.git
cd tender-recommender-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python manage.py init_db

# Run migrations
python manage.py migrate

# Start the backend server
python manage.py runserver
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 🚀 Usage

### Company Profile Setup

1. Register and create your account
2. Complete your company profile with:
   - Industry sectors
   - Core competencies
   - Previous projects
   - Team expertise
   - Certifications and compliance documents

### Finding Tender Recommendations

1. Navigate to the Dashboard
2. View recommended tenders sorted by relevance score
3. Use filters to refine recommendations
4. Click on a tender to view detailed information and matching analysis

### Analyzing Tender Opportunities

1. Review the tender matching score and success probability
2. Examine the key factors influencing the recommendation
3. Check required documents and compliance requirements
4. View similar tenders you've bid on in the past

### Managing Bids

1. Mark tenders of interest
2. Track application deadlines
3. Upload and organize bid documents
4. Record bid outcomes for future reference

## 📊 Data Sources

The system collects tender data from multiple sources:

- Government procurement portals
- Official tender websites
- Public sector purchasing platforms
- International tender databases
- Historical bid records (user-provided)

Data is refreshed daily to ensure up-to-date recommendations.

## 🧠 Machine Learning Model

The recommendation system employs a hybrid approach combining:

- **Content-Based Filtering**: Matches tender requirements with company capabilities
- **Collaborative Filtering**: Identifies patterns from similar companies' bidding behaviors
- **NLP Techniques**: Processes and analyzes tender document text
- **Classification Models**: Categorizes tenders by relevance and suitability
- **Regression Models**: Predicts success probability

Models are regularly retrained with new data and user feedback to improve accuracy over time.

## 📡 API Documentation

The Tender Recommender AI provides a comprehensive REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Authenticate user |
| `/api/profile` | GET/PUT | Retrieve/update company profile |
| `/api/tenders` | GET | List available tenders |
| `/api/tenders/recommended` | GET | Get personalized recommendations |
| `/api/tenders/{id}` | GET | Get tender details |
| `/api/bids` | POST | Record a new bid |
| `/api/bids/history` | GET | View bidding history |
| `/api/analytics/performance` | GET | Get bid performance analytics |

For detailed API documentation, refer to `/docs/api` after starting the server.

## 🖥️ Frontend Application

The web application provides an intuitive interface built with:

- React.js for component-based UI
- Redux for state management
- D3.js for data visualization
- Material UI for design components
- Responsive design for mobile and desktop usage

Key screens include:
- Dashboard
- Tender Discovery
- Bid Management
- Analytics
- Company Profile
- Settings

## ⚙️ Configuration

Configuration options can be set in the `.env` file:

```
# Server Configuration
PORT=8000
NODE_ENV=development

# Database Configuration
MONGODB_URI=mongodb://localhost:27017/tender-recommender

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_EXPIRY=24h

# API Keys for Tender Sources
GOV_TENDER_API_KEY=your_api_key
INTERNATIONAL_DB_USERNAME=username
INTERNATIONAL_DB_PASSWORD=password

# AI Model Settings
MODEL_REFRESH_INTERVAL=7d
RECOMMENDATION_THRESHOLD=0.65

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=true
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASS=password
```

## 👥 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the code style guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact

Subhash Govindharaj - [@SubhashGovind](https://twitter.com/SubhashGovind) - subhash.govindharaj@example.com

Project Link: [https://github.com/SubhashGovindharaj/tender-recommender-ai](https://github.com/SubhashGovindharaj/tender-recommender-ai)

---

© 2025 Tender Recommender AI | Created by Subhash Govindharaj
