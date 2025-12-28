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

# --- 🎨 PRO-LEVEL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    .css-1r6slb0, .css-1wivap2 {
        background-color: white; border-radius: 12px; 
        padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] {
        background-color: white; border: 1px solid #eef2f6; 
        padding: 15px; border-radius: 10px; text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .insight-box {
        background-color: #e8f4fd; border-left: 4px solid #2196f3;
        padding: 20px; border-radius: 8px; margin-bottom: 20px;
    }
    .insight-title { color: #1565c0; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    .insight-text { color: #0d47a1; font-size: 1.05em; }
    .season-bar-bg { background-color: #eee; height: 8px; border-radius: 4px; width: 100%; margin-top: 5px; }
    .season-bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #aa00ff, #e040fb); }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🏭 Expedition Co.")
page = st.sidebar.radio("Navigate", ["Dashboard", "Inventory Management", "Demand Forecasting", "Procurement Agent", "Logistics Risk"])
st.sidebar.markdown("---")
st.sidebar.caption("System Status: 🟢 Online")

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
                # Rename for UI consistency
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
             
             # --- ADD PRODUCT (VOICE ENABLED) ---
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

                # --- TAB 1: VOICE & AI ---
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

                # --- TAB 2: MANUAL FORM ---
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

             # --- AI SMART PRICING ---
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

             # --- AI CRYSTAL BALL (SCENARIO SIMULATOR) ---
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
                            # --- FIX: Map UI Columns (Capitalized) back to Backend Columns (lowercase) ---
                            # 1. Select the columns available in the UI dataframe 'df'
                            sim_df = df[['Product', 'Category', 'Stock', 'Price']].copy()
                            
                            # 2. Rename them to match what main.py expects: product, category, on_hand, unit_price
                            sim_df = sim_df.rename(columns={
                                'Product': 'product',
                                'Category': 'category',
                                'Stock': 'on_hand',
                                'Price': 'unit_price'
                            })
                            
                            # 3. Convert to list of dictionaries
                            prod_list = sim_df.to_dict(orient='records')
                            
                            # 4. Send request
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

             # ACTION BUTTONS GRID
             c1, c2 = st.columns(2)
             c3, c4 = st.columns(2)
             if c1.button("➕ Add", use_container_width=True): add_form()
             if c2.button("✏️ Edit", use_container_width=True): edit_form()
             if c3.button("🔄 Log", use_container_width=True): log_form()
             if c4.button("🗑️ Delete", use_container_width=True): delete_form()
             
             c5, c6 = st.columns(2)
             if c5.button("💲 Smart Pricing", use_container_width=True): pricing_form()
             if c6.button("🔮 Crystal Ball", use_container_width=True): simulator_form()

        # 4. MAIN TABLE (WITH SEARCH BAR)
        st.subheader("Current Inventory Status")
        
        # --- NEW: SEARCH BAR ---
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
# PAGE 4: PROCUREMENT
# ==========================================
elif page == "Procurement Agent":
    st.title("🤝 AI Negotiator")
    col1, col2 = st.columns([1, 2])
    with col1:
        material = st.text_input("Material", "Gore-Tex Fabric")
        qty = st.number_input("Qty", 500)
        days = st.number_input("Deadline", 5)
        if st.button("🚀 Run AI Analysis"):
            with st.spinner("Analyzing..."):
                try:
                    res = requests.post(f"{API_URL}/procurement/compare/", json={"material_name": material, "quantity": qty, "max_days_allowed": days})
                    st.session_state['procurement_result'] = res.json().get('ai_recommendation')
                except: st.error("Connection Failed")
    with col2:
        if 'procurement_result' in st.session_state:
            st.info(st.session_state['procurement_result'])

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