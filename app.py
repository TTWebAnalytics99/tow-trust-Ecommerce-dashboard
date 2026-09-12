import os
import psycopg2
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="TT SWPTA", layout="wide")

DB_URI = st.secrets.get("DATABASE_URL") or os.getenv("DATABASE_URL")
API_KEY = st.secrets.get("PAGESPEED_API_KEY") or os.getenv("PAGESPEED_API_KEY", "")

def authenticate():
    auto_viewer = str(st.secrets.get("AUTO_LOGIN_VIEWER", "false")).lower() == "true"
    is_kiosk_url = st.query_params.get("mode") == "kiosk"

    if auto_viewer or is_kiosk_url:
        st.session_state["auth_ok"] = True
        st.session_state["role"] = "viewer"
        return

    def check():
        user_input = st.session_state.get("pass_input", "").strip()
        admin_pass = st.secrets.get("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD")
        viewer_pass = st.secrets.get("VIEWER_PASSWORD") or os.getenv("VIEWER_PASSWORD", "viewer123")

        if admin_pass and user_input == str(admin_pass).strip():
            st.session_state["auth_ok"] = True
            st.session_state["role"] = "admin"
            del st.session_state["pass_input"]
        elif viewer_pass and user_input == str(viewer_pass).strip():
            st.session_state["auth_ok"] = True
            st.session_state["role"] = "viewer"
            del st.session_state["pass_input"]
        else:
            st.session_state["auth_ok"] = False

    if not st.session_state.get("auth_ok", False):
        st.subheader("🔒 Tow-Trust ECommerce Web Performance and Synthetic Testing Application")
        st.text_input("Enter Passkey", type="password", key="pass_input", on_change=check)
        if st.session_state.get("auth_ok") is False:
            st.error("Invalid credentials.")
        st.stop()

    with st.sidebar:
        role_label = "Administrator" if st.session_state.get("role") == "admin" else "Office Kiosk (Viewer)"
        st.write(f"Logged in as **{role_label}**")
        if st.button("🚪 Log Out", key="logout_btn", use_container_width=True):
            st.session_state["auth_ok"] = False
            st.session_state["role"] = None
            st.rerun()

authenticate()

def get_db_connection():
    return psycopg2.connect(DB_URI)

def get_metric_grade(val, good_threshold, poor_threshold, is_lower_better=True):
    if is_lower_better:
        if val <= good_threshold:
            return "A", "Good", "success"
        elif val <= poor_threshold:
            return "C", "Needs Improvement", "warning"
        else:
            return "F", "Poor", "error"
    else:
        if val >= good_threshold:
            return "A", "Good", "success"
        elif val >= poor_threshold:
            return "C", "Needs Improvement", "warning"
        else:
            return "F", "Poor", "error"

def render_gtmetrix_card(title, value, grade, status_text, target_str, status_type):
    color_map = {
        'success': {'border': '#28a745', 'bg': '#e6f4ea', 'badge': '#137333'},
        'warning': {'border': '#f9ab00', 'bg': '#fef7e0', 'badge': '#b06000'},
        'error': {'border': '#d93025', 'bg': '#fce8e6', 'badge': '#c5221f'}
    }
    c = color_map.get(status_type, color_map['success'])
    
    return f"""
    <div style="border: 1px solid #e0e0e0; border-top: 4px solid {c['border']}; background-color: {c['bg']}; padding: 18px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 13px; font-weight: 600; color: #444; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
            <span style="background-color: {c['badge']}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 13px;">Grade {grade}</span>
        </div>
        <div style="font-size: 32px; font-weight: 700; color: #111; margin-bottom: 6px;">{value}</div>
        <div style="font-size: 13px; color: #333; font-weight: 600; margin-bottom: 4px;">{status_text}</div>
        <div style="font-size: 12px; color: #555; border-top: 1px solid rgba(0,0,0,0.08); padding-top: 6px; margin-top: 4px;">{target_str}</div>
    </div>
    """

is_admin = st.session_state.get("role") == "admin"
tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks"]
tabs = st.tabs(tab_titles)

