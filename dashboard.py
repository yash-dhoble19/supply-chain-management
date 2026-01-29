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
import json
import os
import streamlit.components.v1 as components
import time
# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Expedition Co. Control Tower", layout="wide", page_icon="🏭")
# Country mapping
COUNTRY_MAP = {
    "India": "IN",
    "United States": "US",
    "United Kingdom": "UK"
}

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

    .supplier-card, .po-card { background: var(--card); border-radius: 14px; padding: 18px; box-shadow: var(--shadow); transition: transform .18s ease, box-shadow .18s ease; }
    .po-card { border: 1px solid #e5e7eb; border-left: 6px solid var(--primary); }
    .po-card:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(0,0,0,.12); }
    .po-header { display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
    .po-title { font-weight: 800; font-size: 1.05em; margin:0 0 4px 0; color: #0f172a; letter-spacing:.3px; }
    .po-meta { color: var(--muted); font-size:.95em; }
    .po-status { padding: 6px 10px; border-radius: 12px; color: #fff; font-weight: 700; font-size:.8em; box-shadow: 0 4px 12px rgba(0,0,0,.08); }
    .priority-pill { padding: 6px 10px; border-radius: 12px; font-weight: 700; font-size:.8em; background:#f9fafb; color:#111827; border: 1px solid #e5e7eb; }
    .progress-caption { margin-top: 6px; color:#6b7280; font-size:.85em; }

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
page = st.sidebar.radio("Navigate", ["Dashboard", "Inventory Management", "Demand Forecasting", "Procurement Agent", "Logistics Risk", "Logistics Optimize"])
st.sidebar.markdown("---")
st.sidebar.caption("System Status: 🟢 Online")

# --- SESSION STATE INITIALIZATION ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"  # "main" or "generate"
if "forecast_result" not in st.session_state:
    st.session_state.forecast_result = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = None
if "validation_result" not in st.session_state:
    st.session_state.validation_result = None
if "selected_external_factors" not in st.session_state:
    st.session_state.selected_external_factors = {}
if "forecast_history" not in st.session_state:
    st.session_state.forecast_history = []  # List to store all forecasts
if "storage_initialized" not in st.session_state:
    st.session_state.storage_initialized = False

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
    # Professional Dashboard Header
    st.markdown("""
    <div style="background: #1e3a8a; 
                color: white; padding: 24px 32px; border-radius: 12px; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 24px;">
        <h1 style="margin: 0; font-size: 2em; font-weight: 700; letter-spacing: -0.5px;">Control Tower Overview</h1>
        <p style="margin: 8px 0 0 0; font-size: 0.95em; opacity: 0.85; font-weight: 400;">Real-time supply chain intelligence and analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch all data
    inventory_data, orders_data, pos_data, health_data = [], [], [], {}
    try:
        inv_res = requests.get(f"{API_URL}/inventory/analysis")
        if inv_res.status_code == 200: inventory_data = inv_res.json()
        
        ord_res = requests.get(f"{API_URL}/orders/")
        if ord_res.status_code == 200: orders_data = ord_res.json()
        
        po_res = requests.get(f"{API_URL}/procurement/po/list")
        if po_res.status_code == 200: pos_data = po_res.json()
        
        health_res = requests.get(f"{API_URL}/procurement/health")
        if health_res.status_code == 200: health_data = health_res.json()
    except:
        st.error("⚠️ Backend Offline. Please run 'python -m uvicorn main:app --reload'")

    # Calculate metrics
    crit_stock = len([x for x in inventory_data if x.get('status') == 'CRITICAL'])
    low_stock = len([x for x in inventory_data if x.get('status') == 'LOW'])
    active_pos = len([x for x in pos_data if x.get('status') in ['DRAFT', 'APPROVED', 'IN_TRANSIT']])
    total_value = sum([x.get('on_hand', 0) * x.get('unit_price', 0) for x in inventory_data])
    health_score = health_data.get('health_score', 0)
    
    # Professional Metrics Styling
    st.markdown("""
    <style>
    .metric-card {
        background: #ffffff;
        padding: 20px 18px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        border-left: 4px solid;
        transition: box-shadow 0.2s ease;
        margin-bottom: 0;
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .metric-value {
        font-size: 2em;
        font-weight: 700;
        margin: 8px 0 6px 0;
        color: #111827;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.8em;
        color: #6b7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .metric-delta {
        font-size: 0.75em;
        margin-top: 8px;
        padding: 3px 10px;
        border-radius: 6px;
        display: inline-block;
        font-weight: 500;
    }
    .activity-item {
        background: #ffffff;
        padding: 12px 14px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #e5e7eb;
        border-left: 3px solid;
        transition: border-color 0.2s ease;
    }
    .activity-item:hover {
        border-color: #d1d5db;
    }
    .activity-icon {
        font-size: 1.2em;
        margin-right: 10px;
        display: inline-block;
    }
    .activity-time {
        color: #9ca3af;
        font-size: 0.75em;
        float: right;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Metrics Row with compact spacing
    col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #1e40af;">
            <div class="metric-label">Total SKUs</div>
            <div class="metric-value">{len(inventory_data)}</div>
            <div class="metric-delta" style="background: #eff6ff; color: #1e40af;">Active Products</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #dc2626;">
            <div class="metric-label">Critical Stock</div>
            <div class="metric-value">{crit_stock}</div>
            <div class="metric-delta" style="background: #fef2f2; color: #991b1b;">Requires Attention</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #d97706;">
            <div class="metric-label">Low Stock</div>
            <div class="metric-value">{low_stock}</div>
            <div class="metric-delta" style="background: #fffbeb; color: #92400e;">Monitor Closely</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #059669;">
            <div class="metric-label">Active POs</div>
            <div class="metric-value">{active_pos}</div>
            <div class="metric-delta" style="background: #f0fdf4; color: #065f46;">In Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #4b5563;">
            <div class="metric-label">Total Value</div>
            <div class="metric-value" style="font-size: 1.6em;">${total_value:,.0f}</div>
            <div class="metric-delta" style="background: #f9fafb; color: #374151;">Inventory Worth</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Professional Health Score Card
    if health_data:
        health_score = health_data.get('health_score', 0)
        status = health_data.get('status', 'UNKNOWN')
        
        if status == "HEALTHY":
            health_bg = "#f0fdf4"
            health_border = "#059669"
            health_text = "#065f46"
            status_badge = "#d1fae5"
        elif status == "WARNING":
            health_bg = "#fffbeb"
            health_border = "#d97706"
            health_text = "#92400e"
            status_badge = "#fef3c7"
        else:
            health_bg = "#fef2f2"
            health_border = "#dc2626"
            health_text = "#991b1b"
            status_badge = "#fee2e2"
        
        st.markdown(f"""
        <div style="background: {health_bg}; border: 1px solid {health_border}; 
                    padding: 24px 32px; border-radius: 8px; margin-bottom: 24px;
                    border-left: 4px solid {health_border};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0 0 12px 0; font-size: 1em; font-weight: 600; color: #374151; 
                               text-transform: uppercase; letter-spacing: 0.5px;">Supply Chain Health Score</h3>
                    <div style="font-size: 3em; font-weight: 700; margin: 8px 0; color: {health_text}; line-height: 1;">
                        {health_score:.1f}<span style="font-size: 0.4em; color: #6b7280; font-weight: 400;">/100</span>
                    </div>
                    <div style="background: {status_badge}; padding: 5px 14px; border-radius: 6px; 
                                display: inline-block; font-weight: 600; font-size: 0.85em; color: {health_text}; margin-top: 10px;">
                        {status}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2.2em; font-weight: 700; margin-bottom: 6px; color: #111827;">{health_data.get('critical_items_count', 0)}</div>
                    <div style="color: #6b7280; font-size: 0.85em; font-weight: 500;">Critical Items</div>
                    <div style="font-size: 2.2em; font-weight: 700; margin: 16px 0 6px 0; color: #111827;">{health_data.get('pending_pos', 0)}</div>
                    <div style="color: #6b7280; font-size: 0.85em; font-weight: 500;">Pending POs</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Main Content Layout with compact spacing
    col_chart, col_activity = st.columns([2.5, 1], gap="medium")
    
    with col_chart:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e5e7eb; padding: 20px 24px; 
                    border-radius: 8px; margin-bottom: 16px;">
            <h2 style="margin: 0 0 16px 0; color: #111827; font-size: 1.1em; font-weight: 600; 
                       text-transform: uppercase; letter-spacing: 0.5px;">Inventory Health Overview</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if inventory_data:
            df_inv = pd.DataFrame(inventory_data)
            if not df_inv.empty:
                # Enhanced bar chart
                fig = go.Figure()
                
                # Professional colors based on status
                colors = []
                for status in df_inv.get('status', []):
                    if status == 'CRITICAL':
                        colors.append('#dc2626')
                    elif status == 'LOW':
                        colors.append('#d97706')
                    else:
                        colors.append('#059669')
                
                fig.add_trace(go.Bar(
                    x=df_inv['product'],
                    y=df_inv['on_hand'],
                    marker_color=colors,
                    text=df_inv['on_hand'],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Stock: %{y}<extra></extra>'
                ))
                
                fig.update_layout(
                    height=340,
                    plot_bgcolor='#ffffff',
                    paper_bgcolor='#ffffff',
                    xaxis_title="Products",
                    yaxis_title="Stock Units",
                    showlegend=False,
                    margin=dict(l=50, r=20, t=20, b=70),
                    xaxis=dict(
                        tickangle=-45,
                        gridcolor='#f3f4f6',
                        title_font=dict(size=11, color='#374151'),
                        tickfont=dict(size=9, color='#6b7280')
                    ),
                    yaxis=dict(
                        gridcolor='#f3f4f6',
                        title_font=dict(size=11, color='#374151'),
                        tickfont=dict(size=9, color='#6b7280')
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Status Summary with compact spacing
                status_counts = df_inv['status'].value_counts().to_dict()
                status_col1, status_col2, status_col3 = st.columns(3, gap="medium")
                
                with status_col1:
                    st.metric("Healthy", status_counts.get('OK', 0), delta="Optimal")
                with status_col2:
                    st.metric("Low Stock", status_counts.get('LOW', 0), delta="Review Needed", delta_color="inverse")
                with status_col3:
                    st.metric("Critical", status_counts.get('CRITICAL', 0), delta="Action Required", delta_color="inverse")
        else:
            st.info("📦 No inventory data available")
    
    with col_activity:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e5e7eb; padding: 20px 18px; 
                    border-radius: 8px; margin-bottom: 16px;">
            <h2 style="margin: 0 0 16px 0; color: #111827; font-size: 1.1em; font-weight: 600; 
                       text-transform: uppercase; letter-spacing: 0.5px;">Recent Activity</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Collect all recent activities
        activities = []
        
        # Recent Orders
        if orders_data:
            for order in orders_data[:5]:
                order_time = order.get('created_at', '')
                if isinstance(order_time, str):
                    try:
                        order_dt = datetime.fromisoformat(order_time.replace('Z', '+00:00'))
                        time_ago = (datetime.now(order_dt.tzinfo) - order_dt).total_seconds() / 60  # minutes
                    except:
                        time_ago = 0
                else:
                    time_ago = 0
                
                activities.append({
                    'type': 'order',
                    'icon': '📦',
                    'title': f"New Order from {order.get('customer_name', 'Unknown')}",
                    'description': f"Status: {order.get('status', 'PENDING')}",
                    'time': f"{int(time_ago)}m ago" if time_ago < 60 else f"{int(time_ago/60)}h ago",
                    'color': '#1e40af'
                })
        
        # Recent Purchase Orders
        if pos_data:
            for po in sorted(pos_data, key=lambda x: x.get('created_at', ''), reverse=True)[:5]:
                po_time = po.get('created_at', '')
                if isinstance(po_time, str):
                    try:
                        po_dt = datetime.strptime(po_time, '%Y-%m-%d') if '-' in po_time else datetime.now()
                        time_ago = (datetime.now() - po_dt).total_seconds() / 3600  # hours
                    except:
                        time_ago = 0
                else:
                    time_ago = 0
                
                status_emoji = {
                    'DRAFT': '📝',
                    'APPROVED': '✅',
                    'IN_TRANSIT': '🚚',
                    'RECEIVED': '📦'
                }.get(po.get('status', 'DRAFT'), '📋')
                
                activities.append({
                    'type': 'po',
                    'icon': status_emoji,
                    'title': f"{po.get('po_number', 'PO')} - {po.get('product_name', 'Product')}",
                    'description': f"Qty: {po.get('quantity', 0)} • ${po.get('total_value', 0):,.2f}",
                    'time': f"{int(time_ago)}h ago" if time_ago < 24 else f"{int(time_ago/24)}d ago",
                    'color': '#059669' if po.get('status') == 'RECEIVED' else '#d97706'
                })
        
        # Critical Inventory Alerts
        if inventory_data:
            critical_items = [x for x in inventory_data if x.get('status') == 'CRITICAL'][:3]
            for item in critical_items:
                activities.append({
                    'type': 'alert',
                    'icon': '🚨',
                    'title': f"Critical: {item.get('product', 'Unknown')}",
                    'description': f"Stock: {item.get('on_hand', 0)}/{item.get('optimal_stock', 0)}",
                    'time': 'Now',
                    'color': '#dc2626'
                })
        
        # Sort activities by time (most recent first)
        activities.sort(key=lambda x: x['time'])
        activities = activities[:10]  # Show latest 10 activities
        
        if activities:
            for activity in activities:
                st.markdown(f"""
                <div class="activity-item" style="border-left-color: {activity['color']};">
                    <div style="display: flex; align-items: flex-start;">
                        <span class="activity-icon">{activity['icon']}</span>
                        <div style="flex: 1; min-width: 0;">
                            <div style="font-weight: 600; color: #111827; margin-bottom: 4px; font-size: 0.85em; line-height: 1.3;">
                                {activity['title']}
                            </div>
                            <div style="color: #6b7280; font-size: 0.8em; line-height: 1.4;">
                                {activity['description']}
                            </div>
                        </div>
                        <span class="activity-time">{activity['time']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 30px 20px; color: #9ca3af; border: 1px dashed #e5e7eb; border-radius: 8px;">
                <div style="font-size: 2em; margin-bottom: 8px; opacity: 0.5;">📭</div>
                <div style="font-size: 0.85em; font-weight: 500;">No recent activity</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Professional Quick Stats Row with compact spacing
    col_stat1, col_stat2, col_stat3 = st.columns(3, gap="medium")
    
    with col_stat1:
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid #1e40af; 
                    padding: 18px 20px; border-radius: 8px;">
            <div style="font-size: 1.8em; font-weight: 700; margin-bottom: 6px; color: #111827;">{len(orders_data)}</div>
            <div style="font-size: 0.8em; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Total Orders</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat2:
        avg_stock = sum([x.get('on_hand', 0) for x in inventory_data]) / len(inventory_data) if inventory_data else 0
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid #059669; 
                    padding: 18px 20px; border-radius: 8px;">
            <div style="font-size: 1.8em; font-weight: 700; margin-bottom: 6px; color: #111827;">{avg_stock:,.0f}</div>
            <div style="font-size: 0.8em; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Avg Stock per SKU</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_stat3:
        completed_pos = len([x for x in pos_data if x.get('status') == 'RECEIVED'])
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid #4b5563; 
                    padding: 18px 20px; border-radius: 8px;">
            <div style="font-size: 1.8em; font-weight: 700; margin-bottom: 6px; color: #111827;">{completed_pos}</div>
            <div style="font-size: 0.8em; color: #6b7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Completed POs</div>
        </div>
        """, unsafe_allow_html=True)

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
                            else:
                                    error_detail = res.json().get('detail', res.text)
                                    st.error(f"❌ AI Processing Failed: {error_detail}")
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
                price = c_b.number_input("Unit Price ($)", min_value=0.01, value=float(d['price']), step=0.1)
                
                optimal = max(1, stock if stock > 0 else 100) 
                optimal = max(1, int(max(optimal, round(optimal * 1.2))))
                safety = max(1, int(round(optimal * 0.2)))
                
                optimal = c_a.number_input("Optimal Stock", min_value=1, value=optimal)
                safety = c_b.number_input("Safety Stock", min_value=1, value=safety)
                
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
            if st.button("➕ Add Product", type="primary", use_container_width=True): add_form()
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
        st.info("📦 No products found in the database.")
        st.write("Click below to add your first product to the inventory.")
        if st.button("➕ Add Your First Product", type="primary"): 
            add_form()
# ==========================================
# DEMAND FORECASTING HELPER FUNCTIONS & SETUP
# ==========================================

STORAGE_FILE = "forecast_history.json"

def load_forecast_history():
    """Load forecast history from JSON file."""
    try:
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading forecast history: {e}")
        return []

def save_forecast_history(history):
    """Save forecast history to JSON file."""
    try:
        with open(STORAGE_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving forecast history: {e}")
        return False
    
def initialize_storage():
    """Initialize storage on app load."""
    if not st.session_state.storage_initialized:
        try:
            # Load existing history from file
            history = load_forecast_history()
            if history:
                st.session_state.forecast_history = history
            st.session_state.storage_initialized = True
        except Exception as e:
            print(f"Storage initialization error: {e}")
            st.session_state.storage_initialized = True

# Initialize storage when app loads
initialize_storage()

# --- ENHANCED CSS FOR FORECASTING ---
st.markdown("""
<style>
    .stApp {
        background-color: #f4f6f9;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a237e;
        margin-bottom: 0.5rem;
    }
    
    .card-box {
        background: white;
        padding: 16px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        margin-bottom: 15px;
    }
    
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-left: 3.5rem !important;
        padding-right: 3.5rem !important;
    }
    
    h1 {
        color: #1a237e !important;
        font-weight: 700;
    }

    .insight-box {
        background: linear-gradient(135deg, #e8f4fd 0%, #e0f2f1 100%);
        border-left: 4px solid #2196f3;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
            
    .insight-title {
        color: #1565c0;
        font-weight: bold;
        font-size: 1.1em;
        margin-bottom: 10px;
    }
    
    .insight-text {
        color: #0d47a1;
        font-size: 1.05em;
        line-height: 1.6;
    }
    
    .empty-state-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 70vh;
        text-align: center;
        padding: 40px 20px;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 24px;
        opacity: 0.3;
    }
    
    .empty-state-heading {
        font-size: 1.75rem;
        font-weight: 600;
        color: #1a237e;
        margin-bottom: 12px;
    }
    
    .empty-state-description {
        font-size: 1.05rem;
        color: #666;
        max-width: 480px;
        margin-bottom: 32px;
        line-height: 1.5;
    }
    
    .forecast-drivers-container {
        background: white;
        padding: 26px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-top: 28px;
        margin-bottom: 28px;
    }
    
    .drivers-header {
        font-size: 1.55rem;
        font-weight: 700;
        color: #1a237e;
        margin-bottom: 10px;
    }
    
    .drivers-subtitle {
        font-size: 0.96rem;
        color: #666;
        margin-bottom: 22px;
    }
    
    .driver-card {
        background: #fafafa;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        transition: all 0.2s ease;
    }
    
    .driver-card:hover {
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transform: translateX(2px);
    }
    
    .driver-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 12px;
        flex-shrink: 0;
    }
    
    .indicator-positive {
        background: #4caf50;
        box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
    }
    
    .indicator-negative {
        background: #f44336;
        box-shadow: 0 0 8px rgba(244, 67, 54, 0.4);
    }
    
    .indicator-neutral {
        background: #ff9800;
        box-shadow: 0 0 8px rgba(255, 152, 0, 0.4);
    }
    
    .indicator-none {
        background: #9e9e9e;
    }
    
    .driver-content {
        flex: 1;
    }
    
    .driver-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1a237e;
        margin-bottom: 2px;
    }
    
    .driver-description {
        font-size: 0.85rem;
        color: #666;
        line-height: 1.4;
    }
    
    .seasonal-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
        border-left: 4px solid #9c27b0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        transition: all 0.2s ease;
    }
    
    .seasonal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .seasonal-name {
        font-size: 0.98rem;
        font-weight: 600;
        color: #1a237e;
        flex: 1;
    }
    
    .seasonal-impact {
        font-size: 0.92rem;
        font-weight: 700;
        color: #7b1fa2;
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        padding: 4px 12px;
        border-radius: 14px;
        white-space: nowrap;
        margin-left: 12px;
    }
    
    .seasonal-period {
        font-size: 0.86rem;
        color: #666;
        display: flex;
        align-items: center;
        gap: 6px;
    }
            
    .seasonal-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transform: translateX(2px);
    }
    
    .no-factors-message {
        text-align: center;
        padding: 32px 24px;
        color: #999;
        font-size: 0.95rem;
        background: #fafafa;
        border-radius: 10px;
        border: 1px dashed #ddd;
    }
    
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a237e;
        margin: 0;
    }
    
    .section-subtitle {
        font-size: 0.95rem;
        color: #666;
        margin-top: 6px;
        margin-left: 48px;
    }
            
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        background: white;
        padding: 18px 24px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        margin-top: 24px;
    }
    
    .section-icon {
        font-size: 1.8rem;
        line-height: 1;
    }
            
    .column-title {
        font-size: 1.12rem;
        font-weight: 600;
        color: #1a237e;
        margin-bottom: 18px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e0e0e0;
    }
    
    .stButton>button {
        background-color: #2563eb !important;   
        color: #ffffff !important;              
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 0.55rem 1.4rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }

    .stButton>button:hover {
        background-color: #1e40af !important;  
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        cursor: pointer;
    }

    .stButton>button:active {
        background-color: #1e3a8a !important; 
        transform: translateY(1px);
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.25);
    }
            
    div[data-testid="stFileUploader"] button {
        background-color: #2563eb !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.55rem 1.4rem !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
        cursor: pointer;
    }

    div[data-testid="stFileUploader"] button:hover {
        background-color: #1e40af !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

</style>
""", unsafe_allow_html=True)


def find_col(keywords: list, columns: list) -> str:
    """Auto-detect column based on keywords."""
    for col in columns:
        if any(keyword in col.lower() for keyword in keywords):
            return col
    return columns[0] if columns else None


def create_forecast_chart(history_data: list, forecast_data: list, category: str):
    """Generate Plotly chart with historical data, forecast, and confidence interval."""
    history_df = pd.DataFrame(history_data)
    forecast_df = pd.DataFrame(forecast_data)
    
    history_df["Date"] = pd.to_datetime(history_df["Date"])
    forecast_df["Date"] = pd.to_datetime(forecast_df["Date"])
    
    fig = go.Figure()
    
    # Confidence Interval
    if "Upper_Bound" in forecast_df.columns and "Lower_Bound" in forecast_df.columns:
        fig.add_trace(go.Scatter(
            name='Upper Bound',
            x=forecast_df["Date"],
            y=forecast_df["Upper_Bound"],
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            name='Confidence Interval',
            x=forecast_df["Date"],
            y=forecast_df["Lower_Bound"],
            mode='lines',
            fill='tonexty',
            fillcolor='rgba(41, 98, 255, 0.2)',
            line=dict(width=0)
        ))
    
    # Historical Data
    fig.add_trace(go.Scatter(
        x=history_df['Date'],
        y=history_df['Actual_Units'],
        mode='lines+markers',
        name='Historical Sales',
        line=dict(color='#00C853', width=3),
        marker=dict(size=6)
    ))
    
    # Forecasted Data
    fig.add_trace(go.Scatter(
        x=forecast_df['Date'],
        y=forecast_df['Forecasted_Units'],
        mode='lines+markers',
        name='AI Forecast',
        line=dict(color='#2962FF', width=3, dash='dot'),
        marker=dict(size=10, symbol='diamond')
    ))
    
    # Connect last historical to first forecast
    if not history_df.empty and not forecast_df.empty:
        fig.add_trace(go.Scatter(
            x=[history_df['Date'].iloc[-1], forecast_df['Date'].iloc[0]],
            y=[history_df['Actual_Units'].iloc[-1], forecast_df['Forecasted_Units'].iloc[0]],
            mode='lines',
            line=dict(color='#9e9e9e', width=2, dash='dash'),
            showlegend=False
        ))

    fig.update_layout(
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title=dict(
            text=f'📊 Demand Forecast: {category}',
            font=dict(size=20)
        ),
        xaxis_title="Date (Monthly)",
        yaxis_title="Units Sold",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)'
        )
    )
    
    return fig


def get_impact_class(factor_name: str, external_factors: dict) -> str:
    """Determine impact indicator color based on factor type."""
    positive_factors = ["upcoming_promotion", "marketing_campaign"]
    if factor_name in positive_factors:
        return "indicator-positive"
    
    negative_factors = [
        "supply_chain_disruption", 
        "availability_issues", 
        "logistics_constraints",
        "regulatory_changes"
    ]
    if factor_name in negative_factors:
        return "indicator-negative"
    
    neutral_factors = ["new_product_launch", "economic_uncertainty"]
    if factor_name in neutral_factors:
        if factor_name == "new_product_launch":
            return "indicator-neutral"
        if factor_name == "economic_uncertainty":
            uncertainty_level = external_factors.get("economic_uncertainty", "None")
            if uncertainty_level in ["Medium", "High"]:
                return "indicator-negative"
            return "indicator-neutral"
    
    if factor_name == "price_change":
        price_direction = external_factors.get("price_change", "Same")
        if price_direction == "Decrease":
            return "indicator-positive"
        elif price_direction == "Increase":
            return "indicator-negative"
    
    return "indicator-none"


def get_factor_description(factor_name: str, external_factors: dict) -> str:
    """Get human-readable description for each factor."""
    descriptions = {
        "upcoming_promotion": "Promotional campaign expected to boost demand through price incentives",
        "marketing_campaign": "Active marketing initiatives expanding brand awareness and consideration",
        "new_product_launch": "New SKU introduction - may expand category or cannibalize existing products",
        "availability_issues": "Inventory constraints may limit ability to meet demand",
        "supply_chain_disruption": "Supply chain constraints may cap fulfillment capacity",
        "logistics_constraints": "Transportation limitations may delay product availability",
        "regulatory_changes": "Compliance requirements may impact product availability or pricing",
        "economic_uncertainty": f"{external_factors.get('economic_uncertainty', 'Low')} economic volatility affecting consumer spending patterns",
        "price_change": f"Price {external_factors.get('price_change', 'Same').lower()} may influence purchase decisions"
    }
    
    return descriptions.get(factor_name, "Market condition affecting demand")


def render_forecast_drivers(external_factors: dict, festivals: list, seasonality: dict, data_months: int):
    """Render the Forecast Drivers section with external and seasonal factors."""
    
    st.markdown("""
    <div class="forecast-drivers-container">
        <div class="drivers-header">📊 Forecast Drivers</div>
        <div class="drivers-subtitle">This forecast is influenced by external conditions and seasonal demand patterns.</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_external, col_seasonal = st.columns(2)
    
    # === LEFT COLUMN: External Factors ===
    with col_external:
        st.markdown('<div class="column-title">🌍 External Factors Impact</div>', unsafe_allow_html=True)
        
        active_factors = []
        
        if external_factors:
            factor_mapping = {
                "upcoming_promotion": "Promotional Campaign",
                "marketing_campaign": "Marketing Initiative",
                "new_product_launch": "New Product Launch",
                "availability_issues": "Inventory Constraints",
                "price_change": "Price Adjustment",
                "supply_chain_disruption": "Supply Chain Risk",
                "logistics_constraints": "Logistics Limitation",
                "regulatory_changes": "Regulatory Changes",
                "economic_uncertainty": "Economic Uncertainty"
            }
            
            for key, display_name in factor_mapping.items():
                if key == "price_change":
                    if external_factors.get(key) and external_factors.get(key) != "Same":
                        active_factors.append({
                            "name": f"{display_name} ({external_factors.get(key)})",
                            "key": key,
                            "description": get_factor_description(key, external_factors)
                        })
                elif key == "economic_uncertainty":
                    if external_factors.get(key) and external_factors.get(key) != "None":
                        active_factors.append({
                            "name": f"{display_name} ({external_factors.get(key)})",
                            "key": key,
                            "description": get_factor_description(key, external_factors)
                        })
                else:
                    if external_factors.get(key):
                        active_factors.append({
                            "name": display_name,
                            "key": key,
                            "description": get_factor_description(key, external_factors)
                        })
        
        if active_factors:
            for factor in active_factors:
                impact_class = get_impact_class(factor["key"], external_factors)
                st.markdown(f"""
                <div class="driver-card">
                    <div class="driver-indicator {impact_class}"></div>
                    <div class="driver-content">
                        <div class="driver-name">{factor["name"]}</div>
                        <div class="driver-description">{factor["description"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="no-factors-message">
                No external factors specified.<br>
                Forecast is based on historical patterns only.
            </div>
            """, unsafe_allow_html=True)
    
    # === RIGHT COLUMN: Seasonal Factors ===
    with col_seasonal:
        st.markdown('<div class="column-title">🗓️ Seasonal Factors Impact</div>', unsafe_allow_html=True)
        
        seasonal_items = []
        
        if data_months >= 24 and seasonality:
            yearly_strength = seasonality.get("yearly_seasonality_strength", 0)
            
            if yearly_strength > 15:
                seasonal_items.append({
                    "name": "Yearly Seasonal Pattern",
                    "period": "Throughout the year",
                    "impact": f"{yearly_strength:.0f}% variance",
                    "impact_value": yearly_strength
                })
        
        if seasonal_items:
            for item in seasonal_items:
                st.markdown(f"""
                <div class="seasonal-card">
                    <div class="seasonal-header">
                        <div class="seasonal-name">{item["name"]}</div>
                        <div class="seasonal-impact">{item["impact"]}</div>
                    </div>
                    <div class="seasonal-period">📅 {item["period"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            if data_months < 24:
                st.markdown(f"""
                <div class="no-factors-message">
                    <strong>No significant seasonal impact detected.</strong><br><br>
                    Limited historical data available ({data_months} months). At least 24 months of historical data are required to reliably identify seasonal patterns and calculate their impact on demand.<br><br>
                    As more data becomes available, seasonal trends will be automatically detected and displayed here.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="no-factors-message">
                    No significant seasonal patterns detected for the selected period.<br><br>
                    Demand appears relatively stable throughout the year.
                </div>
                """, unsafe_allow_html=True)


def render_festivals_awareness(festivals: list):
    """Render festivals as contextual awareness only."""
    
    if not festivals or len(festivals) == 0:
        return
    
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">📅</div>
        <div>
            <div class="section-title">Upcoming Festivals & Holidays</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div style="margin-top: 16px;"></div>', unsafe_allow_html=True)
    
    for festival in festivals[:4]:
        if '(' in festival:
            festival_name = festival.split('(')[0].strip()
            festival_date = festival.split('(')[1].replace(')', '').strip()
        else:
            festival_name = festival
            festival_date = "Date TBD"
        
        st.markdown(f"""
        <div style="background: white; padding: 14px 18px; border-radius: 10px; margin-bottom: 10px; 
                    border-left: 4px solid #9c27b0; box-shadow: 0 2px 6px rgba(0,0,0,0.06);">
            <div style="font-size: 1rem; font-weight: 600; color: #1a237e; margin-bottom: 6px;">
                {festival_name}
            </div>
            <div style="font-size: 0.88rem; color: #666; display: flex; align-items: center; gap: 6px;">
                📅 {festival_date}
            </div>
        </div>
        """, unsafe_allow_html=True)

   # ============================================
# PAGE 1: MAIN PAGE (AI DEMAND FORECASTING)
# ============================================

def render_main_page():
    """Main landing page showing latest forecast or empty state."""
    
    st.title("📈 AI Demand Forecasting")
    st.caption("Powered by advanced time-series AI with contextual market analysis")
    
    # Auto-load latest forecast if history exists and no current forecast is displayed
    if not st.session_state.forecast_result and st.session_state.forecast_history:
        latest_forecast = st.session_state.forecast_history[-1]  # Get the most recent
        st.session_state.forecast_result = latest_forecast['result']
        st.session_state.selected_category = latest_forecast['category']
        st.session_state.selected_external_factors = latest_forecast.get('external_factors', {})
    
    # Show forecast if exists
    if st.session_state.forecast_result:
        res = st.session_state.forecast_result
        category = st.session_state.get('selected_category', 'Product')
        
        # AI Insight Box
        insight = res.get('ai_insight', 'AI analysis pending...')
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">✨ AI Insight: {category}</div>
            <div class="insight-text">{insight}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Main layout
        col_chart, col_info = st.columns([3, 1])
        
        with col_chart:
            st.markdown("""
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div>
                    <div class="section-title">Forecast Results</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Metrics Row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            col_m1.metric(
                label="🎯 Forecasted Units",
                value=f"{res['forecasted_units']:,}",
                delta=f"{res['mom_change_percent']:+.1f}% MoM" if res.get('mom_change_percent') else None,
                delta_color="normal" if res.get('mom_change_percent', 0) >= 0 else "inverse"
            )
            
            col_m2.metric(label="📈 Trend", value=res["trend"], delta=f"{res['confidence']} Confidence", delta_color="off")
            col_m3.metric(label="📅 Historical Data", value=f"{res['data_months']} months", delta="✓ Sufficient" if res['data_months'] >= 12 else "⚠ Limited", delta_color="off")
            col_m4.metric(label="📊 Confidence Range", value=f"{res.get('lower_bound', 0):,} - {res.get('upper_bound', 0):,}", delta="95% interval", delta_color="off")
            
            st.write("")
            
            # Chart
            fig = create_forecast_chart(res["history_data"], res["forecast_data"], category)
            st.plotly_chart(fig, use_container_width=True)
            
            # Forecast Drivers
            render_forecast_drivers(
                external_factors=st.session_state.get('selected_external_factors', {}),
                festivals=res.get('festivals', []),
                seasonality=res.get('seasonality', {}),
                data_months=res.get('data_months', 0)
            )
            
            # Festivals Awareness
            render_festivals_awareness(festivals=res.get('festivals', []))
            
            # Navigation buttons below festivals - not full width
            st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🚀 Generate New Forecast", key="gen_new_main"):
                    st.session_state.current_page = "generate"
                    st.rerun()
            with col_btn2:
                if st.button("📄 Export Report", key="export_main"):
                    st.info("Export functionality coming soon!")
        
        with col_info:
            st.markdown("""
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div>
                    <div class="section-title">Data Quality</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            data_summary = res.get("data_summary", {})
            
            if data_summary:
                st.markdown(f"**Date Range:**")
                st.markdown(f"{data_summary.get('date_range_start', 'N/A')}")
                st.markdown(f"to {data_summary.get('date_range_end', 'N/A')}")
                st.write("")
                st.markdown(f"**Avg Monthly:** {data_summary.get('avg_monthly_units', 0):,.0f} units")
                st.markdown(f"**Total Units:** {data_summary.get('total_units', 0):,}")
            
            st.markdown("---")
            
            # Forecast History Section
            st.markdown("""
            <div class="section-header" style="margin-top: 20px;">
                <div class="section-icon">📚</div>
                <div>
                    <div class="section-title" style="font-size: 1.3rem;">Forecast History</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.forecast_history:
                # Get unique values for filters
                all_categories = list(set([f['category'] for f in st.session_state.forecast_history]))
                all_horizons = list(set([f['horizon'] for f in st.session_state.forecast_history]))
                all_data_months = list(set([f['data_months'] for f in st.session_state.forecast_history]))
                
                all_categories.sort()
                all_horizons.sort()
                all_data_months.sort()
                
                # Filters
                st.markdown("**Filters:**")
                filter_category = st.selectbox(
                    "Category",
                    ["All"] + all_categories,
                    key="filter_category"
                )
                
                filter_horizon = st.selectbox(
                    "Horizon",
                    ["All"] + [f"{h} month{'s' if h > 1 else ''}" for h in all_horizons],
                    key="filter_horizon"
                )
                
                filter_data_months = st.selectbox(
                    "Data Months",
                    ["All"] + [f"{m} months" for m in all_data_months],
                    key="filter_data_months"
                )
                
                # Apply filters
                filtered_forecasts = st.session_state.forecast_history.copy()
                
                if filter_category != "All":
                    filtered_forecasts = [f for f in filtered_forecasts if f['category'] == filter_category]
                
                if filter_horizon != "All":
                    horizon_value = int(filter_horizon.split()[0])
                    filtered_forecasts = [f for f in filtered_forecasts if f['horizon'] == horizon_value]
                
                if filter_data_months != "All":
                    data_months_value = int(filter_data_months.split()[0])
                    filtered_forecasts = [f for f in filtered_forecasts if f['data_months'] == data_months_value]
                
                st.write("")
                
                if filtered_forecasts:
                    st.markdown(f"**Found {len(filtered_forecasts)} forecast{'s' if len(filtered_forecasts) > 1 else ''}:**")
                    st.write("")
                    
                    # Display filtered forecasts
                    for idx, forecast in enumerate(reversed(filtered_forecasts)):  # Most recent first
                        with st.container():
                            st.markdown('<div class="card-box">', unsafe_allow_html=True)
                            st.markdown(f"**{forecast['category']}**")
                            st.caption(f"Generated: {forecast['timestamp']}")
                            st.caption(f"Horizon: {forecast['horizon']} month{'s' if forecast['horizon'] > 1 else ''} | Data: {forecast['data_months']} months")
                            st.caption(f"Forecast: {forecast['forecasted_units']:,} units")
                            
                            if st.button("📊 Show", key=f"show_forecast_{idx}", use_container_width=True):
                                st.session_state.forecast_result = forecast['result']
                                st.session_state.selected_category = forecast['category']
                                st.session_state.selected_external_factors = forecast.get('external_factors', {})
                                st.rerun()
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.write("")
                else:
                    st.info("No forecasts match the selected filters.")
            else:
                st.info("No forecast history yet. Generate your first forecast!")
    
    else:
        # Empty state
        st.markdown("""
            <div class="empty-state-container">
                <div class="empty-state-icon">📊</div>
                <div class="empty-state-heading">No forecasts yet</div>
                <div class="empty-state-description">
                    Click "Generate New Forecast" below to create your first AI-powered demand forecast.
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Show buttons in empty state too
        col_empty1, col_empty2, col_empty3 = st.columns([1, 1, 1])
        with col_empty2:
            if st.button("🚀 Generate New Forecast", use_container_width=True, key="gen_new_empty"):
                st.session_state.current_page = "generate"
                st.rerun()
    
    # Footer
    st.divider()
    st.caption("🚀 Expedition Co. | AI-Powered Supply Chain Management | Demand Forecasting Module v1.0")


# ============================================
# PAGE 2: GENERATE FORECAST PAGE
# ============================================

def render_generate_page():
    """Page for uploading data and generating forecasts."""
    
    st.title("📈 Generate Demand Forecast")
    st.caption("Turn historical sales data into accurate demand forecasts")
    
    # Back button
    if st.button("← Back to Main Page"):
        st.session_state.current_page = "main"
        st.rerun()
    
    st.divider()
    
    col_upload, col_info = st.columns([3, 1])
    
    with col_upload:
        # Data Upload Section
        st.markdown("""
        <div class="section-header">
            <div class="section-icon">📂</div>
            <div>
                <div class="section-title">Data Upload & Column Mapping</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload Sales Data (CSV)",
            type="csv",
            help="Upload a CSV file containing your historical sales data",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, dtype=str)
            cols = df.columns.tolist()
            
            with st.expander("👀 Preview Uploaded Data", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"Total rows: {len(df)} | Columns: {len(cols)}")
            
            # Column Mapping
            with st.expander("⚙️ Column Mapping (Configure your file)", expanded=True):
                st.info("Map your CSV columns to the required fields")
                
                c1, c2, c3 = st.columns(3)
                
                default_date = find_col(['date', 'time', 'period', 'day', 'ts'], cols)
                default_cat = find_col(['cat', 'prod', 'type', 'item', 'store', 'sku', 'product'], cols)
                default_units = find_col(['unit', 'qty', 'sold', 'number', 'sales', 'amount', 'quantity'], cols)
                
                date_col = c1.selectbox("📅 Date Column", cols, index=cols.index(default_date) if default_date in cols else 0)
                category_col = c2.selectbox("📦 Category/Product Column", cols, index=cols.index(default_cat) if default_cat in cols else 0)
                units_col = c3.selectbox("🔢 Units Sold Column", cols, index=cols.index(default_units) if default_units in cols else 0)
            
            st.divider()
            
            # Product/Category Selection
            st.markdown("""
            <div class="section-header">
                <div class="section-icon">📦</div>
                <div>
                    <div class="section-title">Select Product / Category</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if category_col and category_col in df.columns:
                unique_cats = df[category_col].dropna().unique().tolist()
                try:
                    unique_cats.sort()
                except TypeError:
                    pass
                
                sel_cat = st.selectbox(
                    "Select Product/Category to Forecast", 
                    unique_cats, 
                    key="sel_cat", 
                    label_visibility="collapsed"
                )
            else:
                st.error("❌ Category column not found or selected.")
                sel_cat = None
            
            # Validate button
            if sel_cat and st.button("🔍 Validate Data"):
                with st.spinner("Validating data..."):
                    temp_df = df.rename(columns={date_col: "Date", category_col: "Category", units_col: "Units_Sold"})
                    
                    buffer = io.StringIO()
                    temp_df.to_csv(buffer, index=False)
                    buffer.seek(0)
                    
                    files = {"file": ("data.csv", buffer.getvalue(), "text/csv")}
                    data = {"category": str(sel_cat), "date_col": "Date", "category_col": "Category", "units_col": "Units_Sold"}
                    
                    try:
                        response = requests.post(f"{API_URL}/validate-data", files=files, data=data, timeout=30)
                        
                        if response.status_code == 200:
                            st.session_state['validation_result'] = response.json()
                            st.success("✅ Data validated successfully!")
                            st.rerun()
                        else:
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"❌ Validation Failed: {error_detail}")
                            
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to backend server")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            # Forecast Configuration
            if st.session_state.get('validation_result'):
                validation = st.session_state['validation_result']
                st.markdown("""
                <div class="section-header">
                    <div class="section-icon">⚙️</div>
                    <div>
                        <div class="section-title">Forecast Configuration</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Region & Forecast Period
                col_region, col_horizon = st.columns(2)
                
                with col_region:
                    region = st.selectbox(
                        "🌍 Region",
                        list(COUNTRY_MAP.keys()),
                        index=0,
                        help="Select your target market region"
                    )
                    country_code = COUNTRY_MAP[region]
                
                with col_horizon:
                    available_horizons = validation.get('available_horizons', [])
                    if not available_horizons:
                        st.error("❌ No forecast horizons available. Insufficient data.")
                        selected_horizon = None
                    else:
                        selected_horizon = st.radio(
                            "Forecast Period",
                            available_horizons,
                            format_func=lambda x: f"{x} Month{'s' if x > 1 else ''}",
                            horizontal=True
                        )
                
                if selected_horizon:
                    # --- FIX START: Use .get() to prevent KeyError ---
                    summary = validation.get('data_summary', {})
                    data_months = summary.get('num_months', 0)
                    # --- FIX END ---
                    
                    disabled_messages = []
                    # Check available_horizons safely
                    avail = validation.get('available_horizons', [])
                    
                    if 3 not in avail and data_months < 12:
                        disabled_messages.append(f"ℹ️ 3-month forecast requires 12+ months (you have {data_months})")
                    if 6 not in avail and data_months < 24:
                        disabled_messages.append(f"ℹ️ 6-month forecast requires 24+ months (you have {data_months})")
                    
                    if disabled_messages:
                        for msg in disabled_messages:
                            st.info(msg)
                    # External Factors Section
                    st.markdown("""
                    <div class="section-header">
                        <div class="section-icon">🌍</div>
                        <div>
                            <div class="section-title">External Factors (Optional)</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("**Business Factors**")
                    col_left, col_right = st.columns(2)
                    with col_left:
                        with st.container():
                            st.markdown('<div class="card-box">', unsafe_allow_html=True)
                            upcoming_promotion = st.checkbox("Upcoming Promotion", help="Planned promotional campaign or sale event")
                            marketing_campaign = st.checkbox("Marketing Campaign", help="Active marketing or advertising initiative")
                            new_product_launch = st.checkbox("New Product Launch", help="New product introduction scheduled")
                            availability_issues = st.checkbox("Availability Issues", help="Expected inventory or stock constraints")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                    with col_right:
                        with st.container():
                            st.markdown('<div class="card-box">', unsafe_allow_html=True)
                            price_change = st.selectbox("Price Change", ["Same", "Increase", "Decrease"], help="Planned pricing adjustments")
                            st.markdown('</div>', unsafe_allow_html=True)

                    st.markdown("**Risk Factors**")
                    col_left, col_right = st.columns(2)
                    with col_left:
                        with st.container():
                            st.markdown('<div class="card-box">', unsafe_allow_html=True)
                            supply_chain_disruption = st.checkbox("Supply Chain Disruption", help="Supply chain or sourcing risks")
                            regulatory_changes = st.checkbox("Regulatory Changes", help="Regulatory or compliance changes expected")
                            logistics_constraints = st.checkbox("Logistics Constraints", help="Transportation or delivery constraints")
                            st.markdown('</div>', unsafe_allow_html=True)

                    with col_right:
                        with st.container():
                            st.markdown('<div class="card-box">', unsafe_allow_html=True)
                            economic_uncertainty = st.selectbox("Economic Uncertainty", ["None", "Low", "Medium", "High"], help="Economic volatility level")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Generate Forecast Button
                    generate_clicked = st.button("🚀 Generate Forecast", use_container_width=True)
                    
                    if generate_clicked:
                        status_placeholder = st.empty()
                        status_placeholder.info(f"⏳ Preparing data for **{sel_cat}**...")
                        
                        temp_df = df.rename(columns={date_col: "Date", category_col: "Category", units_col: "Units_Sold"})
                        
                        buffer = io.StringIO()
                        temp_df.to_csv(buffer, index=False)
                        buffer.seek(0)
                        
                        files = {"file": ("data.csv", buffer.getvalue(), "text/csv")}
                        data = {
                            "category": str(sel_cat),
                            "date_col": "Date",
                            "category_col": "Category",
                            "units_col": "Units_Sold",
                            "horizon": selected_horizon,
                            "upcoming_promotion": str(upcoming_promotion).lower(),
                            "marketing_campaign": str(marketing_campaign).lower(),
                            "new_product_launch": str(new_product_launch).lower(),
                            "availability_issues": str(availability_issues).lower(),
                            "price_change": price_change,
                            "supply_chain_disruption": str(supply_chain_disruption).lower(),
                            "regulatory_changes": str(regulatory_changes).lower(),
                            "logistics_constraints": str(logistics_constraints).lower(),
                            "economic_uncertainty": economic_uncertainty,
                            "region": region,
                            "country": country_code
                        }
                        
                        # Store selected external factors
                        st.session_state['selected_external_factors'] = {
                            "upcoming_promotion": upcoming_promotion,
                            "marketing_campaign": marketing_campaign,
                            "new_product_launch": new_product_launch,
                            "availability_issues": availability_issues,
                            "price_change": price_change,
                            "supply_chain_disruption": supply_chain_disruption,
                            "regulatory_changes": regulatory_changes,
                            "logistics_constraints": logistics_constraints,
                            "economic_uncertainty": economic_uncertainty
                        }
                        
                        try:
                            status_placeholder.info("⚙️ Running AI model & generating insights...")
                            
                            api_response = requests.post(f"{API_URL}/forecast/upload", files=files, data=data, timeout=120)
                            
                            if api_response.status_code == 200:
                                result = api_response.json()
                                st.session_state['forecast_result'] = result
                                st.session_state['selected_category'] = sel_cat
                                
                                # Store in forecast history
                                forecast_entry = {
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'category': sel_cat,
                                    'horizon': selected_horizon,
                                    'data_months': result.get('data_months', 0),
                                    'forecasted_units': result.get('forecasted_units', 0),
                                    'result': result,
                                    'external_factors': st.session_state['selected_external_factors']
                                }
                                st.session_state['forecast_history'].append(forecast_entry)
                                
                                # Save to persistent storage (JSON file)
                                try:
                                    save_forecast_history(st.session_state['forecast_history'])
                                except Exception as e:
                                    print(f"Error saving to storage: {e}")
                                
                                status_placeholder.success("✅ Forecast generated successfully!")
                                
                                # Redirect to main page after 1 second
                                import time
                                time.sleep(1)
                                st.session_state.current_page = "main"
                                st.rerun()
                            else:
                                status_placeholder.empty()
                                error_detail = api_response.json().get("detail", "Unknown error")
                                st.error(f"❌ Forecast Failed: {error_detail}")
                                
                        except requests.exceptions.ConnectionError:
                            status_placeholder.empty()
                            st.error("❌ Cannot connect to backend server")
                        except Exception as e:
                            status_placeholder.empty()
                            st.error(f"❌ Error: {str(e)}")
    
    with col_info:
        if st.session_state.get('validation_result'):
            validation = st.session_state['validation_result']
            
            st.markdown("""
            <div class="section-header">
                <div class="section-icon">📊</div>
                <div>
                    <div class="section-title">Data Quality</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            data_summary = validation.get("data_summary", {})
            
            if data_summary:
                st.markdown(f"**Date Range:**")
                st.markdown(f"{data_summary.get('date_range_start', 'N/A')}")
                st.markdown(f"to {data_summary.get('date_range_end', 'N/A')}")
                st.write("")
                st.markdown(f"**Data Points:** {data_summary.get('num_months', 0)} months")
                st.markdown(f"**Avg Monthly:** {data_summary.get('avg_monthly_units', 0):,.0f} units")
                st.markdown(f"**Total Units:** {data_summary.get('total_units', 0):,}")
            
            st.markdown("---")
            
            if validation.get('ready_for_forecast'):
                st.success("✅ Ready for forecast")
            else:
                st.warning("⚠️ More data needed")
        
        else:
            st.markdown("""
            <div class="section-header">
                <div class="section-icon">💡</div>
                <div>
                    <div class="section-title">Tips</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            - Upload **6+ months** minimum
            - **12+ months** for seasonal patterns
            - **24+ months** for best accuracy
            - Ensure CSV has date, category, units columns
            """)
    
    # Footer
    st.divider()
    st.caption("🚀 Expedition Co. | AI-Powered Supply Chain Management | Demand Forecasting Module v1.0")

# Handle Demand Forecasting page routing (called after function definitions)
if page == "Demand Forecasting":
    # Determine which page to render
    if st.session_state.current_page == "main":
        render_main_page()
    elif st.session_state.current_page == "generate":
        render_generate_page()

# ==========================================
# PAGE 4: PROCUREMENT AGENT (MAIN PAGE)
# ==========================================
if page == "Procurement Agent":
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
                gradient = "linear-gradient(135deg, #1a98a6 0%, #8BC34A 100%)"
                status_emoji = "✅"
            elif status == "WARNING":
                gradient = "linear-gradient(135deg,  #1a98a6 0%, #FFC107 100%)"
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
<div class="supplier-card supplier-card-modern" style="margin-bottom: 24px; margin-right: 24px;">
  <div style="display:flex; justify-content:space-between; align-items:center; gap:30px;">
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
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
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

                                    # Sidebar edit form (global placement, cleaner UI)
                                    with st.sidebar:
                                        if st.session_state.get("selected_supplier_id") == s['id']:
                                            st.subheader("Edit Supplier")
                                            presets = st.session_state.get("edit_supplier_preset", {})
                                            with st.form(f"edit_form_sidebar_{s['id']}"):
                                                c1, c2 = st.columns(2)
                                                with c1:
                                                    new_email = st.text_input("Contact Email", value=str(presets.get('contact_email', '')))
                                                    new_category = st.text_input("Category", value=str(presets.get('category', '')))
                                                    new_price = st.number_input("Price per Unit ($)", min_value=0.0, value=float(presets.get('price_per_unit', 0.0)), step=0.1)
                                                with c2:
                                                    new_days = st.number_input("Delivery Speed (Days)", min_value=1, value=int(presets.get('delivery_speed_days', 5)))
                                                    new_reliability = st.slider("Reliability Score", 0, 100, int(presets.get('reliability_score', 95)))
                                                    new_delivery_cost = st.number_input("Delivery Cost ($)", min_value=0.0, value=float(presets.get('delivery_cost', 0.0)), step=0.1)
                                                save = st.form_submit_button("💾 Save Changes", type="primary")
                                                if save:
                                                    payload = {
                                                        "contact_email": new_email,
                                                        "category": new_category,
                                                        "price_per_unit": new_price,
                                                        "delivery_speed_days": new_days,
                                                        "reliability_score": new_reliability,
                                                        "delivery_cost": new_delivery_cost,
                                                    }
                                                    try:
                                                        upd_res = requests.put(f"{API_URL}/procurement/suppliers/{s['id']}", json=payload)
                                                        if upd_res.status_code == 200:
                                                            st.success("Supplier updated successfully")
                                                            # Clear selection after save
                                                            st.session_state["selected_supplier_id"] = None
                                                            st.session_state["selected_supplier_name"] = None
                                                            st.session_state["edit_supplier_preset"] = None
                                                        else:
                                                            st.error(upd_res.text)
                                                    except Exception as e:
                                                        st.error(f"Update error: {e}")

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

    # Manage existing suppliers (clean controls, moved from cards)
    st.subheader("Manage Existing Suppliers")
    try:
        sup_list_res = requests.get(f"{API_URL}/procurement/suppliers/analysis")
        if sup_list_res.status_code == 200:
            data = sup_list_res.json()
            suppliers = []
            if isinstance(data, list):
                suppliers = data
            elif isinstance(data, dict):
                suppliers = data.get('suppliers') or data.get('items') or data.get('data') or []
                if isinstance(suppliers, dict):
                    suppliers = suppliers.get('items', [])
            if suppliers:
                names = [f"{s.get('name', 'Unnamed')} • {s.get('category','N/A')}" for s in suppliers if isinstance(s, dict)]
                selected_idx = st.selectbox("Select supplier", options=list(range(len(suppliers))), format_func=lambda i: names[i] if i < len(names) else f"Supplier #{i}")
                selected = suppliers[selected_idx]

                supplier_id = selected.get('id') if isinstance(selected, dict) else None
                supplier_name = (selected.get('name') if isinstance(selected, dict) else None) or "Supplier"

                c1, c2, c3 = st.columns([1,1,2])
                with c1:
                    if st.button("✏️ Edit in Sidebar", type="primary"):
                        if supplier_id is None:
                            st.error("Missing supplier ID; cannot edit.")
                        else:
                            st.session_state["selected_supplier_id"] = supplier_id
                            st.session_state["selected_supplier_name"] = supplier_name
                            st.session_state["edit_supplier_preset"] = {
                                "contact_email": str(selected.get('contact_email', '')),
                                "category": str(selected.get('category', '')),
                                "price_per_unit": float(selected.get('price_per_unit', 0.0)),
                                "delivery_speed_days": int(selected.get('delivery_speed_days', 5)),
                                "reliability_score": int(selected.get('reliability_score', 95)),
                                "delivery_cost": float(selected.get('delivery_cost', 0.0)),
                            }
                            st.toast(f"Editing {supplier_name} in sidebar")
                with c2:
                    if st.button("🗑️ Delete", type="secondary"):
                        if supplier_id is None:
                            st.error("Missing supplier ID; cannot delete.")
                        else:
                            try:
                                del_res = requests.delete(f"{API_URL}/procurement/suppliers/{supplier_id}")
                                if del_res.status_code == 200:
                                    st.success(f"Deleted supplier '{supplier_name}'")
                                else:
                                    err = del_res.json().get('detail', del_res.text)
                                    st.error(f"Delete failed: {err}")
                            except Exception as e:
                                st.error(f"Delete error: {e}")
                with c3:
                    if st.button("🧠 AI Negotiation Email", type="secondary"):
                        if supplier_id is None:
                            st.error("Missing supplier ID; cannot generate.")
                        else:
                            try:
                                gen_res = requests.post(f"{API_URL}/procurement/suppliers/{supplier_id}/negotiation_email")
                                if gen_res.status_code == 200:
                                    email = gen_res.json().get('email', '')
                                    safe_name = supplier_name.replace(' ', '_')
                                    with st.expander(f"AI Draft for {supplier_name}", expanded=True):
                                        st.code(email)
                                        st.download_button(
                                            label="⬇️ Download Draft",
                                            data=email,
                                            file_name=f"negotiation_{safe_name}.txt",
                                            mime="text/plain"
                                        )
                                else:
                                    st.error(gen_res.text)
                            except Exception as e:
                                st.error(f"Generation error: {e}")

            else:
                st.caption("No suppliers yet. Use Add Supplier above.")
        else:
            st.error(sup_list_res.text)
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
                                  <div class="po-title">{po['po_number']}</div>
                                  <div class="po-meta">{po['product_name']} • {po['supplier_name']}</div>
                                </div>
                                <div style="display:flex; gap:8px; align-items:center;">
                                  <span class="po-status" style="background:{status_info['color']}">{status_info['icon']} {po['status']}</span>
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
                            if st.button("✅ Approve", key=f"approve_{po['id']}", disabled=not can_approve, width="stretch", type="primary" if can_approve else "secondary"):
                                update_po_status(po['id'], "APPROVED")
                        with col2:
                            if st.button("🚚 Transit", key=f"transit_{po['id']}", disabled=not can_transit, width="stretch", type="primary" if can_transit else "secondary"):
                                update_po_status(po['id'], "IN_TRANSIT")
                        with col3:
                            if st.button("📦 Receive", key=f"receive_{po['id']}", disabled=not can_receive, width="stretch", type="primary" if can_receive else "secondary"):
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
if page == "Logistics Risk":
    st.title("🚛 Logistics Control Tower")
    
    # Tabs for new functionality
    tab_active, tab_plan, tab_carriers = st.tabs(["📡 Active Shipments", "➕ Plan New Shipment", "🏢 Carrier Management"])
    
    # ==========================================
    # TAB 1: ACTIVE SHIPMENTS & SATELLITE TRACKING
    # ==========================================
    # ==========================================
    # TAB 1: ACTIVE SHIPMENTS & SATELLITE TRACKING
    # ==========================================
    with tab_active:
        st.subheader("Live Shipment Tracking")
        
        try:
            shipments = requests.get(f"{API_URL}/logistics/shipments/list").json()
            if not shipments:
                st.info("No active shipments found.")
            else:
                # 3-Column Layout for shipments list
                cols = st.columns(3)
                for idx, ship in enumerate(shipments):
                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"**#{ship['tracking_number']}**")
                            st.caption(f"{ship['origin']} ➝ {ship['destination']}")
                            st.progress(ship['progress_percent'] / 100)
                            st.caption(f"Status: {ship['status']}")
                            
                            if st.button("🛰️ Track Live", key=f"track_{ship['id']}", width="stretch"):
                                st.session_state['tracking_shipment'] = ship
                                st.rerun()

        except Exception as e:
            st.error(f"Error loading shipments: {e}")
            
        # SATELLITE COMMAND CENTER & DRIVER MODE
        if 'tracking_shipment' in st.session_state:
            s_initial = st.session_state['tracking_shipment']
            
            # RE-FETCH latest data to ensure coordinates are fresh
            try:
                # Find the specific shipment in the list (inefficient but safe for prototype)
                fresh_shipments = requests.get(f"{API_URL}/logistics/shipments/list").json()
                s = next((item for item in fresh_shipments if item["id"] == s_initial["id"]), s_initial)
            except:
                s = s_initial

            st.divider()
            st.markdown(f"### 🛰️ Live Operations: {s['tracking_number']}")
            
            # --- DRIVER MODE (SENDER) ---
            with st.expander("🚚 Driver Controls (Click here if you are the Driver)", expanded=True):
                st.info("Click 'Start Delivery' to begin broadcasting your GPS location to the control tower.")
                
                # JavaScript for Geolocation
                # We use a unique key to prevent re-running on every refresh unless intended
                start_gps = st.button("▶️ Start Delivery (Enable GPS Broadcast)", key=f"start_gps_{s['id']}")
                stop_gps = st.button("⏹️ Stop Broadcast", key=f"stop_gps_{s['id']}")
                
                if start_gps:
                    gps_js = f"""
                    <script>
                        if (navigator.geolocation) {{
                            navigator.geolocation.watchPosition(function(position) {{
                                var lat = position.coords.latitude;
                                var lon = position.coords.longitude;
                                
                                // Send to Backend
                                fetch('{API_URL}/logistics/shipments/{s['id']}/update', {{
                                    method: 'POST',
                                    headers: {{
                                        'Content-Type': 'application/json',
                                    }},
                                    body: JSON.stringify({{
                                        "current_location_lat": lat, 
                                        "current_location_lon": lon,
                                        "status": "IN_TRANSIT"
                                    }})
                                }});
                                
                                document.getElementById("gps_status").innerHTML = "✅ GPS Broadcasting: " + lat.toFixed(5) + ", " + lon.toFixed(5);
                            }}, function(error) {{
                                document.getElementById("gps_status").innerHTML = "❌ GPS Error: " + error.message;
                            }}, {{
                                enableHighAccuracy: true
                            }});
                        }} else {{
                            document.getElementById("gps_status").innerHTML = "❌ Geolocation not supported.";
                        }}
                    </script>
                    <div id="gps_status" style="font-weight:bold; color:green; padding:10px; border:1px solid #ddd; background:#f9f9f9;">
                        ⏳ Requesting Location Permission...
                    </div>
                    """
                    components.html(gps_js, height=80)
                
                if stop_gps:
                    st.warning("Broadcast Stopped.")

            # --- CONTROL TOWER MODE (VIEWER) ---
            track_col1, track_col2 = st.columns([3, 1])
            
            with track_col1:
                # Live Map Visualization
                lat = s.get('current_location_lat')
                lon = s.get('current_location_lon')
                
                if lat and lon:
                    current_pos = [lat, lon]
                    
                    # Map Configuration - SATELLITE TILES (Google Maps Hybrid)
                    m = folium.Map(
                        location=current_pos,
                        zoom_start=15,
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                        attr='Google'
                    )
                    
                    # Draw Original Planned Route (if available) - FADED
                    if s.get('route_geometry'):
                        try:
                            decoded_path = polyline.decode(s['route_geometry'])
                            folium.PolyLine(decoded_path, color="#94a3b8", weight=3, opacity=0.3, dash_array="5,5").add_to(m)
                        except: pass
                    
                    # Get DYNAMIC ROUTE from current location to destination
                    try:
                        # Get destination coordinates
                        dest_coords = None
                        if s.get('destination'):
                            from geopy.geocoders import Nominatim
                            geolocator = Nominatim(user_agent="scm_dashboard")
                            location = geolocator.geocode(s['destination'])
                            if location:
                                dest_coords = (location.latitude, location.longitude)
                        
                        if dest_coords:
                            # Call OSRM for dynamic route
                            osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon},{lat};{dest_coords[1]},{dest_coords[0]}"
                            osrm_params = {"overview": "full", "geometries": "polyline"}
                            osrm_res = requests.get(osrm_url, params=osrm_params, timeout=5)
                            
                            if osrm_res.status_code == 200:
                                route_data = osrm_res.json()
                                if route_data.get('routes'):
                                    remaining_geometry = route_data['routes'][0]['geometry']
                                    remaining_path = polyline.decode(remaining_geometry)
                                    # Draw REMAINING route in GREEN (bold)
                                    folium.PolyLine(remaining_path, color="#10b981", weight=6, opacity=0.8).add_to(m)
                                    
                                    # Add destination marker
                                    folium.Marker(
                                        dest_coords,
                                        popup=f"Destination: {s['destination']}",
                                        icon=folium.Icon(color="blue", icon="flag-checkered", prefix="fa")
                                    ).add_to(m)
                    except Exception as e:
                        st.caption(f"⚠️ Could not calculate dynamic route: {str(e)[:50]}")
                    
                    # Live Truck Marker
                    folium.Marker(
                        current_pos,
                        popup=f"LIVE: {s['tracking_number']}",
                        icon=folium.Icon(color="red", icon="truck", prefix="fa")
                    ).add_to(m)
                    
                    # Render Map
                    st_folium(m, width="100%", height=500, key=f"map_{s['id']}_{lat}_{lon}") # Key updates map on change
                else:
                    st.warning("⚠️ No GPS signal received yet. Driver must enable tracking.")

            with track_col2:
                st.markdown("**📡 Telemetry**")
                st.metric("Status", s['status'])
                
                if lat and lon:
                    st.caption(f"Lat: {lat:.5f}")
                    st.caption(f"Lon: {lon:.5f}")
                    st.success("Signal: Strong")
                else:
                    st.error("Signal: Offline")
                
                if st.button("🔄 Refresh Map"):
                    st.rerun()
                
                st.caption("Auto-refresh not enabled to save resources. Click Refresh to see latest position.")


    # ==========================================
    # TAB 2: PLAN NEW SHIPMENT (Pre-Schedule Calculation)
    # ==========================================
    with tab_plan:
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("1️⃣ Route Details")
            ref_num = st.text_input("Tracking/Reference #", f"TRK-{int(time.time())}")
            
            p_start = st.text_input("📍 Origin", "Mumbai, India", help="E.g. College Location")
            
            # Waypoints (Simplified for clarity, can add back dynamic if needed)
            if "plan_waypoints" not in st.session_state: st.session_state.plan_waypoints = []
            
            p_end = st.text_input("🏁 Destination", "Pune, India", help="E.g. Home Location")

            # 2. CALCULATION STEP
            if st.button("🧮 Calculate Logistics", type="primary"):
                with st.spinner("Analyzing Route..."):
                    try:
                        # Use existing plan_route API to get metrics
                        payload = {
                            "start_address": p_start,
                            "end_address": p_end,
                            "waypoints": []
                        }
                        res = requests.post(f"{API_URL}/logistics/plan_route", json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state['planned_route_metrics'] = data
                            st.success("Analysis Complete!")
                        else:
                            st.error(res.text)
                    except Exception as e:
                        st.error(f"Error: {e}")

        # METRICS PREVIEW
        with c2:
            st.subheader("2️⃣ Estimates")
            if 'planned_route_metrics' in st.session_state:
                m = st.session_state['planned_route_metrics']['route_info']
                dist = m['distance_km']
                dur = m['duration_min']
                
                # Custom Calculation: (Distance / 40) * 100
                fuel_cost = (dist / 40) * 100
                
                st.metric("Total Distance", f"{dist} km")
                st.metric("Est. Time", f"{int(dur // 60)}h {int(dur % 60)}m")
                st.metric("Est. Fuel Cost", f"₹{fuel_cost:.2f}", help=f"({dist}km / 40km/l) * ₹100/l")
                
                st.divider()
                
                # Fetch Resources for Final Step
                try:
                    carriers = requests.get(f"{API_URL}/logistics/carriers/list").json() or []
                    drivers = requests.get(f"{API_URL}/logistics/drivers/list").json() or []
                    c_map = {c['name']: c['id'] for c in carriers}
                    d_map = {d['name']: d['id'] for d in drivers}
                    
                    st.subheader("3️⃣ Schedule")
                    s_c = st.selectbox("Carrier", list(c_map.keys()) if c_map else [])
                    s_d = st.selectbox("Driver", list(d_map.keys()) if d_map else [])
                    
                    if st.button("📅 Confirm & Schedule", type="primary", width="stretch"):
                        payload = {
                            "tracking_number": ref_num,
                            "origin": p_start,
                            "destination": p_end,
                            "carrier_id": c_map.get(s_c),
                            "driver_id": d_map.get(s_d)
                        }
                        res = requests.post(f"{API_URL}/logistics/shipments/create", json=payload)
                        if res.status_code == 200:
                            st.success("✅ Scheduled!")
                            time.sleep(1)
                            st.rerun()
                except:
                    st.warning("Ensure carriers/drivers are added first.")
            else:
                st.info("Enter locations and click 'Calculate' to see metrics.")


    # ==========================================
    # TAB 3: CARRIER MANAGEMENT
    # ==========================================
    with tab_carriers:
        st.subheader("Partner Carriers")
        
        with st.expander("➕ Add New Carrier", expanded=False):
            with st.form("add_carrier"):
                c_name = st.text_input("Carrier Name")
                c_contact = st.text_input("Contact Info")
                c_fleet = st.number_input("Fleet Size", 1, 1000)
                submitted = st.form_submit_button("Add Carrier")
                if submitted:
                    res = requests.post(f"{API_URL}/logistics/carriers/create", json={"name": c_name, "contact_info": c_contact, "fleet_size": c_fleet})
                    if res.status_code == 200: st.success("Carrier Added!")
        
        st.divider()
        
        st.subheader("Drivers Pool")
        with st.expander("➕ Onboard Driver", expanded=False):
            with st.form("add_driver"):
                try:
                    carriers = requests.get(f"{API_URL}/logistics/carriers/list").json() or []
                    c_map = {c['name']: c['id'] for c in carriers}
                    
                    d_name = st.text_input("Driver Name")
                    d_license = st.text_input("License #")
                    d_carrier = st.selectbox("Associated Carrier", list(c_map.keys()) if c_map else [])
                    
                    sub_d = st.form_submit_button("Add Driver")
                    if sub_d and d_carrier:
                        res = requests.post(f"{API_URL}/logistics/drivers/create", json={
                            "name": d_name, 
                            "license_number": d_license, 
                            "carrier_id": c_map[d_carrier]
                        })
                        if res.status_code == 200: st.success("Driver Onboarded!")
                except: st.error("Load carriers first")

            # Customer Tracking Page Implementation
# This will be appended to dashboard.py

# ==========================================
# PAGE: LOGISTICS OPTIMIZE (Customer Tracking)
# ==========================================
if page == "Logistics Optimize":
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 24px 32px; border-radius: 12px; 
                box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 24px;">
        <h1 style="margin: 0; font-size: 2em; font-weight: 700; letter-spacing: -0.5px;">📦 Track Your Delivery</h1>
        <p style="margin: 8px 0 0 0; font-size: 0.95em; opacity: 0.85; font-weight: 400;">Real-time delivery tracking</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tracking Number Input
    tracking_number = st.text_input("🔍 Enter Tracking Number", placeholder="e.g., SHIP-2024-001")
    
    if tracking_number:
        try:
            # Fetch shipment data
            shipments = requests.get(f"{API_URL}/logistics/shipments/list").json()
            shipment = next((s for s in shipments if s['tracking_number'] == tracking_number), None)
            
            if shipment:
                # Display shipment info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", shipment['status'])
                with col2:
                    st.metric("Progress", f"{shipment.get('progress_percent', 0):.1f}%")
                with col3:
                    if shipment.get('eta'):
                        eta_str = shipment['eta'].split('T')[0] if 'T' in str(shipment['eta']) else str(shipment['eta'])
                        st.metric("ETA", eta_str)
                    else:
                        st.metric("ETA", "Calculating...")
                
                # Progress Bar
                progress = shipment.get('progress_percent', 0)
                st.markdown(f"""
                <div style="background: #e5e7eb; border-radius: 10px; height: 24px; overflow: hidden; margin: 20px 0;">
                    <div style="background: linear-gradient(90deg, #10b981, #059669); 
                                width: {progress}%; height: 100%; 
                                transition: width 0.5s ease;
                                display: flex; align-items: center; justify-content: center;
                                color: white; font-weight: bold; font-size: 0.85em;">
                        {progress:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                
                # Live Map
                lat = shipment.get('current_location_lat')
                lon = shipment.get('current_location_lon')
                
                if lat and lon:
                    st.subheader("🗺️ Live Location")
                    
                    # Map
                    m = folium.Map(
                        location=[lat, lon],
                        zoom_start=14,
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                        attr='Google'
                    )
                    
                    # Driver marker
                    folium.Marker(
                        [lat, lon],
                        popup=f"Driver Location",
                        icon=folium.Icon(color="red", icon="truck", prefix="fa")
                    ).add_to(m)
                    
                    # Try to show route to destination
                    try:
                        if shipment.get('destination'):
                            from geopy.geocoders import Nominatim
                            geolocator = Nominatim(user_agent="scm_dashboard")
                            dest_location = geolocator.geocode(shipment['destination'])
                            
                            if dest_location:
                                dest_coords = (dest_location.latitude, dest_location.longitude)
                                
                                # Destination marker
                                folium.Marker(
                                    dest_coords,
                                    popup=f"Destination: {shipment['destination']}",
                                    icon=folium.Icon(color="green", icon="home", prefix="fa")
                                ).add_to(m)
                                
                                # Route line
                                osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon},{lat};{dest_coords[1]},{dest_coords[0]}"
                                osrm_res = requests.get(osrm_url, params={"overview": "full", "geometries": "polyline"}, timeout=5)
                                
                                if osrm_res.status_code == 200:
                                    route_data = osrm_res.json()
                                    if route_data.get('routes'):
                                        route_geom = route_data['routes'][0]['geometry']
                                        route_path = polyline.decode(route_geom)
                                        folium.PolyLine(route_path, color="#3b82f6", weight=5, opacity=0.7).add_to(m)
                    except:
                        pass
                    
                    st_folium(m, width="100%", height=450)
                    
                    # Auto-refresh button
                    st.info("💡 Click the button below to refresh and see the latest location")
                    if st.button("🔄 Refresh Tracking", type="primary"):
                        st.rerun()
                else:
                    st.warning("📍 Waiting for driver to start delivery...")
                    
            else:
                st.error("❌ Tracking number not found. Please check and try again.")
        except Exception as e:
            st.error(f"Error fetching tracking data: {e}")
    else:
        st.info("👆 Enter your tracking number above to see delivery status")
