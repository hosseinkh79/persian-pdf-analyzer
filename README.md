# 📄 AI Document Intelligence Pipeline

An end-to-end, containerized microservice architecture designed to ingest PDF documents, extract text streams, enforce structured JSON analysis via LLM APIs, and store persistent records in PostgreSQL. Built with **FastAPI**, **Streamlit**, and **Docker Compose**.

---

## 🏗️ Architecture & System Topology

The application follows a decoupled multi-container design, isolating the presentation layer, the API processing orchestration, and data persistence behind a private Docker virtual network.

```text
[ Browser / User ]
       │
       ▼ (Port 8501)
┌──────────────┐      HTTP / REST API      ┌──────────────┐      LLM API Requests      ┌──────────────┐
│  Streamlit   │ ────────────────────────► │   FastAPI    │ ─────────────────────────► │  LLM Provider│
│ (Frontend UI)│ ◄──────────────────────── │  (Backend)   │ ◄───────────────────────── │ (OpenAI/Anth)│
└──────────────┘                           └──────┬───────┘                            └──────────────┘
                                                  │
                                                  │ SQL Queries
                                                  ▼ (Port 5432)
                                           ┌──────────────┐
                                           │  PostgreSQL  │ ──► [ Docker Volume ]
                                           │  (Database)  │    (Persistent Data)
                                           └──────────────┘

## ✨ Features

- 📤 **Upload PDFs** - Drag and drop or browse for PDF files
- 🤖 **AI-Powered Analysis** - Extract structured data using OpenRouter
- 📊 **Structured Output** - Get title, author, summary, and keywords
- 💾 **Persistent Storage** - PostgreSQL database with Docker volume
- 🎨 **Beautiful UI** - Modern, responsive Streamlit interface
- 🐳 **Dockerized** - Easy deployment with Docker Compose


## Project Structure   
                                      .
├── backend/
│   ├── app/
│   │   ├── routers/        # REST Endpoints (Upload, List, Delete)
│   │   ├── services/       # PDF Extraction & LLM API Integration
│   │   ├── config.py       # Pydantic BaseSettings Environment Loader
│   │   ├── db.py           # Engine Initialization & Session Lifecycle
│   │   ├── models.py       # SQLAlchemy ORM Database Schemas
│   │   ├── schemas.py      # Pydantic Data Contracts & Analysis Outputs
│   │   └── main.py         # FastAPI Entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py              # Streamlit Dashboard Code
│   ├── Dockerfile
│   └── requirements.txt
├── .env.example            # Environment Variable Template
├── .gitignore              # Git Ignore Definitions
├── docker-compose.yml      # Service Orchestration & Network Definitions
└── README.md





## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (2.0+)
- [OpenRouter API Key](https://openrouter.ai/keys)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/hosseinkh79/persian-pdf-analyzer.git
   cd persian-pdf-analyzer


cp .env.example .env
nano .env

docker-compose up --build -d



**Explanation:**
- `###` = Heading level 3
- `1.` = Numbered list
- ```bash = Code block for bash commands

---

### 7. Add API Documentation

**What to write:**
```markdown
## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload a PDF file |
| `POST` | `/documents/{id}/analyze` | Analyze a document |
| `GET` | `/documents/` | Get all documents |
| `GET` | `/documents/{id}` | Get document details |
| `DELETE` | `/documents/{id}` | Delete a document |

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact

- **Author**: Hossein Kh
- **GitHub**: [@hosseinkh79](https://github.com/hosseinkh79)
- **Project**: [persian-pdf-analyzer](https://github.com/hosseinkh79/persian-pdf-analyzer)

---

**Made with ❤️ using FastAPI, Streamlit, and PostgreSQL**

git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

cp .env.example .env

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password_123
POSTGRES_DB=pdf_analyzer
LLM_API_KEY=your_actual_api_key_here

docker compose up --build

