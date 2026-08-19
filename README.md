# 📄 PDF Analyzer Pro

AI-Powered PDF Document Analysis - Extract structured information from PDFs using state-of-the-art language models.

---

## ✨ Features

- Upload PDFs - Drag and drop or browse for PDF files
- AI-Powered Analysis - Extract structured data using OpenRouter
- Structured Output - Get title, author, summary, and keywords
- Persistent Storage - PostgreSQL database with Docker volume
- Beautiful UI - Modern, responsive Streamlit interface
- Dockerized - Easy deployment with Docker Compose

---

## 🏗️ Architecture

The application consists of three main components:

1. **Streamlit Frontend** - User interface (port 8501)
2. **FastAPI Backend** - API server (port 8000)
3. **PostgreSQL Database** - Data storage (port 5432)

The backend communicates with OpenRouter API for AI-powered PDF analysis.

---

## 🚀 Quick Start

### Prerequisites

Before you begin, make sure you have:

- Docker installed (20.10 or higher)
- Docker Compose installed (2.0 or higher)
- An OpenRouter API key (get one at https://openrouter.ai/keys)

### Installation Steps

**Step 1: Clone the repository**

Open your terminal and run:
git clone https://github.com/hosseinkh79/persian-pdf-analyzer.git
cd persian-pdf-analyzer


**Step 2: Set up environment variables**
Copy the example environment file:
cp .env.example .env

Open the .env file and add your OpenRouter API key:
OPEN_ROUTER_API_KEY=your-api-key-here


**Step 3: Start the application**

Run Docker Compose to build and start all services:
docker-compose up --build 


**Step 4: Access the application**

Open your browser and go to:
- Streamlit UI: http://localhost:8501
- FastAPI Docs: http://localhost:8000/docs
- API Health Check: http://localhost:8000/health

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /documents/upload | Upload a PDF file |
| POST | /documents/{id}/analyze | Analyze a document |
| GET | /documents/ | Get all documents |
| GET | /documents/{id} | Get document details |
| DELETE | /documents/{id} | Delete a document |

### Example API Calls

Upload a PDF:
curl -X POST http://localhost:8000/documents/{document-id}/analyze


---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default Value |
|----------|-------------|---------------|
| POSTGRES_USER | PostgreSQL username | postgres |
| POSTGRES_PASSWORD | PostgreSQL password | postgres |
| POSTGRES_DB | Database name | pdf_analyzer |
| OPEN_ROUTER_API_KEY | OpenRouter API key | (required) |
| OPENROUTER_MODEL | Default LLM model | nvidia/nemotron-3.5-lightning:free |

### Supported Models

You can use any model available on OpenRouter:

**Free Models:**
- nvidia/nemotron-3.5-lightning:free
- google/gemini-2.0-flash-exp:free
- meta-llama/llama-3.2-1b-instruct:free

**Paid Models:**
- openai/gpt-4
- anthropic/claude-3-sonnet
- meta-llama/llama-3-70b-instruct

To change the model, update OPENROUTER_MODEL in your .env file.

---

## 📁 Project Structure

Here's how the project is organized:
persian-pdf-analyzer/
│
├── backend/ # FastAPI backend
│ ├── app/
│ │ ├── main.py # Entry point
│ │ ├── config.py # Configuration
│ │ ├── database.py # Database connection
│ │ ├── models.py # Database models
│ │ ├── schemas.py # Pydantic schemas
│ │ ├── routers/ # API routes
│ │ │ └── documents.py
│ │ └── services/ # Business logic
│ │ └── analysis.py
│ ├── uploads/ # Uploaded files
│ ├── requirements.txt
│ └── Dockerfile
│
├── frontend/ # Streamlit frontend
│ ├── app.py # Main UI
│ ├── requirements.txt
│ └── Dockerfile
│
├── docker-compose.yml # Docker orchestration
├── .env.example # Environment template
└── README.md # This file


---

## 📝 License

This project is licensed under the MIT License.

---

## 📞 Contact

- **Author**: Hossein Kh
- **GitHub**: [@hosseinkh79](https://github.com/hosseinkh79)
- **Project URL**: https://github.com/hosseinkh79/persian-pdf-analyzer

---

**Made with ❤️ using FastAPI, Streamlit, and PostgreSQL**

