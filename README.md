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


# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies

pip install -r requirements.txt



4. Configure Environment Variables
Create a file named .env in the root directory (do not commit this file!) and add your keys:

Properties

# Your Groq API Key for AI Agents
GROQ_API_KEY=your_groq_api_key_here

# Your PostgreSQL Connection String
# Format: postgresql://username:password@localhost/database_name
DATABASE_URL=postgresql://postgres:password@localhost/supply_chain_db

supply_chain_db
Note: Ensure you have a local PostgreSQL database created named supply_chain_db


Here is a professional and clear README.md file for your Supply Chain Management project. This file is crucial because it tells people (recruiters, teammates, or future you) exactly what the project does and how to run it.

Step 1: Create the file
Create a new file named README.md in your project folder C:\Users\yashd\scm-backend-python.

Step 2: Copy and Paste this content
Copy the text inside the code block below and paste it into your new README.md file.

Markdown

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
2. Set up a Virtual Environment
Bash

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
4. Configure Environment Variables
Create a file named .env in the root directory (do not commit this file!) and add your keys:

Properties

# Your Groq API Key for AI Agents
GROQ_API_KEY=your_groq_api_key_here

# Your PostgreSQL Connection String
# Format: postgresql://username:password@localhost/database_name
DATABASE_URL=postgresql://postgres:password@localhost/supply_chain_db
Note: Ensure you have a local PostgreSQL database created named supply_chain_db.

🏃‍♂️ How to Run
You need to run the Backend and Frontend in two separate terminal windows.

Terminal 1: Start the Backend (API)
This handles the logic, database connections, and AI requests.

Bash

uvicorn main:app --reload
The API will start at http://127.0.0.1:8000

Terminal 2: Start the Frontend (Dashboard)
This launches the user interface.

Bash

streamlit run app.py
The dashboard will open automatically in your browser at http://localhost:8501


