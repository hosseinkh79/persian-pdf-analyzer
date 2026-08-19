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

git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd your-repo-name

cp .env.example .env

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password_123
POSTGRES_DB=pdf_analyzer
LLM_API_KEY=your_actual_api_key_here

docker compose up --build

