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

# TAB 1: EXECUTIVE BRIEFING (Full PageSpeed Insights Replica with Insights & Diagnostics)
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
        recorded_time = latest_row.get("recorded_at").strftime("%b %d, %Y, %I:%M %p GMT%z") if pd.notnull(latest_row.get("recorded_at")) else "Sep 12, 2026, 11:41 PM GMT+1"
        
        avg_lcp = latest_row.get("lcp_ms", 0.0) / 1000.0
        avg_tbt = latest_row.get("tbt_ms", 0.0)
        avg_cls = latest_row.get("cls", 0.0)
        avg_ttfb = latest_row.get("ttfb_ms", 0.0)
        
        score_color, score_bg = get_psi_grade_color(perf_score)
        
        # PSI Top URL Bar Header Container
        url_bar_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px 24px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,28,64,0.08);"><div><span style="font-size: 12px; font-weight: 500; color: #5f6368; text-transform: uppercase; letter-spacing: 0.8px;">PageSpeed Insights Audit URL</span><div style="font-size: 18px; font-weight: 400; color: #1a73e8; margin-top: 2px; word-break: break-all;"><a href="{target_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">{target_url}</a></div></div><div style="background-color: #f1f3f4; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; color: #3c4043; text-transform: capitalize;">💻 Form Factor: {selected_strategy}</div></div>'
        st.markdown(url_bar_html, unsafe_allow_html=True)

        # Audit Metadata Bar
        meta_bar_html = f'<div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; padding: 12px 20px; margin-bottom: 24px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 12px; color: #5f6368;"><div style="display: flex; align-items: center; gap: 8px;">📅 <span>Captured at {recorded_time}</span></div><div style="display: flex; align-items: center; gap: 8px;">💻 <span>Emulated {selected_strategy.capitalize()} with Lighthouse 13.4.1</span></div><div style="display: flex; align-items: center; gap: 8px;">🔗 <span>Single page session</span></div><div style="display: flex; align-items: center; gap: 8px;">⏱️ <span>Initial page load</span></div><div style="display: flex; align-items: center; gap: 8px;">📶 <span>Custom throttling</span></div><div style="display: flex; align-items: center; gap: 8px;">🌐 <span>Using HeadlessChromium 151.0.7922.173</span></div></div>'
        st.markdown(meta_bar_html, unsafe_allow_html=True)

        # Executive Summary Callout
        executive_summary = f'<div style="background-color: #e8f0fe; border-left: 4px solid #1a73e8; padding: 16px; border-radius: 4px; margin-bottom: 24px; color: #174ea6;"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">Executive Summary & Health Status</div><div style="font-size: 13px; line-height: 1.5;">The current performance score for this {selected_strategy} environment is <strong>{perf_score}/100</strong>. Key load speeds (LCP at <strong>{avg_lcp:.2f}s</strong>) and layout stability (CLS at <strong>{avg_cls:.3f}</strong>) are continuously audited against Google Core Web Vitals standards. <a href="https://web.dev/explore/learn-core-web-vitals" target="_blank" style="color: #1a73e8; font-weight: 600; text-decoration: underline;">Read official CWV definitions &rarr;</a></div></div>'
        st.markdown(executive_summary, unsafe_allow_html=True)

        # Main Performance Section
        col_gauge, col_metrics = st.columns([1, 2.5])
        
        with col_gauge:
            gauge_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 28px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;"><div style="font-size: 14px; font-weight: 500; color: #5f6368; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px;">Performance Score</div><div style="width: 110px; height: 110px; border-radius: 50%; border: 8px solid {score_color}; background-color: {score_bg}; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px auto;"><span style="font-size: 38px; font-weight: 700; color: {score_color};">{perf_score}</span></div><div style="font-size: 12px; color: #5f6368;">Scale: 0-49 (Poor) | 50-89 (Average) | 90-100 (Good)</div></div>'
            st.markdown(gauge_html, unsafe_allow_html=True)

        with col_metrics:
            lcp_color = "#0cce6b" if avg_lcp <= 2.5 else ("#ffa400" if avg_lcp <= 4.0 else "#ff4e42")
            tbt_color = "#0cce6b" if avg_tbt <= 200 else ("#ffa400" if avg_tbt <= 600 else "#ff4e42")
            cls_color = "#0cce6b" if avg_cls <= 0.10 else ("#ffa400" if avg_cls <= 0.25 else "#ff4e42")
            ttfb_color = "#0cce6b" if avg_ttfb <= 800 else ("#ffa400" if avg_ttfb <= 1800 else "#ff4e42")

            metrics_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"><div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 14px; border-bottom: 1px solid #e8eaed; padding-bottom: 8px;">Core Web Vitals & Technical Diagnostics</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;"><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {lcp_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Largest Contentful Paint (LCP)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_lcp:.2f} s</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 2.5s (Good)</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {tbt_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Total Blocking Time (TBT)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_tbt:.0f} ms</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 200 ms</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {cls_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Cumulative Layout Shift (CLS)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_cls:.3f}</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 0.10 (Good)</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {ttfb_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Server Response Time (TTFB)</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_ttfb:.0f} ms</div><div style="font-size: 11px; color: #5f6368;">Target: ≤ 800 ms</div></div></div></div>'
            st.markdown(metrics_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # INSIGHTS & OPPORTUNITIES SECTION (Replicating PSI Panel)
        insights_box_html = """
        <div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e8eaed; padding-bottom: 10px; margin-bottom: 14px;">
                <span style="font-size: 14px; font-weight: 600; color: #202124; text-transform: uppercase; letter-spacing: 0.5px;">Insights</span>
                <span style="font-size: 12px; color: #5f6368;">Show audits relevant to: <strong><u>All</u></strong> FCP LCP TBT CLS</span>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: #202124;">
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> Render-blocking requests &mdash; <span style="color: #d93025; font-weight: 500;">Est savings of 1,380 ms</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> Forced reflow</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> LCP breakdown</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> LCP request discovery</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> Network dependency tree</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #f9ab00; font-weight: bold; margin-right: 8px;">■</span> Use efficient cache lifetimes &mdash; <span style="color: #b06000; font-weight: 500;">Est savings of 83 KiB</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #f9ab00; font-weight: bold; margin-right: 8px;">■</span> Font display &mdash; <span style="color: #b06000; font-weight: 500;">Est savings of 10 ms</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #f9ab00; font-weight: bold; margin-right: 8px;">■</span> Improve image delivery &mdash; <span style="color: #b06000; font-weight: 500;">Est savings of 1,287 KiB</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #f9ab00; font-weight: bold; margin-right: 8px;">■</span> Legacy JavaScript &mdash; <span style="color: #b06000; font-weight: 500;">Est savings of 7 KiB</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #9aa0a6; font-weight: bold; margin-right: 8px;">●</span> Layout shift culprits</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #9aa0a6; font-weight: bold; margin-right: 8px;">●</span> 3rd parties</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
            </div>
            <div style="font-size: 12px; color: #5f6368; margin-top: 14px; border-top: 1px solid #f1f3f4; padding-top: 10px;">
                These insights are also available in the Chrome DevTools Performance Panel &mdash; <a href="https://developer.chrome.com/docs/devtools/performance/" target="_blank" style="color: #1a73e8; text-decoration: none;">record a trace</a> to view more detailed information.
            </div>
        </div>
        """
        st.markdown(insights_box_html, unsafe_allow_html=True)

        # DIAGNOSTICS SECTION
        diagnostics_box_html = """
        <div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 24px;">
            <div style="border-bottom: 1px solid #e8eaed; padding-bottom: 10px; margin-bottom: 14px;">
                <span style="font-size: 14px; font-weight: 600; color: #202124; text-transform: uppercase; letter-spacing: 0.5px;">Diagnostics</span>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 8px; font-size: 13px; color: #202124;">
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> Reduce unused JavaScript &mdash; <span style="color: #d93025; font-weight: 500;">Est savings of 196 KiB</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #d93025; font-weight: bold; margin-right: 8px;">▲</span> Reduce unused CSS &mdash; <span style="color: #d93025; font-weight: 500;">Est savings of 179 KiB</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #f9ab00; font-weight: bold; margin-right: 8px;">■</span> Image elements do not have explicit width and height</div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; border-bottom: 1px solid #f1f3f4; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #9aa0a6; font-weight: bold; margin-right: 8px;">●</span> Avoid long main-thread tasks &mdash; <span style="color: #5f6368; font-weight: 500;">5 long tasks found</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
                <div style="padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div><span style="color: #9aa0a6; font-weight: bold; margin-right: 8px;">●</span> Avoid non-composited animations &mdash; <span style="color: #5f6368; font-weight: 500;">2 animated elements found</span></div>
                    <span style="color: #5f6368; font-size: 12px;">▼</span>
                </div>
            </div>
            <div style="font-size: 12px; color: #5f6368; margin-top: 14px; border-top: 1px solid #f1f3f4; padding-top: 10px;">
                More information about the performance of your application. These numbers don't <span style="text-decoration: underline;">directly affect</span> the Performance score.
            </div>
        </div>
        """
        st.markdown(diagnostics_box_html, unsafe_allow_html=True)

        # Additional PSI Audit Pillars Section
        st.markdown('<div style="font-size: 16px; font-weight: 600; color: #202124; margin-bottom: 12px;">Additional PageSpeed Audit Pillars</div>', unsafe_allow_html=True)
        
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #1a73e8;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">Accessibility</div><div style="font-size: 28px; font-weight: 700; color: #1a73e8; margin: 8px 0;">90</div><div style="font-size: 11px; color: #5f6368;">Labels & Contrast Checks</div></div>', unsafe_allow_html=True)
            
        with col_p2:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #0cce6b;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">Best Practices</div><div style="font-size: 28px; font-weight: 700; color: #0cce6b; margin: 8px 0;">96</div><div style="font-size: 11px; color: #5f6368;">Trust & Code Standards</div></div>', unsafe_allow_html=True)
            
        with col_p3:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #ffa400;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">SEO</div><div style="font-size: 28px; font-weight: 700; color: #ffa400; margin: 8px 0;">61</div><div style="font-size: 11px; color: #5f6368;">Crawling & Meta Tags</div></div>', unsafe_allow_html=True)

        with col_p4:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #1a73e8;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">Agentic Browsing</div><div style="font-size: 28px; font-weight: 700; color: #1a73e8; margin: 8px 0;">1/3</div><div style="font-size: 11px; color: #5f6368;">AI Agent Accessibility</div></div>', unsafe_allow_html=True)

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
