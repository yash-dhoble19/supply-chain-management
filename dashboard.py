import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import io
import folium
from streamlit_folium import st_folium
import polyline
from datetime import datetime, timedelta
from streamlit_mic_recorder import speech_to_text 

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Expedition Co. Control Tower", layout="wide", page_icon="🏭")

# --- 🎨 PROFESSIONAL THEME & STYLES ---
st.markdown("""
<style>
    :root {
        --bg: #f5f7fb; --card: #ffffff; --text: #1f2937; --muted: #6b7280;
        --primary: #2563eb; --accent: #10b981; --warning: #f59e0b; --danger: #ef4444;
        --shadow: 0 6px 24px rgba(0,0,0,0.08);
    }
    .stApp { background: var(--bg); color: var(--text); }
    .main .block-container { padding-top: 12px; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: var(--card); border: 1px solid #e5e7eb;
        padding: 18px; border-radius: 14px; text-align: center;
        box-shadow: var(--shadow);
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px; font-weight: 700; border: 1px solid #dbeafe;
        padding: 10px 16px; transition: all .18s ease; letter-spacing:.2px; text-shadow: 0 1px 0 rgba(0,0,0,.06);
    }
    .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: #ffffff;
    }
    .stButton > button[data-testid="baseButton-secondary"] {
        background: #ffffff; color: #1f2937; border: 1px solid #e5e7eb;
    }
    .stButton > button:disabled {
        background: #eef2ff !important; color: #9ca3af !important; border-color: #e5e7eb !important; cursor: not-allowed;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 10px 20px rgba(59,130,246,.18); filter: brightness(1.02); }
    .stButton > button[data-testid="baseButton-secondary"]:hover { background:#f9fafb; }
    .stButton > button:focus-visible { outline: 3px solid #93c5fd; outline-offset: 2px; }

    /* Button micro-animations */
    @keyframes softPulse { 0%{ transform:scale(1);} 50%{ transform:scale(1.015);} 100%{ transform:scale(1);} }
    .stButton > button:hover { animation: softPulse .35s ease; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background: #eef2ff; color: #1e3a8a;
        border-radius: 10px 10px 0 0; padding: 12px 20px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background: #dbeafe; color: #0f172a; }

    /* Insights */
    .insight-box { background: #f0f9ff; border-left: 4px solid var(--primary); padding: 20px; border-radius: 12px; }
    .insight-title { color: #0ea5e9; font-weight: 700; }
    .insight-text { color:#0c4a6e; }
    .season-bar-bg { background: #e5e7eb; height: 8px; border-radius: 4px; width: 100%; }
    .season-bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #7c3aed, #22d3ee); }

    /* Procurement cards */
    .health-card { background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); color: white; padding: 30px; border-radius: 16px; box-shadow: var(--shadow); }
    .health-score { font-size: 3.2em; font-weight: 900; text-shadow: 2px 3px 12px rgba(0,0,0,.25); }
    .health-status { font-size: 1em; font-weight: 700; background: rgba(255,255,255,0.18); padding: 6px 16px; border-radius: 16px; display:inline-block; }
    .briefing-text { font-size: 1.05em; line-height: 1.6; opacity: .95; }

    .recommendation-card { background: var(--card); border-radius: 14px; padding: 20px; margin-bottom: 16px; border-left: 6px solid var(--primary); box-shadow: var(--shadow); transition: transform .2s, box-shadow .2s; }
    .recommendation-card:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(0,0,0,.12); }
    .urgency-badge { padding: 6px 12px; border-radius: 14px; font-weight: 700; font-size: .85em; display: inline-block; }

    .supplier-card, .po-card { background: var(--card); border-radius: 14px; padding: 18px; box-shadow: var(--shadow); }
    .po-card { border-left: 6px solid var(--primary); }
    .status-badge { padding: 6px 12px; border-radius: 14px; color: #fff; font-weight: 700; font-size: .8em; }

    .supplier-card-modern { transition: all .25s ease; }
    .supplier-card-modern:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0,0,0,.12) !important; }
    .po-card-timeline { transition: all .2s ease; cursor: pointer; }
    .po-card-timeline:hover { box-shadow: 0 12px 28px rgba(0,0,0,.12) !important; }

    /* Tables */
    .stDataFrame div[data-testid="stTable"] { border-radius: 12px; overflow:hidden; box-shadow: var(--shadow); }

    /* Header */
    .app-header { display:flex; align-items:center; justify-content: space-between; padding: 18px 24px; background: #0f172a; color: #fff; border-radius: 12px; margin-bottom: 16px; box-shadow: 0 10px 24px rgba(2,6,23,.35); }
    .app-header .brand { font-size: 1.1em; font-weight: 800; letter-spacing: .3px; }
    .app-header .tagline { opacity: .8; font-size: .95em; }
</style>
""", unsafe_allow_html=True)

