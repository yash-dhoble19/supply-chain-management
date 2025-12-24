import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import io
import folium
from streamlit_folium import st_folium
import polyline
from datetime import datetime, timedelta  # For Date/Time Math


# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Expedition Co. Control Tower", layout="wide", page_icon="🏭")

# --- 🎨 PRO-LEVEL CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    
    /* Card Container */
    .css-1r6slb0, .css-1wivap2 {
        background-color: white; border-radius: 12px; 
        padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: white; border: 1px solid #eef2f6; 
        padding: 15px; border-radius: 10px; text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    /* AI Insight Box (Blue) */
    .insight-box {
        background-color: #e8f4fd; border-left: 4px solid #2196f3;
        padding: 20px; border-radius: 8px; margin-bottom: 20px;
    }
    .insight-title { color: #1565c0; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    .insight-text { color: #0d47a1; font-size: 1.05em; }
    
    /* Seasonal Bars */
    .season-bar-bg { background-color: #eee; height: 8px; border-radius: 4px; width: 100%; margin-top: 5px; }
    .season-bar-fill { height: 8px; border-radius: 4px; background: linear-gradient(90deg, #aa00ff, #e040fb); }
    
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("🏭 Expedition Co.")
page = st.sidebar.radio("Navigate", ["Dashboard", "Demand Forecasting", "Procurement Agent", "Logistics Risk"])
st.sidebar.markdown("---")
st.sidebar.caption("System Status: 🟢 Online")

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard":
    st.title("📊 Control Tower Overview")
    
    inventory_data, orders_data = [], []
    try:
        inv_res = requests.get(f"{API_URL}/inventory/analysis")
        if inv_res.status_code == 200: inventory_data = inv_res.json()
        ord_res = requests.get(f"{API_URL}/orders/")
        if ord_res.status_code == 200: orders_data = ord_res.json()
    except:
        st.error("⚠️ Backend Offline. Please restart 'main.py'.")

    c1, c2, c3, c4 = st.columns(4)
    crit_stock = len([x for x in inventory_data if x.get('status') == 'CRITICAL'])
    
    c1.metric("📦 Total SKUs", len(inventory_data))
    c2.metric("🚨 Critical Stock", crit_stock, delta="-Alert", delta_color="inverse")
    c3.metric("⚠️ High Risk Orders", 2, delta="-Review", delta_color="inverse") # Dummy for now
    c4.metric("🚛 Active POs", 1) 

    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.subheader("🛑 Inventory Health")
        if inventory_data:
            df_inv = pd.DataFrame(inventory_data)
            if not df_inv.empty:
                st.bar_chart(df_inv.set_index('product')['on_hand'], color="#FF4B4B")
                
                crit_items = df_inv[df_inv['status'] == 'CRITICAL']
                if not crit_items.empty:
                    st.error(f"Action Required: {crit_items.iloc[0]['product']} is below safety levels!")
    
    with c_right:
        st.subheader("Recent Activity")
        if orders_data:
            df_ord = pd.DataFrame(orders_data)
            st.dataframe(df_ord[['customer_name', 'status']], hide_index=True)

# --- PAGE 2: DEMAND FORECASTING (UNIVERSAL EDITION) ---
elif page == "Demand Forecasting":
    st.title("📈 AI Demand Forecasting")
    st.caption("Machine learning-powered demand predictions with market context.")

    # 1. AI INSIGHT
    if 'forecast_result' in st.session_state:
        res = st.session_state['forecast_result']
        insight = res.get('ai_insight', 'AI analysis pending...')
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">✨ AI-Powered Insight</div>
            <div class="insight-text">{insight}</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. MAIN LAYOUT
    col_chart, col_season = st.columns([2, 1])

    with col_chart:
        st.subheader("12-Month Demand Forecast")
        
        uploaded_file = st.file_uploader("Upload Sales Data (CSV)", type="csv")
        
        if uploaded_file:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file)
            cols = df.columns.tolist()
            
            # --- 🛠️ DYNAMIC MAPPING SECTION ---
            with st.expander("⚙️ Column Mapping (Configure your file)", expanded=True):
                st.info("Please confirm which columns match our data points.")
                c1, c2, c3 = st.columns(3)
                
                # Auto-guess defaults to save time
                def find_col(keywords, columns):
                    for col in columns:
                        if any(k in col.lower() for k in keywords): return col
                    return columns[0]

                default_date = find_col(['date', 'time', 'period'], cols)
                default_cat = find_col(['cat', 'prod', 'type', 'sku', 'item'], cols)
                default_val = find_col(['price', 'rev', 'amount', 'total', 'sales'], cols)

                # The User Selects the actual columns
                date_col = c1.selectbox("Date Column", cols, index=cols.index(default_date) if default_date in cols else 0)
                cat_col = c2.selectbox("Category/Product Column", cols, index=cols.index(default_cat) if default_cat in cols else 0)
                val_col = c3.selectbox("Revenue/Price Column", cols, index=cols.index(default_val) if default_val in cols else 0)
            
            # Get categories from the USER SELECTED column
            unique_cats = df[cat_col].unique().tolist()
            sel_cat = st.selectbox("Select Product to Forecast", unique_cats)
            
            # GENERATE BUTTON
            if st.button("🚀 Generate New Forecast", type="primary"):
                with st.spinner(f"Standardizing data for '{sel_cat}' & Forecasting..."):
                    
                    # 1. STANDARDIZE THE DATAFRAME LOCALLY
                    # We rename the user's messy columns to the clean names the Backend expects
                    clean_df = df.rename(columns={
                        date_col: 'Date',
                        cat_col: 'Category',
                        val_col: 'Total_Revenue' 
                    })
                    
                    # Convert to CSV buffer to send to backend
                    buffer = io.StringIO()
                    clean_df.to_csv(buffer, index=False)
                    buffer.seek(0)
                    
                    # Send the CLEANED file
                    files = {"file": buffer.getvalue()}
                    data = {"category": sel_cat}
                    
                    try:
                        api_res = requests.post(f"{API_URL}/forecast/upload", files=files, data=data)
                        if api_res.status_code == 200:
                            st.session_state['forecast_result'] = api_res.json()
                            st.rerun()
                        else:
                            st.error(f"Server Error: {api_res.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")

        # CHART RENDERER
        if 'forecast_result' in st.session_state:
            res = st.session_state['forecast_result']
            if 'chart_data' in res:
                df = pd.DataFrame(res['chart_data'])
                fig = go.Figure()
                
                hist = df[df['Type'] == 'Historical']
                fig.add_trace(go.Scatter(x=hist['Date'], y=hist['Sales'], mode='lines', 
                                       name='History', line=dict(color='#00C853', width=3)))
                
                fore = df[df['Type'] == 'Forecast']
                fig.add_trace(go.Scatter(x=fore['Date'], y=fore['Sales'], mode='lines+markers', 
                                       name='AI Prediction', line=dict(color='#2962FF', width=3, dash='dot')))

                fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                  xaxis_title="Date", yaxis_title="Revenue ($)", hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)

    with col_season:
        st.subheader("Seasonal Trends")
        st.markdown("**Identified patterns**")
        
        # (Static Visuals for Demo)
        st.write("")
        st.markdown("**🎄 Holiday Season (Nov-Dec)**")
        st.markdown("""<div class="season-bar-bg"><div class="season-bar-fill" style="width: 94%;"></div></div>""", unsafe_allow_html=True)
        st.caption("Impact: Very High")
        
        st.write("")
        st.markdown("**📱 Tech Launch (Sep-Oct)**")
        st.markdown("""<div class="season-bar-bg"><div class="season-bar-fill" style="width: 70%;"></div></div>""", unsafe_allow_html=True)
        st.caption("Impact: High")

    # 3. EXTERNAL FACTORS
    st.divider()
    st.subheader("External Factor Analysis")
    if 'forecast_result' in st.session_state:
        res = st.session_state['forecast_result']
        factors = res.get('external_factors', [])
        if factors:
            cols = st.columns(3)
            for i, f in enumerate(factors):
                with cols[i % 3]:
                    st.metric(f.get('name'), f"{f.get('score', 50)}/100", f.get('impact', 'Neutral'))

# --- PAGE 3: PROCUREMENT ---
elif page == "Procurement Agent":
    st.title("🤝 AI Negotiator")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("### Request Settings")
        material = st.text_input("Material", "Gore-Tex Fabric")
        qty = st.number_input("Qty", 500)
        days = st.number_input("Deadline (Days)", 5)
        
        if st.button("🚀 Run AI Analysis", type="primary"):
            with st.spinner("Analyzing Suppliers..."):
                payload = {"material_name": material, "quantity": qty, "max_days_allowed": days}
                try:
                    res = requests.post(f"{API_URL}/procurement/compare/", json=payload)
                    st.session_state['procurement_result'] = res.json().get('ai_recommendation', 'No recommendation found.')
                except Exception as e:
                    st.error(f"Connection Failed: {e}")

    with col2:
        st.markdown("### AI Recommendation")
        if 'procurement_result' in st.session_state:
            st.info(st.session_state['procurement_result'])
        else:
            st.write("👈 Set parameters and click Run.")

# --- PAGE 4: LOGISTICS RISK ---
elif page == "Logistics Risk":
    st.title("🚛 Logistics Control Tower")
    st.caption("Route Optimization & Geopolitical Risk Analysis")

    # Layout: Map on Top, Inputs/Stats below
    col_map, col_controls = st.columns([2, 1])

    with col_controls:
        st.subheader("📍 Route Planner")
        
        # Default Warehouse Location
        start_addr = st.text_input("Origin (Warehouse)", "Mumbai, India")
        end_addr = st.text_input("Destination (Customer)", "Kathmandu, Nepal")
        
        plan_btn = st.button("🗺️ Optimize Route", type="primary")
        
        if plan_btn:
            with st.spinner("Calculating optimal path & analyzing risks..."):
                payload = {"start_address": start_addr, "end_address": end_addr}
                try:
                    res = requests.post(f"{API_URL}/logistics/plan_route", json=payload)
                    if res.status_code == 200:
                        st.session_state['route_data'] = res.json()
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")

        # SHOW STATS IF DATA EXISTS
        if 'route_data' in st.session_state:
            data = st.session_state['route_data']
            route = data['route_info']
            
            st.divider()
            st.markdown("### 📊 Trip Metrics")
            c1, c2, c3 = st.columns(3) # Use 3 columns for better layout
            
            # 1. Distance
            c1.metric("Distance", f"{route['distance_km']} km")
            
            # 2. Duration (Formatted nicely)
            total_mins = int(route['duration_min'])
            hours = total_mins // 60
            minutes = total_mins % 60
            
            if hours > 0:
                time_fmt = f"{hours}h {minutes}m"
            else:
                time_fmt = f"{minutes}m"
                
            c2.metric("Duration", time_fmt)
            
            # 3. Estimated Arrival (Date + Time)
            # Assuming the trip starts 'Now'
            arrival_dt = datetime.now() + timedelta(minutes=total_mins)
            arrival_str = arrival_dt.strftime("%d %b %I:%M %p") # e.g. 21 Dec 04:30 PM
            
            c3.metric("Est. Arrival", arrival_str)
            
            st.markdown("### 🛡️ AI Risk Assessment")
            st.info(data['risk_analysis'])

    with col_map:
        # MAP RENDERING LOGIC
        if 'route_data' in st.session_state:
            data = st.session_state['route_data']
            start = data['start_coords']
            end = data['end_coords']
            geom = data['route_info']['geometry']
            
            # Create Map centered between points
            mid_lat = (start[0] + end[0]) / 2
            mid_lon = (start[1] + end[1]) / 2
            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=6)

            # 1. Add Route Line
            # Decode Google's polyline
            route_coords = polyline.decode(geom)
            folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

            # 2. Add Markers
            folium.Marker(start, popup="Warehouse", icon=folium.Icon(color="green", icon="warehouse", prefix="fa")).add_to(m)
            folium.Marker(end, popup="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)

        else:
            # Default empty map
            m = folium.Map(location=[20.5937, 78.9629], zoom_start=5) # Center of India

        # Render map in Streamlit
        st_folium(m, width="100%", height=500)