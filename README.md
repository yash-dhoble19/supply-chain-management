<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Neon_PostgreSQL-00E5A0?style=for-the-badge&logo=postgresql&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
</p>

# ⚡ ChainMind — AI-Powered Supply Chain Management

**ChainMind** is a full-stack, AI-powered supply chain management platform that combines real-time inventory monitoring, demand forecasting, procurement intelligence, and logistics tracking into a single executive dashboard.

---

## 🏗️ Architecture

```
scm-backend-python/
├── main.py                  # FastAPI application (all API routes)
├── models.py                # SQLAlchemy ORM models
├── database.py              # Neon PostgreSQL connection setup
├── config.py                # App settings (Pydantic)
├── ai_insight_service.py    # AI-powered procurement insights
├── forecast_service.py      # Demand forecasting engine
├── prophet_model.py         # Facebook Prophet integration
├── data_preparation.py      # Data preprocessing utilities
├── evaluation.py            # Forecast accuracy evaluation
├── ai_agent.py              # Supply chain AI agent
├── seed_db.py               # Database seeder (sample data)
├── init_db.py               # Database initialization script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template (copy to .env)
│
└── frontend/                # React + Vite + TypeScript dashboard
    ├── src/
    │   ├── components/      # Reusable UI components
    │   ├── pages/           # Page-level components
    │   ├── services/        # API service layer
    │   ├── hooks/           # Custom React hooks
    │   ├── types/           # TypeScript type definitions
    │   └── utils/           # Utility functions
    ├── package.json
    └── vite.config.ts
```

---

## 🚀 Quick Start (5 minutes)

### Prerequisites

| Tool        | Version  | Install Guide                                      |
| ----------- | -------- | -------------------------------------------------- |
| **Python**  | 3.10+    | [python.org](https://www.python.org/downloads/)     |
| **Node.js** | 18+      | [nodejs.org](https://nodejs.org/)                   |
| **Git**     | any      | [git-scm.com](https://git-scm.com/)                |

### 1. Clone the Repository

```bash
git clone https://github.com/yash-dhoble19/supply-chain-management.git
cd supply-chain-management
```

### 2. Set Up Environment Variables

```bash
# Copy the example env file (contains shared Neon DB credentials)
cp .env.example .env
```

> **Note for collaborators:** The `.env.example` includes the shared Neon PostgreSQL database URL and Groq API key. Just copy it — no additional database setup is needed.

### 3. Set Up the Backend (FastAPI)

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# Windows (PowerShell):
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Initialize & Seed the Database (first-time only)

```bash
# Create all database tables
python init_db.py

# Seed with sample data (optional but recommended)
python seed_db.py
```

### 5. Start the Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend will be live at **http://localhost:8000**  
📄 API docs at **http://localhost:8000/docs**

### 6. Set Up & Start the Frontend (React)

```bash
# Navigate to the frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

✅ Frontend will be live at **http://localhost:5173**

---

## 🗄️ Database — Neon PostgreSQL (Shared)

This project uses a **shared [Neon](https://neon.tech) PostgreSQL** database so that all collaborators work against the same data. The connection string is already included in `.env.example`.

| Parameter        | Value                                                  |
| ---------------- | ------------------------------------------------------ |
| **Host**         | `ep-late-moon-ahpifz5m-pooler.c-3.us-east-1.aws.neon.tech` |
| **Database**     | `neondb`                                                |
| **User**         | `neondb_owner`                                          |
| **SSL**          | Required (`sslmode=require`)                            |

> ⚠️ **Important:** Do **not** commit the `.env` file to Git. It is already listed in `.gitignore`. Use `.env.example` as the template.

---

## 🧠 Key Features

| Module                      | Description                                                          |
| --------------------------- | -------------------------------------------------------------------- |
| **Executive Dashboard**     | Real-time KPIs, health score, shipment tracking, activity feed       |
| **Inventory Management**    | Product CRUD, stock movements, safety stock alerts                   |
| **Demand Forecasting**      | Facebook Prophet-based forecasting with seasonal & festival awareness |
| **Procurement Intelligence**| AI-driven reorder recommendations, supplier matching, PO generation  |
| **Supplier Management**     | Reliability scoring, performance ranking, category-based matching    |
| **Logistics & Routing**     | OSRM-based route optimization, shipment tracking, carrier management |
| **AI Agent**                | Natural language supply chain assistant powered by Groq/LLaMA        |

---

## 🔌 API Overview

Once the backend is running, visit **http://localhost:8000/docs** for the full interactive API documentation (Swagger UI).

Key endpoint groups:

| Endpoint Prefix           | Purpose                        |
| ------------------------- | ------------------------------ |
| `/products`               | Inventory & product management |
| `/suppliers`              | Supplier management            |
| `/procurement/*`          | Procurement intelligence       |
| `/api/procurement/*`      | Purchase orders & insights     |
| `/forecast/*`             | Demand forecasting             |
| `/orders`                 | Order management               |
| `/shipments`              | Shipment tracking              |
| `/logistics/*`            | Route optimization             |

---

## 🛠️ Tech Stack

| Layer      | Technology                     |
| ---------- | ------------------------------ |
| Backend    | FastAPI, SQLAlchemy, Pydantic  |
| Database   | Neon PostgreSQL (serverless)   |
| Frontend   | React 18, TypeScript, Vite     |
| Styling    | Tailwind CSS                   |
| AI/ML      | Groq (LLaMA 3.3), Prophet     |
| Geocoding  | Geopy + Nominatim              |
| Routing    | OSRM (Open Source)             |

---

## 📁 Running Both Servers (Quick Reference)

Open **two terminals**:

**Terminal 1 — Backend:**
```bash
cd supply-chain-management
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd supply-chain-management/frontend
npm run dev
```

| Service   | URL                        |
| --------- | -------------------------- |
| Backend   | http://localhost:8000      |
| API Docs  | http://localhost:8000/docs |
| Frontend  | http://localhost:5173      |

---

## 🤝 Contributing

1. Fork the repo & clone it locally  
2. Copy `.env.example` → `.env`  
3. Follow the [Quick Start](#-quick-start-5-minutes) steps above  
4. Create a feature branch: `git checkout -b feature/my-feature`  
5. Commit your changes: `git commit -m "Add my feature"`  
6. Push to branch: `git push origin feature/my-feature`  
7. Open a Pull Request

---

## 📜 License

This project is for educational and internal team use.

---

<p align="center">
  Built with ❤️ by <strong>Yash Dhoble</strong>
</p>
