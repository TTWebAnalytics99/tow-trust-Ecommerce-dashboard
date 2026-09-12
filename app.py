import os
import psycopg2
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="SANDBOX TT SWPTA", layout="wide")

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
        st.subheader("🔒 SANDBOX Tow-Trust ECommerce Web Performance and Synthetic Testing Application")
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

def get_psi_grade_color(score):
    if score >= 90:
        return "#0cce6b", "#e6f4ea"
    elif score >= 50:
        return "#ffa400", "#fef7e0"
    else:
        return "#ff4e42", "#fce8e6"

is_admin = st.session_state.get("role") == "admin"
tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks"]
tabs = st.tabs(tab_titles)

# TAB 1: EXECUTIVE BRIEFING (PageSpeed Insights Replica)
with tabs[0]:
    col_sel1, col_sel2 = st.columns([2, 4])
    with col_sel1:
        selected_strategy = st.radio("Select Form Factor", ["mobile", "desktop"], horizontal=True)

    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs WHERE recorded_at >= NOW() - INTERVAL '30 days' ORDER BY recorded_at ASC;", conn)

    if df.empty:
        st.info("No performance telemetry recorded yet.")
    else:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)
        
        df_strat = df[df["strategy"] == selected_strategy]
        if df_strat.empty:
            df_strat = df  

        latest_row = df_strat.iloc[-1]
        
        target_url = latest_row.get("target_url", "https://towtrust.cloudfyuat.com")
        perf_score = int(latest_row.get("perf_score", 0))
        
        avg_lcp = latest_row.get("lcp_ms", 0.0) / 1000.0
        avg_tbt = latest_row.get("tbt_ms", 0.0)
        avg_cls = latest_row.get("cls", 0.0)
        avg_ttfb = latest_row.get("ttfb_ms", 0.0)
        
        score_color, score_bg = get_psi_grade_color(perf_score)
        
        url_bar_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px 24px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,28,64,0.08);"><div><span style="font-size: 12px; font-weight: 500; color: #5f6368; text-transform: uppercase; letter-spacing: 0.8px;">PageSpeed Insights Audit URL</span><div style="font-size: 18px; font-weight: 400; color: #1a73e8; margin-top: 2px; word-break: break-all;"><a href="{target_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">{target_url}</a></div></div><div style="background-color: #f1f3f4; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; color: #3c4043; text-transform: capitalize;">💻 Form Factor: {selected_strategy}</div></div>'
        st.markdown(url_bar_html, unsafe_allow_html=True)

        banner_html = '<div style="background-color: #f8f9fa; border-left: 4px solid #1a73e8; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px; font-size: 13px; color: #3c4043;"><strong>Core Web Vitals Assessment:</strong> Google evaluates real-world user experience and lab performance against strict thresholds. <a href="https://web.dev/explore/learn-core-web-vitals" target="_blank" style="color: #1a73e8; text-decoration: none; font-weight: 500;">Learn more about Core Web Vitals metrics &rarr;</a></div>'
        st.markdown(banner_html, unsafe_allow_html=True)

        col_gauge, col_metrics = st.columns([1, 2.5])
        
        with col_gauge:
            gauge_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 28px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;"><div style="font-size: 14px; font-weight: 500; color: #5f6368; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px;">Performance Score</div><div style="width: 110px; height: 110px; border-radius: 50%; border: 8px solid {score_color}; background-color: {score_bg}; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto;"><span style="font-size: 38px; font-weight: 700; color: {score_color};">{perf_score}</span></div><div style="font-size: 12px; color: #5f6368;">Scale: 0-49 (Poor) | 50-89 (Average) | 90-100 (Good)</div></div>'
            st.markdown(gauge_html, unsafe_allow_html=True)

        with col_metrics:
            lcp_color = "#0cce6b" if avg_lcp <= 2.5 else ("#ffa400" if avg_lcp <= 4.0 else "#ff4e42")
            tbt_color = "#0cce6b" if avg_tbt <= 200 else ("#ffa400" if avg_tbt <= 600 else "#ff4e42")
            cls_color = "#0cce6b" if avg_cls <= 0.10 else ("#ffa400" if avg_cls <= 0.25 else "#ff4e42")
            ttfb_color = "#0cce6b" if avg_ttfb <= 800 else ("#ffa400" if avg_ttfb <= 1800 else "#ff4e42")

            metrics_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"><div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 14px; border-bottom: 1px solid #e8eaed; padding-bottom: 8px;">Diagnostics & Core Web Vitals Breakdown</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;"><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {lcp_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Largest Contentful Paint (LCP)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_lcp:.2f} s</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 2.5s (Good)</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {tbt_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Total Blocking Time (TBT)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_tbt:.0f} ms</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 200 ms</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {cls_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Cumulative Layout Shift (CLS)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_cls:.3f}</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 0.10 (Good)</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {ttfb_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Server Response Time (TTFB)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_ttfb:.0f} ms</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 800 ms</div></div></div></div>'
            st.markdown(metrics_html, unsafe_allow_html=True)

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