# TAB 1: EXECUTIVE BRIEFING
with tabs[0]:
    st.header("📑 Executive Core Web Vitals Briefing")
    st.caption("Live operational health evaluated against Google Core Web Vitals standards.")

    # Informational box with link to Core Web Vitals definitions
    st.markdown("""
    <div style="background-color: #f8f9fa; border-left: 4px solid #1f77b4; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; font-size: 14px; color: #333;">
        <strong>Core Web Vitals (CWV) Guide:</strong> These are essential metrics measuring real-world user experience for loading performance, interactivity, and visual stability. 
        <a href="https://web.dev/explore/learn-core-web-vitals" target="_blank" style="color: #1f77b4; text-decoration: none; font-weight: 600;">View official Core Web Vitals definitions &rarr;</a>
    </div>
    """, unsafe_allow_html=True)

    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs WHERE recorded_at >= NOW() - INTERVAL '30 days' ORDER BY recorded_at ASC;", conn)

    if df.empty:
        st.info("No performance telemetry recorded yet.")
    else:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)
        
        avg_lcp = (df["lcp_ms"] / 1000.0).mean()
        avg_tbt = df["tbt_ms"].mean()
        avg_cls = df["cls"].mean()

        lcp_compliance = (len(df[df["lcp_ms"] <= 2500]) / len(df)) * 100.0 if len(df) > 0 else 0.0
        tbt_compliance = (len(df[df["tbt_ms"] <= 200]) / len(df)) * 100.0 if len(df) > 0 else 0.0
        cls_compliance = (len(df[df["cls"] <= 0.10]) / len(df)) * 100.0 if len(df) > 0 else 0.0

        sla_passes = len(df[(df["lcp_ms"] <= 2500) & (df["tbt_ms"] <= 200) & (df["cls"] <= 0.10)])
        sla_rate = (sla_passes / len(df)) * 100.0 if len(df) > 0 else 0.0

        overall_grade, overall_status, overall_type = get_metric_grade(sla_rate, 90.0, 50.0, is_lower_better=False)
        lcp_grade, lcp_status, lcp_type = get_metric_grade(avg_lcp, 2.5, 4.0, is_lower_better=True)
        tbt_grade, tbt_status, tbt_type = get_metric_grade(avg_tbt, 200, 600, is_lower_better=True)
        cls_grade, cls_status, cls_type = get_metric_grade(avg_cls, 0.10, 0.25, is_lower_better=True)

        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(render_gtmetrix_card("CWV Compliance Rate", f"{sla_rate:.1f}%", overall_grade, overall_status, "KPI Target: ≥ 90% SLA Pass Rate", overall_type), unsafe_allow_html=True)
        with c2:
            st.markdown(render_gtmetrix_card("Avg LCP (Visual Speed)", f"{avg_lcp:.2f} s", lcp_grade, lcp_status, f"KPI Target: ≤ 2.5s ({lcp_compliance:.0f}% meeting target)", lcp_type), unsafe_allow_html=True)
        with c3:
            st.markdown(render_gtmetrix_card("Avg TBT (Interaction)", f"{avg_tbt:.0f} ms", tbt_grade, tbt_status, f"KPI Target: ≤ 200ms ({tbt_compliance:.0f}% meeting target)", tbt_type), unsafe_allow_html=True)
        with c4:
            st.markdown(render_gtmetrix_card("Avg CLS (Stability)", f"{avg_cls:.3f}", cls_grade, cls_status, f"KPI Target: ≤ 0.10 ({cls_compliance:.0f}% meeting target)", cls_type), unsafe_allow_html=True)

# TAB 2: URL VITALS
with tabs[1]:
    st.header("📊 Historical URL Vitals")
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at ASC;", conn)

    if not df.empty:
        sel_url = st.selectbox("Select Target URL", df["target_url"].unique())
        filt = df[df["target_url"] == sel_url]
        fig = px.line(filt, x="recorded_at", y=["lcp_ms", "tbt_ms", "ttfb_ms"], title="Latency Evolution (ms)")
        st.plotly_chart(fig, use_container_width=True)

# TAB 3: ASSET BOTTLENECKS
with tabs[2]:
    st.header("🎨 Asset & Resource Bottlenecks")
    with get_db_connection() as conn:
        df_code = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at DESC LIMIT 1;", conn)
    if not df_code.empty:
        row = df_code.iloc[0]
        st.metric("Unoptimized Image Waste", f"{row.get('unoptimized_images_kb', 0):.1f} KB")
        st.metric("Unused CSS Payload", f"{row.get('unused_css_kb', 0):.1f} KB")
        st.metric("Third-Party Script Drag", f"{row.get('third_party_main_thread_ms', 0):.0f} ms")
