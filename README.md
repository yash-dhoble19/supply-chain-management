# 🏭 GenAI-Powered Supply Chain Control Tower

This project is an AI-driven Supply Chain Management system that integrates a **FastAPI backend** (logic & AI agents) with a **Streamlit frontend** (interactive dashboard).

## 🚀 Features

* **📊 Dashboard:** Real-time visualization of inventory and order status.
* **🤖 AI Demand Forecasting:** Uses historical data + Groq AI (Llama-3) to predict future sales trends considering market news.
* **🚚 Logistics Control:** Route optimization using OSRM (Open Source Routing Machine) & AI-based risk analysis for delivery locations.
* **🤝 AI Procurement:** Compares supplier quotes and recommends the best option based on deadlines, cost, and reliability.
* **📦 Inventory Management:** Tracks stock levels and alerts on critical shortages.

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit, Plotly, Folium
* **Backend:** FastAPI, Python, SQLAlchemy
* **AI Models:** Groq API (Llama-3 70b), OpenAI Client (wrapper)
* **Database:** PostgreSQL
* **Routing:** OSRM & Nominatim (OpenStreetMap)

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/yash-dhoble19/supply-chain-management.git](https://github.com/yash-dhoble19/supply-chain-management.git)
cd supply-chain-management
```bash


python -m venv venv
venv\Scripts\activate




pip install -r requirements.txt


# .env file

# Your Groq API Key (Get one from console.groq.com)
GROQ_API_KEY=your_actual_groq_api_key_here

# Your Database Connection String
# Format: postgresql://username:password@localhost/database_name
DATABASE_URL=postgresql://postgres:your_password@localhost/supply_chain_db




uvicorn main:app --reload
streamlit run app.py

### Final Step
After you save this file, run these commands to update GitHub:

```bash
git add README.md
git commit -m "Update README with full documentation"
git push origin main