# --- Header Bar ---
st.markdown("""
<div class="app-header">
  <div class="brand">🏭 Expedition Co. Control Tower</div>
  <div class="tagline">GenAI-Powered Supply Chain</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🏭 Expedition Co.")
page = st.sidebar.radio("Navigate", ["Dashboard", "Inventory Management", "Demand Forecasting", "Procurement Agent", "Logistics Risk"])
st.sidebar.markdown("---")
st.sidebar.caption("System Status: 🟢 Online")

# ==========================================
# HELPER FUNCTIONS (DEFINED BEFORE USE)
# ==========================================

def display_recommendations(recommendations, filter_type):
    """Display procurement recommendations with interactive cards"""
    for rec in recommendations:
        st.markdown(f"""
        <div class="recommendation-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                        <h3 style="margin: 0;">{rec['product_name']}</h3>
                        <span class="urgency-badge" style="background: {rec['urgency_color']}; color: white;">
                            {rec['urgency']}
                        </span>
                    </div>
                    <div style="color: #666; margin-bottom: 15px;">
                        SKU: {rec['sku']} | Stock: {rec['current_stock']}/{rec['optimal_stock']} ({rec['stock_percentage']}%)
                    </div>
                    <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
                        💡 <strong>AI Analysis:</strong> {rec['ai_reasoning']}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <div>
                            <div style="color: #666; font-size: 0.85em;">Best Supplier</div>
                            <div style="font-weight: 600;">{rec['supplier_name']}</div>
                        </div>
                        <div>
                            <div style="color: #666; font-size: 0.85em;">Delivery Time</div>
                            <div style="font-weight: 600;">{rec['delivery_days']} days</div>
                        </div>
                        <div>
                            <div style="color: #666; font-size: 0.85em;">Quantity Needed</div>
                            <div style="font-weight: 600;">{rec['quantity_needed']} units</div>
                        </div>
                        <div>
                            <div style="color: #666; font-size: 0.85em;">Estimated Cost</div>
                            <div style="font-weight: 600;">${rec['estimated_cost']:,.2f}</div>
                        </div>
                    </div>
                </div>
                <div style="text-align: center; padding-left: 20px;">
                    <div style="font-size: 2.5em; font-weight: 700; color: #4CAF50;">{rec['supplier_score']}</div>
                    <div style="color: #666; font-size: 0.9em;">Supplier Score</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons with unique keys per tab
        col1, col2 = st.columns(2)
        
        # Include filter_type in key to make it unique across tabs
        if col1.button(f"⚡ Quick PO", key=f"qpo_{filter_type}_{rec['product_id']}", use_container_width=True):
            create_quick_po(rec)
        
        if col2.button(f"📧 Draft Email", key=f"email_{filter_type}_{rec['product_id']}", use_container_width=True):
            draft_procurement_email(rec)
        
        st.divider()

def create_quick_po(rec):
    """Create a PO with one click"""
    with st.spinner("Creating Purchase Order..."):
        try:
            payload = {
                "supplier_id": rec['supplier_id'],
                "product_id": rec['product_id'],
                "product_name": rec['product_name'],
                "quantity": rec['quantity_needed'],
                "unit_price": rec['estimated_cost'] / rec['quantity_needed'] if rec['quantity_needed'] > 0 else 0,
                "priority": "Urgent" if rec['urgency'] == "CRITICAL" else "High"
            }
            res = requests.post(f"{API_URL}/procurement/po/create", json=payload)
            
            if res.status_code == 200:
                result = res.json()
                st.success(f"✅ PO Created: {result['po_number']}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Connection Error: {e}")

def draft_procurement_email(rec):
    """Draft a negotiation email"""
    with st.spinner("AI is drafting your email..."):
        try:
            payload = {
                "product_name": rec['product_name'],
                "supplier_name": rec['supplier_name'],
                "current_stock": rec['current_stock'],
                "optimal_stock": rec['optimal_stock'],
                "unit_price": rec['estimated_cost'] / rec['quantity_needed'] if rec['quantity_needed'] > 0 else 0
            }
            res = requests.post(f"{API_URL}/procurement/draft_email", json=payload)
            
            if res.status_code == 200:
                result = res.json()
                
                with st.expander("📧 Email Draft", expanded=True):
                    st.text_area(
                        "Copy this email:",
                        value=result['email_draft'],
                        height=300
                    )
                    st.info(f"Recommended Quantity: {result['recommended_qty']} units | Estimated Cost: ${result['estimated_cost']:,.2f}")
            else:
                st.error("Failed to generate email")
        except Exception as e:
            st.error(f"Error: {e}")

def update_po_status(po_id, new_status):
    """Update PO status"""
    try:
        res = requests.put(
            f"{API_URL}/procurement/po/{po_id}/status",
            params={"status": new_status}
        )
        
        if res.status_code == 200:
            st.success(f"✅ Status updated to: {new_status}")
            if new_status == "RECEIVED":
                st.balloons()
                st.info("🎉 Stock levels have been automatically updated!")
            st.rerun()
        else:
            st.error("Failed to update status")
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# PAGE 1: DASHBOARD OVERVIEW
# ==========================================
if page == "Dashboard":
    st.title("📊 Control Tower Overview")
    
    inventory_data, orders_data = [], []
    try:
        inv_res = requests.get(f"{API_URL}/inventory/analysis")
        if inv_res.status_code == 200: inventory_data = inv_res.json()
        ord_res = requests.get(f"{API_URL}/orders/")
        if ord_res.status_code == 200: orders_data = ord_res.json()
    except:
        st.error("⚠️ Backend Offline. Please run 'python -m uvicorn main:app --reload'")

    c1, c2, c3, c4 = st.columns(4)
    crit_stock = len([x for x in inventory_data if x.get('status') == 'CRITICAL'])
    
    c1.metric("📦 Total SKUs", len(inventory_data))
    c2.metric("🚨 Critical Stock", crit_stock, delta="-Alert", delta_color="inverse")
    c3.metric("⚠️ High Risk Orders", 2, delta="-Review", delta_color="inverse") 
    c4.metric("🚛 Active POs", 1) 

    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.subheader("🛑 Inventory Health")
        if inventory_data:
            df_inv = pd.DataFrame(inventory_data)
            if not df_inv.empty:
                st.bar_chart(df_inv.set_index('product')['on_hand'], color="#FF4B4B")
    
    with c_right:
        st.subheader("Recent Activity")
        if orders_data:
            df_ord = pd.DataFrame(orders_data)
            if not df_ord.empty:
                st.dataframe(df_ord[['customer_name', 'status']], hide_index=True)
            else:
                st.info("No recent orders.")

# ==========================================
# PAGE 2: INVENTORY MANAGEMENT
# ==========================================
elif page == "Inventory Management":
    st.title("📦 Inventory Control Tower")
    
    # 1. FETCH DATA
    df = pd.DataFrame()
    try:
        res = requests.get(f"{API_URL}/inventory/analysis")
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df = df.rename(columns={
                    "product": "Product", "sku": "SKU", "on_hand": "Stock", 
                    "stage": "Stage", "category": "Category", "unit_price": "Price",
                    "optimal_stock": "Optimal"
                })
    except:
        st.error("Cannot connect to Database.")

    if not df.empty:
        # 2. KPIs
        total_value = (df['Stock'] * df['Price']).sum()
        critical_count = len(df[df['status'] == 'CRITICAL'])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Items", len(df))
        c2.metric("Total Value", f"${total_value:,.0f}")
        c3.metric("Critical Items", critical_count)

        # 3. CHARTS
        st.subheader("Inventory Distribution")
        col_charts, col_actions = st.columns([2, 1])
        
        with col_charts:
            c_pie, c_bar = st.columns(2)
            with c_pie:
                if 'Category' in df.columns:
                    fig_pie = px.pie(df, names='Category', values='Stock', hole=0.4, title="By Category")
                    fig_pie.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0), showlegend=False)
                    st.plotly_chart(fig_pie, use_container_width=True)
            with c_bar:
                if 'Stage' in df.columns:
                    fig_bar = px.bar(df, x='Category', y='Stock', color='Stage', title="By Stage")
                    fig_bar.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
                    st.plotly_chart(fig_bar, use_container_width=True)

        with col_actions:
             st.subheader("Quick Actions")
             st.info(f"💡 AI Suggestion: You have {critical_count} critical items.")
             
             @st.dialog("Add New Product")
             def add_form():
                if 'new_prod_data' not in st.session_state:
                    st.session_state['new_prod_data'] = {
                        "name": "", "cat": "Raw Material", "stage": "Raw Material",
                        "stock": 100, "price": 10.0, "opt": 500, "safe": 50
                    }
                if 'voice_text' not in st.session_state:
                    st.session_state['voice_text'] = ""

                st.write("How do you want to add the product?")
                tab_ai, tab_manual = st.tabs(["🎙️ Voice / AI", "✍️ Manual Entry"])

                with tab_ai:
                    st.info("💡 Click the mic and say something like: 'Add 500 sheets of Metal for 20 dollars'")
                    
                    c_mic, c_info = st.columns([1, 4])
                    with c_mic:
                        text = speech_to_text(language='en', start_prompt="🎤 Record", stop_prompt="🛑 Stop", just_once=False, key='STT')
                    
                    if text: st.session_state['voice_text'] = text
                    
                    user_text = st.text_area("Transcript (Editable)", value=st.session_state['voice_text'], height=70)
                    
                    if st.button("✨ Generate Form", type="primary"):
                        if user_text:
                            with st.spinner("🤖 AI is processing your voice command..."):
                                try:
                                    res = requests.post(f"{API_URL}/ai/parse_product_info", json={"description": user_text})
                                    if res.status_code == 200:
                                        ai_data = res.json()
                                        st.session_state['new_prod_data'].update({
                                            'name': ai_data.get('name', ''),
                                            'cat': ai_data.get('category', 'Raw Material'),
                                            'stage': ai_data.get('stage', 'Raw Material'),
                                            'stock': ai_data.get('current_stock', 0),
                                            'price': ai_data.get('unit_price', 0.0),
                                            'opt': ai_data.get('optimal_stock_level', 100),
                                            'safe': ai_data.get('safety_stock_level', 20)
                                        })
                                        st.success("✅ Voice processed! Check 'Manual Entry' tab.")
                                    else: st.error("AI Failed.")
                                except Exception as e: st.error(f"Error: {e}")

                with tab_manual:
                    with st.form("new_product"):
                        d = st.session_state['new_prod_data']
                        c_a, c_b = st.columns(2)
                        sku = c_a.text_input("SKU (Auto)", f"NEW-{pd.Timestamp.now().strftime('%S%f')[:4]}")
                        name = c_b.text_input("Product Name", value=d['name'])
                        
                        cats = ["Electronics", "Raw Material", "Apparel", "Home", "Food"]
                        cat_idx = cats.index(d['cat']) if d['cat'] in cats else 0
                        cat = c_a.selectbox("Category", cats, index=cat_idx)
                        
                        stages = ["Raw Material", "Work in Progress", "Finished"]
                        stage_idx = stages.index(d['stage']) if d['stage'] in stages else 0
                        stage = c_b.selectbox("Stage", stages, index=stage_idx)
                        
                        stock = c_a.number_input("Current Stock", min_value=0, value=int(d['stock']))
                        optimal = c_b.number_input("Optimal Level", min_value=1, value=int(d['opt']))
                        safety = int(optimal * 0.2) 
                        price = st.number_input("Unit Price ($)", min_value=0.0, value=float(d['price']))
                        
                        if st.form_submit_button("💾 Save to Database"):
                            payload = {
                                "sku": sku, "name": name, "category": cat, "stage": stage,
                                "current_stock": stock, "optimal_stock_level": optimal,
                                "safety_stock_level": safety, "unit_price": price
                            }
                            try:
                                res = requests.post(f"{API_URL}/products/", json=payload)
                                if res.status_code == 200:
                                    st.success("✅ Product Saved!")
                                    st.session_state['new_prod_data'] = {"name": "", "cat": "Raw Material", "stage": "Raw Material", "stock": 100, "price": 10.0, "opt": 500, "safe": 50}
                                    st.session_state['voice_text'] = "" 
                                    st.rerun()
                                else: st.error(f"Error: {res.text}")
                            except Exception as e: st.error(f"Connection Error: {e}")

             @st.dialog("Edit Product")
             def edit_form():
                opts = {f"{row['SKU']} - {row['Product']}": row['id'] for i, row in df.iterrows()}
                sel = st.selectbox("Select Product", list(opts.keys()))
                prod_id = opts[sel]
                curr = df[df['id'] == prod_id].iloc[0]
                with st.form("edit"):
                    new_stage = st.selectbox("Stage", ["Raw Material", "WIP", "Finished"], index=["Raw Material", "WIP", "Finished"].index(curr['Stage']) if curr['Stage'] in ["Raw Material", "WIP", "Finished"] else 0)
                    new_stock = st.number_input("Stock", value=int(curr['Stock']))
                    new_price = st.number_input("Price", value=float(curr['Price']))
                    if st.form_submit_button("Update"):
                        requests.put(f"{API_URL}/products/{prod_id}", json={"stage": new_stage, "current_stock": new_stock, "unit_price": new_price})
                        st.rerun()

             @st.dialog("Log Stock")
             def log_form():
                opts = {f"{row['SKU']} - {row['Product']}": row['id'] for i, row in df.iterrows()}
                sel = st.selectbox("Select Product", list(opts.keys()))
                prod_id = opts[sel]
                with st.form("log"):
                    qty = st.number_input("Quantity (+/-)", step=1, value=10)
                    reason = st.text_input("Reason", "Restock")
                    if st.form_submit_button("Submit"):
                        requests.post(f"{API_URL}/inventory/logs", json={"product_id": prod_id, "quantity_change": qty, "reason": reason})
                        st.rerun()

             @st.dialog("Delete")
             def delete_form():
                opts = {f"{row['SKU']} - {row['Product']}": row['id'] for i, row in df.iterrows()}
                sel = st.selectbox("Select Product", list(opts.keys()))
                if st.button("Confirm Delete", type="primary"):
                    requests.delete(f"{API_URL}/products/{opts[sel]}")
                    st.rerun()

             @st.dialog("💲 AI Smart Pricing")
             def pricing_form():
                opts = {f"{row['SKU']} - {row['Product']}": row['id'] for i, row in df.iterrows()}
                sel = st.selectbox("Select Product", list(opts.keys()))
                prod_id = opts[sel]
                curr = df[df['id'] == prod_id].iloc[0]
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Price", f"${curr['Price']}")
                c2.metric("Stock", int(curr['Stock']))
                c3.metric("Optimal", int(curr['Optimal']))
                
                if st.button("🤖 Analyze Strategy", type="primary"):
                    with st.spinner("Analyzing Market & Inventory..."):
                        try:
                            res = requests.post(f"{API_URL}/ai/pricing_analysis", json={
                                "product_name": curr['Product'], "current_price": float(curr['Price']),
                                "current_stock": int(curr['Stock']), "optimal_stock": int(curr['Optimal']),
                                "category": curr['Category']
                            })
                            if res.status_code == 200:
                                st.session_state['pricing_result'] = res.json()
                                st.session_state['pricing_id'] = prod_id
                            else: st.error("AI Error")
                        except Exception as e: st.error(f"Error: {e}")

                if 'pricing_result' in st.session_state:
                    res = st.session_state['pricing_result']
                    st.divider()
                    st.success(f"Suggestion: {res['action']} price to ${res['new_price']}")
                    st.info(f"💡 Reason: {res['reason']}")
                    if st.button("✅ Apply New Price"):
                        r = requests.put(f"{API_URL}/products/{st.session_state['pricing_id']}", json={"unit_price": res['new_price']})
                        if r.status_code == 200:
                            st.success("Price Updated!")
                            del st.session_state['pricing_result']
                            st.rerun()

             @st.dialog("🔮 The AI Crystal Ball")
             def simulator_form():
                st.write("Stress test your inventory against hypothetical events.")
                scenario_type = st.selectbox("Choose a Scenario", [
                    "Custom Input...", "🚢 Supplier Delay (Port Strike)", "📈 Viral Demand Spike (+50% Sales)",
                    "📉 Economic Downturn (-30% Sales)", "🏭 Factory Fire"
                ])
                scenario = st.text_area("Describe Scenario", "e.g. Blizzard in NY") if scenario_type == "Custom Input..." else scenario_type
                
                if st.button("🚀 Run Simulation", type="primary"):
                    with st.spinner("Simulating..."):
                        try:
                            sim_df = df[['Product', 'Category', 'Stock', 'Price']].copy()
                            sim_df = sim_df.rename(columns={
                                'Product': 'product',
                                'Category': 'category',
                                'Stock': 'on_hand',
                                'Price': 'unit_price'
                            })
                            prod_list = sim_df.to_dict(orient='records')
                            res = requests.post(f"{API_URL}/ai/simulate_scenario", json={"scenario": scenario, "products": prod_list})
                            
                            if res.status_code == 200: st.session_state['sim_result'] = res.json()
                            else: st.error("Simulation Failed.")
                        except Exception as e: st.error(f"Error: {e}")

                if 'sim_result' in st.session_state:
                    res = st.session_state['sim_result']
                    st.divider()
                    st.markdown(f"### 🌪️ Impact Score: {res.get('impact_score', 0)}/100")
                    st.write(res.get('impact_summary'))
                    st.success(f"💡 **Strategy:** {res.get('recommendation')}")

             c1, c2 = st.columns(2)
             c3, c4 = st.columns(2)
             if c1.button("➕ Add", use_container_width=True): add_form()
             if c2.button("✏️ Edit", use_container_width=True): edit_form()
             if c3.button("🔄 Log", use_container_width=True): log_form()
             if c4.button("🗑️ Delete", use_container_width=True): delete_form()
             
             c5, c6 = st.columns(2)
             if c5.button("💲 Smart Pricing", use_container_width=True): pricing_form()
             if c6.button("🔮 Crystal Ball", use_container_width=True): simulator_form()

        st.subheader("Current Inventory Status")
        search_term = st.text_input("🔍 Search Inventory", placeholder="Type Name, SKU, or Category...")
        
        if search_term:
            df_filtered = df[
                df['Product'].str.contains(search_term, case=False, na=False) |
                df['SKU'].str.contains(search_term, case=False, na=False) |
                df['Category'].str.contains(search_term, case=False, na=False)
            ]
        else:
            df_filtered = df

        if not df_filtered.empty:
            df_filtered['Stock_Pct'] = df_filtered['Stock'] / df_filtered['Optimal'].replace(0, 1)
            st.dataframe(
                df_filtered,
                column_order=("SKU", "Product", "Category", "Stage", "Stock", "Stock_Pct", "status", "Price"),
                column_config={
                    "Stock": st.column_config.NumberColumn("Current Stock"),
                    "Stage": st.column_config.TextColumn("Stage"),
                    "Stock_Pct": st.column_config.ProgressColumn("Stock Level", format="%.0f%%", min_value=0, max_value=1.5),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "status": st.column_config.TextColumn("Status"),
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No items match your search.")

    else:
        st.info("No products found.")

# ==========================================
# PAGE 3: DEMAND FORECASTING
# ==========================================
elif page == "Demand Forecasting":
    st.title("📈 AI Demand Forecasting")
    st.caption("Machine learning-powered demand predictions.")

    if 'forecast_result' in st.session_state:
        res = st.session_state['forecast_result']
        insight = res.get('ai_insight', 'AI analysis pending...')
        st.markdown(f"""<div class="insight-box"><div class="insight-title">✨ AI-Powered Insight</div><div class="insight-text">{insight}</div></div>""", unsafe_allow_html=True)

    col_chart, col_season = st.columns([2, 1])

    with col_chart:
        st.subheader("Forecast Upload")
        uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type="csv")
        
        if uploaded_file:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            cols = df.columns.tolist()
            
            with st.expander("⚙️ Column Mapping", expanded=True):
                c1, c2, c3 = st.columns(3)
                def find_col(keywords, columns):
                    for col in columns:
                        if any(k in col.lower() for k in keywords): return col
                    return columns[0]
                
                default_date = find_col(['date', 'time', 'period'], cols)
                default_cat = find_col(['cat', 'prod', 'type', 'sku', 'item'], cols)
                default_val = find_col(['price', 'rev', 'amount', 'total', 'sales'], cols)

                date_col = c1.selectbox("Date Column", cols, index=cols.index(default_date) if default_date in cols else 0)
                cat_col = c2.selectbox("Category/Product Column", cols, index=cols.index(default_cat) if default_cat in cols else 0)
                val_col = c3.selectbox("Revenue/Price Column", cols, index=cols.index(default_val) if default_val in cols else 0)
                
            unique_cats = df[cat_col].unique().tolist() if not df.empty else []
            sel_cat = st.selectbox("Select Product to Forecast", unique_cats)
            
            if st.button("🚀 Generate Forecast", type="primary"):
                with st.spinner(f"Standardizing data for '{sel_cat}' & Forecasting..."):
                    clean_df = df.rename(columns={date_col: 'Date', cat_col: 'Category', val_col: 'Total_Revenue'})
                    buffer = io.StringIO()
                    clean_df.to_csv(buffer, index=False)
                    buffer.seek(0)
                    files = {"file": buffer.getvalue()}
                    data = {"category": sel_cat}
                    try:
                        api_res = requests.post(f"{API_URL}/forecast/upload", files=files, data=data)
                        if api_res.status_code == 200:
                            st.session_state['forecast_result'] = api_res.json()
                            st.rerun()
                        else: st.error(api_res.text)
                    except Exception as e: st.error(f"Connection Error: {e}")

        if 'forecast_result' in st.session_state:
            res = st.session_state['forecast_result']
            if 'chart_data' in res:
                df = pd.DataFrame(res['chart_data'])
                fig = go.Figure()
                hist = df[df['Type'] == 'Historical']
                fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Sales'], mode='lines', name='History', line=dict(color='#00C853', width=3)))
                fore = df[df['Type'] == 'Forecast']
                fig.add_trace(go.Scatter(x=fore['Date'], y=fore['Sales'], mode='lines+markers', name='AI Prediction', line=dict(color='#2962FF', width=3, dash='dot')))
                fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Date", yaxis_title="Revenue ($)", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

    with col_season:
        st.subheader("Seasonal Trends")
        st.markdown("**🎄 Holiday Season (Nov-Dec)**")
        st.markdown("""<div class="season-bar-bg"><div class="season-bar-fill" style="width: 94%;"></div></div>""", unsafe_allow_html=True)

    st.divider()
    st.subheader("External Factor Analysis")
    if 'forecast_result' in st.session_state:
        res = st.session_state['forecast_result']
        factors = res.get('external_factors', [])
        if factors:
            cols = st.columns(3)
            for i, f in enumerate(factors):
                with cols[i % 3]:
                    if isinstance(f, dict):
                        st.metric(f.get('name', 'Factor'), f"{f.get('score', 50)}/100", f.get('impact', 'Neutral'))
                    else:
                        st.info(f"• {str(f)}")

# ==========================================
# PAGE 4: PROCUREMENT AGENT (MAIN PAGE)
# ==========================================
elif page == "Procurement Agent":
    st.title("🤝 AI Procurement Intelligence")
    
    # === 1. MORNING BRIEFING HEADER ===
    try:
        health_res = requests.get(f"{API_URL}/procurement/health")
        if health_res.status_code == 200:
            health_data = health_res.json()
            
            # Health card with gradient
            health_score = health_data.get('health_score', 0)
            status = health_data.get('status', 'UNKNOWN')
            briefing = health_data.get('morning_briefing', 'Loading...')
            critical_count = health_data.get('critical_items_count', 0)
            pending_pos = health_data.get('pending_pos', 0)
            
            # Dynamic color based on health
            if status == "HEALTHY":
                gradient = "linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)"
                status_emoji = "✅"
            elif status == "WARNING":
                gradient = "linear-gradient(135deg, #FF9800 0%, #FFC107 100%)"
                status_emoji = "⚠️"
            else:
                gradient = "linear-gradient(135deg, #F44336 0%, #E91E63 100%)"
                status_emoji = "🚨"
            
            st.markdown(f"""
            <div style="background: {gradient}; color: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 25px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h2 style="margin: 0; font-weight: 300;">Supply Chain Health</h2>
                        <div style="font-size: 4em; font-weight: 900; margin: 10px 0;">{health_score:.1f}/100</div>
                        <div style="background: rgba(255,255,255,0.2); padding: 8px 20px; border-radius: 20px; display: inline-block; font-weight: 600;">
                            {status_emoji} {status}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 2.5em; font-weight: 700;">{critical_count}</div>
                        <div style="opacity: 0.9;">Critical Items</div>
                        <div style="font-size: 2.5em; font-weight: 700; margin-top: 15px;">{pending_pos}</div>
                        <div style="opacity: 0.9;">Pending POs</div>
                    </div>
                </div>
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3); font-size: 1.15em; line-height: 1.6;">
                    <strong>🎯 Morning Briefing:</strong><br>{briefing}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Unable to fetch health metrics. Check backend connection.")
    except Exception as e:
        st.error(f"Connection Error: {e}")
    
    # === 2. SMART RECOMMENDATION ENGINE ===
    st.subheader("🎯 AI-Powered Procurement Recommendations")
    st.caption("Smart supplier matching with urgency-based prioritization")
    
    try:
        rec_res = requests.get(f"{API_URL}/procurement/recommendations")
        if rec_res.status_code == 200:
            recommendations = rec_res.json()
            
            if not recommendations:
                st.success("🎉 All inventory levels are optimal! No urgent procurement needed.")
            else:
                # Tabs for filtering
                tab_all, tab_critical, tab_high = st.tabs(["📋 All", "🚨 Critical", "⚠️ High Priority"])
                
                with tab_all:
                    display_recommendations(recommendations, "ALL")
                
                with tab_critical:
                    critical_recs = [r for r in recommendations if r['urgency'] == 'CRITICAL']
                    if critical_recs:
                        display_recommendations(critical_recs, "CRITICAL")
                    else:
                        st.success("No critical items!")
                
                with tab_high:
                    high_recs = [r for r in recommendations if r['urgency'] == 'HIGH']
                    if high_recs:
                        display_recommendations(high_recs, "HIGH")
                    else:
                        st.info("No high priority items.")
        else:
            st.error("Failed to load recommendations.")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.divider()
    
    # === 3. SUPPLIER INTELLIGENCE NETWORK ===
    st.subheader("🏢 Supplier Intelligence Network")
    
    tab_perf, tab_manage = st.tabs(["📊 Performance Analytics", "⚙️ Manage Suppliers"])
    
    with tab_perf:
        try:
            sup_res = requests.get(f"{API_URL}/procurement/suppliers/analysis")
            if sup_res.status_code == 200:
                suppliers = sup_res.json()
                
                if not suppliers:
                    st.info("No suppliers in database. Add your first supplier in the 'Manage Suppliers' tab.")
                else:
                    # Summary KPIs
                    total_suppliers = len(suppliers)
                    avg_reliability = sum(s['reliability_score'] for s in suppliers) / total_suppliers
                    avg_on_time = sum(s['on_time_delivery_rate'] for s in suppliers) / total_suppliers
                    total_pos = sum(s['total_pos'] for s in suppliers)
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Suppliers", total_suppliers)
                    c2.metric("Avg Reliability", f"{avg_reliability:.1f}")
                    c3.metric("Avg On-Time", f"{avg_on_time:.1f}%")
                    c4.metric("Total POs", total_pos)

                    st.divider()

                    # Leaderboard
                    st.subheader("🏆 Leaderboard")
                    leaderboard_df = pd.DataFrame([
                        {
                            "Supplier": s['name'],
                            "Score": s['overall_score'],
                            "Reliability": s['reliability_score'],
                            "On-Time": s['on_time_delivery_rate'],
                            "POs": s['total_pos'],
                            "Category": s['category'],
                            "Verdict": s['verdict'].replace('_', ' ')
                        }
                        for s in sorted(suppliers, key=lambda x: x['overall_score'], reverse=True)
                    ])
                    st.dataframe(
                        leaderboard_df,
                        use_container_width=True,
                    )

                    st.divider()
                    st.subheader("Supplier Network")

                    # Responsive grid of supplier cards (3 columns)
                    for i in range(0, len(suppliers), 3):
                        cols = st.columns(3)
                        for idx, col in enumerate(cols):
                            if i + idx < len(suppliers):
                                s = suppliers[i + idx]
                                verdict_label = s['verdict'].replace('_', ' ')
                                verdict_color = (
                                    "#10b981" if s['verdict'] == "PREFERRED" else
                                    "#f59e0b" if s['verdict'] == "REVIEW_NEEDED" else
                                    "#ef4444"
                                )
                                with col:
                                    st.markdown(f"""
<div class="supplier-card supplier-card-modern">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <h4 style="margin:0;">{s['name']}</h4>
      <span class="status-badge" style="background:{verdict_color};">{verdict_label}</span>
    </div>
    <div style="text-align:right;">
      <div style="font-size:1.6em; font-weight:800; color:#2563eb;">{s['overall_score']}</div>
      <div style="font-size:.8em; color:#6b7280;">Score</div>
    </div>
  </div>
  <div style="margin:12px 0; color:#6b7280;">📦 {s['category']} • ⏱️ {s['delivery_speed_days']} days • 💰 ${s['price_per_unit']:.2f}/unit</div>
  <div style="display:grid; grid-template-columns:1fr; gap:10px;">
    <div>
      <div style="display:flex; justify-content:space-between;"><span>Reliability</span><span>{s['reliability_score']}</span></div>
      <div style="background:#e5e7eb; height:8px; border-radius:6px;"><div style="width:{s['reliability_score']}%; background:#10b981; height:8px; border-radius:6px;"></div></div>
    </div>
    <div>
      <div style="display:flex; justify-content:space-between;"><span>On-Time</span><span>{s['on_time_delivery_rate']}%</span></div>
      <div style="background:#e5e7eb; height:8px; border-radius:6px;"><div style="width:{s['on_time_delivery_rate']}%; background:#2563eb; height:8px; border-radius:6px;"></div></div>
    </div>
    <div style="display:flex; justify-content:space-between; color:#374151;">
      <div>POs: <strong>{s['total_pos']}</strong></div>
      <div>Lead Time: <strong>{s['delivery_speed_days']} days</strong></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

                    st.caption("Tip: Use Manage Suppliers to add or update entries.")
            else:
                st.error("Failed to load supplier data.")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with tab_manage:
        st.subheader("➕ Add New Supplier")
        st.caption("Expand your supplier network with AI-powered trust scoring")
        
        st.divider()
        
        with st.form("add_supplier_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Supplier Name*", placeholder="e.g., Acme Corporation", help="Official business name")
                category = st.selectbox("Category", ["Electronics", "Raw Material", "Apparel", "Home", "Food"], help="Primary product category")
                reliability = st.slider("Reliability Score", 0, 100, 95, help="Based on past performance (0-100)")
            
            with col2:
                email = st.text_input("Contact Email*", placeholder="procurement@acme.com", help="Primary procurement contact")
                delivery_days = st.number_input("Delivery Speed (Days)", min_value=1, value=5, help="Average delivery time")
                price_unit = st.number_input("Price per Unit ($)", min_value=0.0, value=10.0, step=0.1, help="Average unit price")
            
            st.markdown("---")
            
            col_submit, col_info = st.columns([1, 2])
            
            with col_submit:
                submitted = st.form_submit_button("➕ Add Supplier", type="primary", use_container_width=True)
            
            with col_info:
                st.info("💡 AI will calculate an initial trust score based on the metrics you provide")
            
            if submitted:
                if not name or not email:
                    st.error("⚠️ Supplier name and email are required!")
                elif "@" not in email:
                    st.error("⚠️ Please enter a valid email address")
                else:
                    with st.spinner("🤖 Adding supplier and calculating trust score..."):
                        try:
                            payload = {
                                "name": name,
                                "contact_email": email,
                                "category": category,
                                "delivery_speed_days": delivery_days,
                                "reliability_score": reliability,
                                "price_per_unit": price_unit
                            }
                            res = requests.post(f"{API_URL}/procurement/suppliers/create", json=payload)
                            
                            if res.status_code == 200:
                                result = res.json()
                                st.success(f"✅ Supplier '{name}' added successfully!")
                                st.balloons()
                                
                                # Show trust score using metric
                                st.metric(
                                    label="🎯 Initial Trust Score",
                                    value=result['initial_trust_score'],
                                    help="Based on reliability, speed, and pricing"
                                )
                                
                                st.info("🔄 Refresh the Performance Analytics tab to see the new supplier")
                            else:
                                error_detail = res.json().get('detail', 'Unknown error')
                                st.error(f"❌ Error: {error_detail}")
                        except requests.exceptions.ConnectionError:
                            st.error("❌ Cannot connect to backend. Please ensure the API is running.")
                        except Exception as e:
                            st.error(f"❌ Connection Error: {e}")
    
    st.divider()
    
    # === 4. PURCHASE ORDER MANAGEMENT ===
    st.subheader("📄 Purchase Order Management")
    
    tab_orders, tab_create = st.tabs(["📋 Order History", "➕ Create Custom PO"])
    
    with tab_orders:
        try:
            po_res = requests.get(f"{API_URL}/procurement/po/list")
            if po_res.status_code == 200:
                pos = po_res.json()
                
                if not pos:
                    st.info("No purchase orders yet. Create your first PO or use Quick PO from recommendations.")
                else:
                    # Group by status for better organization
                    status_order = ["DRAFT", "APPROVED", "IN_TRANSIT", "RECEIVED"]
                    pos_sorted = sorted(pos, key=lambda x: status_order.index(x['status']) if x['status'] in status_order else 999)
                    
                    for po in pos_sorted:
                        # Status progression indicators
                        status_progress = {
                            "DRAFT": {"progress": 25, "icon": "📝", "color": "#9E9E9E"},
                            "APPROVED": {"progress": 50, "icon": "✅", "color": "#2196F3"},
                            "IN_TRANSIT": {"progress": 75, "icon": "🚚", "color": "#FF9800"},
                            "RECEIVED": {"progress": 100, "icon": "📦", "color": "#4CAF50"}
                        }
                        
                        status_info = status_progress.get(po['status'], {"progress": 0, "icon": "❓", "color": "#757575"})
                        
                        # Priority colors
                        priority_colors = {
                            "Low": "🔵",
                            "Medium": "🟡",
                            "High": "🟠",
                            "Urgent": "🔴"
                        }
                        priority_emoji = priority_colors.get(po['priority'], "⚪")

                        # Modern PO card header
                        with st.container():
                            st.markdown(f"""
                            <div class="po-card">
                              <div class="po-header">
                                <div>
                                  <div class="po-title">{po['po_number']} {status_info['icon']} {po['status']}</div>
                                  <div class="po-meta">{po['product_name']} • {po['supplier_name']}</div>
                                </div>
                                <div style="display:flex; gap:8px; align-items:center;">
                                  <span class="po-status" style="background:{status_info['color']}">{po['status']}</span>
                                  <span class="priority-pill">{priority_emoji} {po['priority']}</span>
                                </div>
                              </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Progress + caption
                            st.progress(status_info['progress'] / 100)
                            st.markdown('<div class="progress-caption">Draft → Approved → In Transit → Received</div>', unsafe_allow_html=True)

                            # Details grid
                            detail_cols = st.columns(4)
                            detail_cols[0].metric("Quantity", f"{po['quantity']} units")
                            detail_cols[1].metric("Total Value", f"${po['total_value']:,.2f}")
                            detail_cols[2].metric("Expected", po['expected_delivery'])
                            days_color = "normal" if po['days_remaining'] > 5 else "inverse"
                            detail_cols[3].metric("Days Left", f"{po['days_remaining']}", delta=f"{po['days_remaining']} days", delta_color=days_color)

                            st.caption(f"🕒 Created on {po['created_at']}")

                        # Action buttons row
                        col1, col2, col3 = st.columns([1, 1, 1])
                        can_approve = po['status'] == "DRAFT"
                        can_transit = po['status'] == "APPROVED"
                        can_receive = po['status'] == "IN_TRANSIT"

                        with col1:
                            if st.button("✅ Approve", key=f"approve_{po['id']}", disabled=not can_approve, use_container_width=True, type="primary" if can_approve else "secondary"):
                                update_po_status(po['id'], "APPROVED")
                        with col2:
                            if st.button("🚚 Transit", key=f"transit_{po['id']}", disabled=not can_transit, use_container_width=True, type="primary" if can_transit else "secondary"):
                                update_po_status(po['id'], "IN_TRANSIT")
                        with col3:
                            if st.button("📦 Receive", key=f"receive_{po['id']}", disabled=not can_receive, use_container_width=True, type="primary" if can_receive else "secondary"):
                                update_po_status(po['id'], "RECEIVED")
                        st.markdown("<br><br>", unsafe_allow_html=True)
            else:
                st.error("Failed to load POs.")
        except Exception as e:
            st.error(f"Error: {e}")
    
    with tab_create:
        st.write("### Manual PO Creation")
        
        # Get products and suppliers for dropdown
        try:
            inv_res = requests.get(f"{API_URL}/inventory/analysis")
            sup_res = requests.get(f"{API_URL}/procurement/suppliers/analysis")
            
            products = inv_res.json() if inv_res.status_code == 200 else []
            suppliers = sup_res.json() if sup_res.status_code == 200 else []
            
            if not products or not suppliers:
                st.warning("Add products and suppliers first.")
            else:
                with st.form("create_po_form"):
                    col1, col2 = st.columns(2)
                    
                    product_opts = {f"{p['sku']} - {p['product']}": p for p in products}
                    selected_product_key = col1.selectbox("Select Product", list(product_opts.keys()))
                    selected_product = product_opts[selected_product_key]
                    
                    supplier_opts = {s['name']: s for s in suppliers}
                    selected_supplier_key = col2.selectbox("Select Supplier", list(supplier_opts.keys()))
                    selected_supplier = supplier_opts[selected_supplier_key]
                    
                    # Show supplier delivery estimate
                    col2.info(f"📦 Estimated Delivery: {selected_supplier['delivery_speed_days']} days")
                    
                    quantity = col1.number_input("Quantity", min_value=1, value=100)
                    unit_price = col2.number_input("Unit Price ($)", min_value=0.0, value=float(selected_product['unit_price']), step=0.1)
                    
                    priority = col1.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
                    
                    total_cost = quantity * unit_price
                    st.metric("Total Cost", f"${total_cost:,.2f}")
                    
                    submitted = st.form_submit_button("🚀 Create Purchase Order", type="primary")
                    
                    if submitted:
                        with st.spinner("Creating PO..."):
                            try:
                                payload = {
                                    "supplier_id": selected_supplier['id'],
                                    "product_id": selected_product['id'],
                                    "product_name": selected_product['product'],
                                    "quantity": quantity,
                                    "unit_price": unit_price,
                                    "priority": priority
                                }
                                res = requests.post(f"{API_URL}/procurement/po/create", json=payload)
                                
                                if res.status_code == 200:
                                    result = res.json()
                                    st.success(f"✅ PO Created: {result['po_number']}")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {res.text}")
                            except Exception as e:
                                st.error(f"Connection Error: {e}")
        except Exception as e:
            st.error(f"Error loading data: {e}")

# ==========================================
# PAGE 5: LOGISTICS
# ==========================================
elif page == "Logistics Risk":
    st.title("🚛 Logistics Control Tower")
    col_map, col_controls = st.columns([2, 1])

    with col_controls:
        start = st.text_input("Origin", "Mumbai, India")
        end = st.text_input("Destination", "Kathmandu, Nepal")
        if st.button("🗺️ Optimize Route"):
            with st.spinner("Calculating..."):
                try:
                    res = requests.post(f"{API_URL}/logistics/plan_route", json={"start_address": start, "end_address": end})
                    if res.status_code == 200: st.session_state['route_data'] = res.json()
                except: st.error("Connection Error")
        
        if 'route_data' in st.session_state:
            d = st.session_state['route_data']
            st.metric("Distance", f"{d['route_info']['distance_km']} km")
            st.info(d['risk_analysis'])

    with col_map:
        if 'route_data' in st.session_state:
            d = st.session_state['route_data']
            m = folium.Map(location=[20, 78], zoom_start=5)
            folium.PolyLine(polyline.decode(d['route_info']['geometry']), color="blue").add_to(m)
            st_folium(m, width="100%", height=500)
        else:
            st_folium(folium.Map(location=[20, 78], zoom_start=5), width="100%", height=500)