<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Neon_PostgreSQL-00E5A0?style=for-the-badge&logo=postgresql&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
</p>

# ⚡ ChainMind — High-Performance AI Supply Chain Management

**ChainMind** is a state-of-the-art, modular supply chain management platform. It leverages a high-performance architecture that combines deterministic business logic with asynchronous AI insights to provide real-time inventory monitoring, demand forecasting, and procurement intelligence.

---

## 🏗️ Modular Architecture

The backend follows a clean, modular service-oriented architecture designed for scalability and sub-100ms response times.

```
scm-backend-python/
├── api/
│   └── routes/              # Domain-specific API controllers
├── services/                # Core business logic & deterministic engines
├── schemas/                 # Pydantic request/response models
├── models.py                # SQLAlchemy ORM models (Neon Postgres)
├── database.py              # Database connection management
├── main.py                  # API entry point & router aggregation
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
│
└── frontend/                # React + Vite + TypeScript dashboard
    ├── src/
    │   ├── components/      # Atomic UI components
    │   ├── pages/           # Executive Dashboard & Intelligence views
    │   ├── hooks/           # Data fetching & state management
    │   └── services/        # Frontend API client
```

---

## 🚀 Performance Engineering

Unlike traditional AI apps, ChainMind uses a **Performance-First** approach:
- **Deterministic Metrics:** Critical KPIs (Stock health, PO counts) use optimized Python logic for instant loading.
- **Asynchronous AI:** AI-heavy reasoning (Groq/LLM) is offloaded to background tasks and persisted in Postgres.
- **N+1 Optimization:** Uses SQL eager loading (`joinedload`) to eliminate database round-trip bottlenecks.
- **Zero-Block Path:** No live AI calls occur during normal page loads, ensuring the dashboard is always responsive.

---

## 🛠️ Tech Stack

| Layer      | Technology                     |
| ---------- | ------------------------------ |
| **Backend**    | FastAPI, SQLAlchemy, SQLAlchemy Eager Loading |
| **Database**   | Neon PostgreSQL (Serverless)   |
| **Frontend**   | React 18, TypeScript, Vite     |
| **Styling**    | Tailwind CSS, Modern UI/UX     |
| **AI/ML**      | Groq (LLaMA 3.3), FB Prophet   |
| **Logistics**  | OSRM (Routing), Geopy          |

---

## 🚀 Quick Start

### 1. Clone & Environment
```bash
git clone https://github.com/yash-dhoble19/supply-chain-management.git
cd supply-chain-management
cp .env.example .env
```

### 2. Backend Setup
```bash
python -m venv venv
# Activate virtualenv (Windows: .\venv\Scripts\activate | Unix: source venv/bin/activate)
pip install -r requirements.txt
python init_db.py
python seed_db.py  # Optional: Seed sample data
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Key Modules

| Module                      | Description                                                          |
| --------------------------- | -------------------------------------------------------------------- |
| **Executive Dashboard**     | Real-time KPIs with synchronized "System Health" scoring.            |
| **Procurement Intel**       | Multi-layer analysis with persisted AI reasoning and PO management.   |
| **Demand Forecasting**      | Prophet-based predictive engine with visual plotting.                 |
| **Logistics Tracking**      | Real-time shipment milestones and OSRM route optimization.           |
| **Inventory Control**       | Safety stock lifecycle tracking and deterministic stock movement.    |

---
## 🧾 Column Mapping

### Section B

| Column                         | Details                                                                 |
| ------------------------------ | ----------------------------------------------------------------------- |
| Product ID / SKU / Product Name | Key product identifiers that span master-sku linkage, catalog lookups, and dataset joins. |
| Category                       | Product hierarchy or assortment bucket used for segmentation and forecasting. |

### Section C

| Column               | Details                                                                 |
| -------------------- | ----------------------------------------------------------------------- |
| Store ID / Store Name | Identifier and friendly label used to correlate stores across systems and UIs. |
| Geographic Details   | Location metadata (region, city, latitude/longitude, etc.) used for routing, mapping, and market intelligence. |

---

## 🔌 API Documentation
Visit **http://localhost:8000/docs** for the full interactive Swagger documentation.

---

## 📜 License
Internal team use and educational purposes.

<p align="center">
  Built with ❤️ by <strong>Yash Dhoble</strong>
</p>

<!-- anything -->
