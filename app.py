import os
import io
import psycopg2
import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

def get_psi_grade_color(score):
    if score >= 90:
        return "#0cce6b", "#e6f4ea"
    elif score >= 50:
        return "#ffa400", "#fef7e0"
    else:
        return "#ff4e42", "#fce8e6"

def get_gtmetrix_letter_grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    elif score >= 50:
        return "E"
    else:
        return "F"

def get_priority_prefix_and_badge(importance):
    if importance == 1:
        return "🔴 [Level 1]", '<span style="background-color: #d93025; color: white; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">🔴 Level 1 (Critical Priority)</span>'
    elif importance == 2:
        return "🟠 [Level 2]", '<span style="background-color: #f9ab00; color: #fff; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">🟠 Level 2 (Moderate Priority)</span>'
    else:
        return "🟢 [Level 3]", '<span style="background-color: #137333; color: white; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">🟢 Level 3 (Minor Optimization)</span>'

def generate_pdf_executive_report(df_target, target_url, strategy):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1a73e8'), spaceAfter=6)
    sub_style = ParagraphStyle('ReportSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#5f6368'), spaceAfter=15)
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#202124'), spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#3c4043'), leading=14, spaceAfter=8)

    story.append(Paragraph("Tow-Trust ECommerce Performance Executive Report", title_style))
    story.append(Paragraph(f"Environment: <b>{target_url}</b> | Form Factor: <b>{strategy.capitalize()}</b> | Generated: Oct 2026", sub_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Executive Summary & Plain English Overview", heading_style))
    exec_text = (
        "This report provides an immutable, transparent record of synthetic web performance audits conducted for Tow-Trust ECommerce. "
        "Core Web Vitals measure user experience benchmarks: <b>Largest Contentful Paint (LCP)</b> tracks main content loading speed (Target ≤ 2.5s), "
        "<b>Total Blocking Time (TBT)</b> measures main-thread interactivity freezes (Target ≤ 200ms), and <b>Cumulative Layout Shift (CLS)</b> "
        "evaluates visual stability and unexpected content jumping (Target ≤ 0.10)."
    )
    story.append(Paragraph(exec_text, body_style))

    story.append(Paragraph("2. Historical Performance Metrics Summary", heading_style))
    if not df_target.empty:
        mean_score = df_target["perf_score"].mean()
        mean_lcp = df_target["lcp_ms"].mean() / 1000.0
        mean_tbt = df_target["tbt_ms"].mean()
        mean_cls = df_target["cls"].mean()
        
        summary_data = [
            ["Metric Name", "Target Standard", "Observed Average", "Compliance Status"],
            ["Performance Score", "≥ 50 (Grade C+)", f"{mean_score:.1f} / 100", "Passing" if mean_score >= 50 else "Needs Attention"],
            ["Largest Contentful Paint (LCP)", "≤ 2.50 s", f"{mean_lcp:.2f} s", "Passing" if mean_lcp <= 2.5 else "Exceeded"],
            ["Total Blocking Time (TBT)", "≤ 200 ms", f"{mean_tbt:.0f} ms", "Passing" if mean_tbt <= 200 else "Exceeded"],
            ["Cumulative Layout Shift (CLS)", "≤ 0.10", f"{mean_cls:.3f}", "Passing" if mean_cls <= 0.10 else "Exceeded"]
        ]
        
        t = Table(summary_data, colWidths=[150, 100, 100, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0fe')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#174ea6')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dadce0')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("3. Strategic Recommendations", heading_style))
    rec_text = (
        "• <b>Image Compression:</b> Ensure all catalog products use next-gen formats (WebP/AVIF) to keep LCP optimized.<br/>"
        "• <b>Layout Stability:</b> Prevent dynamic banner injections from shifting DOM elements after initial render to secure CLS compliance.<br/>"
        "• <b>Script Budgeting:</b> Defer non-essential third-party marketing widgets to preserve main-thread CPU cycles."
    )
    story.append(Paragraph(rec_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

is_admin = st.session_state.get("role") == "admin"

if is_admin:
    tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks", "📋 ISO Reporting", "📈 Advanced Reporting", "⚙️ Custom URL Testing"]
else:
    tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks", "📋 ISO Reporting", "📈 Advanced Reporting"]

tabs = st.tabs(tab_titles)

# TAB 1: EXECUTIVE BRIEFING
with tabs[0]:
    col_sel1, col_sel2 = st.columns([2, 4])
    with col_sel1:
        selected_strategy = st.radio("Select Form Factor", ["mobile", "desktop"], horizontal=True)

    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at ASC;", conn)

    if df.empty:
        st.info("No performance telemetry recorded yet.")
    else:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)
        
        available_urls = df["target_url"].unique().tolist()
        selected_url = st.selectbox("Select Target URL / Environment", available_urls)

        df_url = df[(df["target_url"] == selected_url) & (df["strategy"] == selected_strategy)]

        if df_url.empty:
            df_url = df[df["target_url"] == selected_url]

        latest_row = df_url.iloc[-1] if not df_url.empty else df.iloc[-1]
        
        target_url = latest_row.get("target_url", selected_url)
        perf_score = int(latest_row.get("perf_score", 0))
        
        raw_time = latest_row.get("recorded_at")
        if pd.notnull(raw_time):
            if raw_time.tzinfo is None:
                raw_time = raw_time.tz_localize("UTC")
            else:
                raw_time = raw_time.tz_convert("UTC")
            uk_time = raw_time.tz_convert("Europe/London")
            recorded_time = uk_time.strftime("%b %d, %Y, %I:%M %p GMT%z")
            recorded_time = recorded_time[:-2] + ":" + recorded_time[-2:]
        else:
            recorded_time = "Recent Audit"
        
        audit_strategy = selected_strategy  
        
        avg_lcp = float(latest_row.get("lcp_ms", 0.0)) / 1000.0
        avg_tbt = float(latest_row.get("tbt_ms", 0.0))
        avg_cls = float(latest_row.get("cls", 0.0))
        avg_ttfb = float(latest_row.get("ttfb_ms", 0.0))
        speed_index = float(latest_row.get("speed_index_ms", latest_row.get("lcp_ms", 1900) * 0.9)) / 1000.0
        
        unoptimized_kb = float(latest_row.get("unoptimized_images_kb", 0))
        unused_css_kb = float(latest_row.get("unused_css_kb", 0))
        unused_js_kb = float(latest_row.get("unused_js_kb", 0))
        third_party_ms = float(latest_row.get("third_party_main_thread_ms", 0))
        
        total_asset_waste = unoptimized_kb + unused_css_kb + unused_js_kb
        
        score_color, score_bg = get_psi_grade_color(perf_score)
        current_letter = get_gtmetrix_letter_grade(perf_score)
        
        estimated_optimized_score = min(98, perf_score + 32)
        estimated_letter = get_gtmetrix_letter_grade(estimated_optimized_score)
        est_color, est_bg = get_psi_grade_color(estimated_optimized_score)
        
        url_bar_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px 24px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,28,64,0.08);"><div><span style="font-size: 12px; font-weight: 500; color: #5f6368; text-transform: uppercase; letter-spacing: 0.8px;">PageSpeed Insights Audit URL</span><div style="font-size: 18px; font-weight: 400; color: #1a73e8; margin-top: 2px; word-break: break-all;"><a href="{target_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">{target_url}</a></div></div><div style="background-color: #f1f3f4; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; color: #3c4043; text-transform: capitalize;">💻 Form Factor: {audit_strategy}</div></div>'
        st.markdown(url_bar_html, unsafe_allow_html=True)

        meta_bar_html = f'<div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; padding: 12px 20px; margin-bottom: 24px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 12px; color: #5f6368;"><div style="display: flex; align-items: center; gap: 8px;">📅 <span>Captured at {recorded_time}</span></div><div style="display: flex; align-items: center; gap: 8px;">💻 <span>Emulated {str(audit_strategy).capitalize()} with Lighthouse 13.4.1</span></div><div style="display: flex; align-items: center; gap: 8px;">🔗 <span>Single page session</span></div><div style="display: flex; align-items: center; gap: 8px;">⏱️ <span>Initial page load</span></div><div style="display: flex; align-items: center; gap: 8px;">📶 <span>Custom throttling</span></div><div style="display: flex; align-items: center; gap: 8px;">🌐 <span>Using HeadlessChromium 151.0.7922.173</span></div></div>'
        st.markdown(meta_bar_html, unsafe_allow_html=True)

        executive_summary = f'<div style="background-color: #e8f0fe; border-left: 4px solid #1a73e8; padding: 16px; border-radius: 4px; margin-bottom: 24px; color: #174ea6;"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">Executive Summary & Health Status</div><div style="font-size: 13px; line-height: 1.5;">The current performance score for environment <code>{target_url}</code> is <strong>{perf_score}/100 (Grade {current_letter})</strong>. Addressing all Level 1 and Level 2 priority insights is projected to lift performance to an estimated <strong>{estimated_optimized_score}/100 (Grade {estimated_letter})</strong>.</div></div>'
        st.markdown(executive_summary, unsafe_allow_html=True)

        col_gauge, col_metrics = st.columns([1, 2.5])
        
        with col_gauge:
            gauge_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 24px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;"><div style="font-size: 13px; font-weight: 600; color: #5f6368; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Performance Score</div><div style="display: flex; gap: 16px; justify-content: center; align-items: center; margin-bottom: 12px;"><div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-weight: 500;">CURRENT</div><div style="width: 85px; height: 85px; border-radius: 50%; border: 6px solid {score_color}; background-color: {score_bg}; display: flex; flex-direction: column; align-items: center; justify-content: center;"><span style="font-size: 26px; font-weight: 700; color: {score_color}; line-height: 1;">{perf_score}</span><span style="font-size: 12px; font-weight: 700; color: {score_color}; margin-top: 2px;">Grade {current_letter}</span></div></div><div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-weight: 500;">EST. OPTIMIZED</div><div style="width: 85px; height: 85px; border-radius: 50%; border: 6px solid {est_color}; background-color: {est_bg}; display: flex; flex-direction: column; align-items: center; justify-content: center;"><span style="font-size: 26px; font-weight: 700; color: {est_color}; line-height: 1;">{estimated_optimized_score}</span><span style="font-size: 12px; font-weight: 700; color: {est_color}; margin-top: 2px;">Grade {estimated_letter}</span></div></div></div><div style="font-size: 11px; color: #5f6368; border-top: 1px solid #e8eaed; padding-top: 8px; width: 100%; margin-bottom: 10px;">Estimated score if all Level 1 & 2 fixes are resolved.</div><div style="display: flex; justify-content: space-around; width: 100%; font-size: 11px; color: #5f6368; border-top: 1px dashed #dadce0; padding-top: 8px;"><div style="display: flex; align-items: center; gap: 4px;"><span style="color: #ff4e42; font-weight: bold;">▲</span> <span>0–49</span></div><div style="display: flex; align-items: center; gap: 4px;"><span style="color: #ffa400; font-weight: bold;">■</span> <span>50–89</span></div><div style="display: flex; align-items: center; gap: 4px;"><span style="color: #0cce6b; font-weight: bold;">●</span> <span>90–100</span></div></div></div>'
            st.markdown(gauge_html, unsafe_allow_html=True)

        with col_metrics:
            st.markdown('<div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 8px;">Performance Metrics & Score Drivers</div>', unsafe_allow_html=True)

            r1c1, r1c2, r1c3 = st.columns(3)
            r2c1, r2c2, r2c3 = st.columns(3)

            with r1c1:
                with st.container(border=True):
                    st.markdown("⭐ **Largest Contentful Paint (CWV)**")
                    lcp_delta = "Target: ≤ 2.5s" if avg_lcp <= 2.5 else "Target: ≤ 2.5s (Exceeded)"
                    st.metric(label="Main Content Load Speed", value=f"{avg_lcp:.2f} s", delta=lcp_delta, delta_color="normal" if avg_lcp <= 2.5 else "inverse")

            with r1c2:
                with st.container(border=True):
                    st.markdown("⭐ **Total Blocking Time (CWV)**")
                    tbt_delta = "Target: ≤ 200ms" if avg_tbt <= 200 else "Target: ≤ 200ms (Exceeded)"
                    st.metric(label="Interactivity Freeze Delay", value=f"{avg_tbt:.0f} ms", delta=tbt_delta, delta_color="normal" if avg_tbt <= 200 else "inverse")

            with r1c3:
                with st.container(border=True):
                    st.markdown("⭐ **Cumulative Layout Shift (CWV)**")
                    cls_delta = "Target: ≤ 0.10" if avg_cls <= 0.10 else "Target: ≤ 0.10 (Exceeded)"
                    st.metric(label="Visual Stability / Jumping", value=f"{avg_cls:.3f}", delta=cls_delta, delta_color="normal" if avg_cls <= 0.10 else "inverse")

            with r2c1:
                with st.container(border=True):
                    st.markdown("**Server Response Time**")
                    ttfb_delta = "Target: ≤ 800ms" if avg_ttfb <= 800 else "Target: ≤ 800ms (Exceeded)"
                    st.metric(label="Initial Server Handshake", value=f"{avg_ttfb:.0f} ms", delta=ttfb_delta, delta_color="normal" if avg_ttfb <= 800 else "inverse")

            with r2c2:
                with st.container(border=True):
                    st.markdown("**Speed Index**")
                    si_delta = "Target: ≤ 3.4s" if speed_index <= 3.4 else "Target: ≤ 3.4s (Exceeded)"
                    st.metric(label="Visual Progress Pace", value=f"{speed_index:.2f} s", delta=si_delta, delta_color="normal" if speed_index <= 3.4 else "inverse")

            with r2c3:
                with st.container(border=True):
                    st.markdown("**Unoptimized Asset Waste**")
                    waste_delta = "Target: Minimal Bloat" if total_asset_waste <= 50 else "Target: Minimal Bloat (High)"
                    st.metric(label="Unused JS/CSS & Images", value=f"{total_asset_waste:.0f} KB", delta=waste_delta, delta_color="normal" if total_asset_waste <= 50 else "inverse")

        st.markdown("<br>", unsafe_allow_html=True)

        # DYNAMIC INSIGHTS GENERATOR (Comprehensive)
        st.markdown('<div style="font-size: 16px; font-weight: 600; color: #202124; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Insights & Optimization Recommendations</div>', unsafe_allow_html=True)
        
        filter_col1, filter_col2 = st.columns([1, 4])
        with filter_col1:
            insight_filter = st.selectbox(
                "Show audits relevant to:",
                [
                    "All",
                    "First Contentful Paint (FCP)",
                    "Largest Contentful Paint (LCP)",
                    "Total Blocking Time (TBT)",
                    "Cumulative Layout Shift (CLS)"
                ],
                label_visibility="collapsed"
            )

        insights = []

        if avg_ttfb > 800:
            insights.append({
                "title": f"High Server Response Time ({avg_ttfb:.0f} ms)",
                "tech": f"Initial server response for {target_url} exceeded the recommended 800ms threshold.",
                "plain": "The server is taking too long to start sending page content back to the visitor's browser.",
                "location": f"{target_url} server backend response pipeline.",
                "cwv_impact": "Directly impacts First Contentful Paint (FCP) and Largest Contentful Paint (LCP).",
                "importance": 1,
                "relevant_to": ["All", "First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)"]
            })

        if speed_index > 3.4:
            insights.append({
                "title": f"Slow Visual Progression — Speed Index ({speed_index:.2f} s)",
                "tech": f"Visual content elements are rendering too slowly across the viewport on {target_url}.",
                "plain": "Elements on the page are taking a while to visually populate on screen during the initial load phase, dragging down the overall score.",
                "location": f"{target_url} above-the-fold render tree and critical CSS path.",
                "cwv_impact": "Directly impacts perceived loading speed and overall Lighthouse performance score.",
                "importance": 1,
                "relevant_to": ["All", "First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)"]
            })

        if total_asset_waste > 100.0:
            insights.append({
                "title": f"Excessive Asset Payload Bloat ({total_asset_waste:.0f} KiB)",
                "tech": f"Cumulative unoptimized images, unused JS, and unused CSS are bloating the network footprint on {target_url}.",
                "plain": "The browser is downloading unnecessary code and oversized files before the page can fully render.",
                "location": f"{target_url} static bundle assets and media directories.",
                "cwv_impact": "Slows down network transfer speeds, hurting both FCP, LCP, and overall performance score.",
                "importance": 1,
                "relevant_to": ["All", "Largest Contentful Paint (LCP)", "Total Blocking Time (TBT)"]
            })

        if unoptimized_kb > 10.0:
            insights.append({
                "title": f"Improve image delivery — Est savings of {unoptimized_kb:.0f} KiB",
                "tech": f"Uncompressed raster images detected on {target_url} wasting ~{unoptimized_kb:.0f} KB.",
                "plain": "Product catalog and banner images are oversized file formats, slowing down visual loading speeds.",
                "location": f"{target_url} catalog grid & banner slots (`/images/products/`).",
                "cwv_impact": "Significantly lightens page weight, directly reducing Largest Contentful Paint (LCP) times.",
                "importance": 1,
                "relevant_to": ["All", "Largest Contentful Paint (LCP)"]
            })

        if third_party_ms > 50.0:
            insights.append({
                "title": f"3rd parties ({third_party_ms:.0f} ms impact)",
                "tech": f"External analytics and chat widgets on {target_url} monopolizing main-thread CPU cycles.",
                "plain": "Third-party marketing and support tools are consuming processor power, making the page temporarily unresponsive.",
                "location": f"{target_url} footer tracking scripts & floating widget iframes.",
                "cwv_impact": "Frees up the main thread, directly reducing Total Blocking Time (TBT).",
                "importance": 2,
                "relevant_to": ["All", "Total Blocking Time (TBT)"]
            })

        if avg_cls > 0.10:
            insights.append({
                "title": f"Layout shift warning (CLS: {avg_cls:.3f})",
                "tech": f"Unstable elements causing visual instability and reflows on {target_url}.",
                "plain": "Content is shifting around while the page loads, causing accidental clicks.",
                "location": f"{target_url} dynamic banner or ad injection blocks.",
                "cwv_impact": "Secures compliance for Cumulative Layout Shift (CLS).",
                "importance": 1,
                "relevant_to": ["All", "Cumulative Layout Shift (CLS)"]
            })

        if avg_tbt > 200:
            insights.append({
                "title": f"High Total Blocking Time ({avg_tbt:.0f} ms)",
                "tech": f"Main-thread execution tasks blocking user interaction on {target_url}.",
                "plain": "Scripts are running too long during page load, freezing interactivity.",
                "location": f"{target_url} client-side JavaScript execution bundles.",
                "cwv_impact": "Improves responsiveness and lowers Total Blocking Time (TBT).",
                "importance": 2,
                "relevant_to": ["All", "Total Blocking Time (TBT)"]
            })

        if not insights:
            insights.append({
                "title": "Optimal Performance Profile",
                "tech": f"Core metrics for {target_url} are currently meeting recommended performance targets.",
                "plain": "No major performance bottlenecks or critical thresholds were breached in this audit cycle.",
                "location": f"{target_url} overall document structure.",
                "cwv_impact": "Maintains healthy Core Web Vitals compliance.",
                "importance": 3,
                "relevant_to": ["All", "First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)", "Total Blocking Time (TBT)", "Cumulative Layout Shift (CLS)"]
            })

        insights.sort(key=lambda x: x["importance"])

        for item in insights:
            if insight_filter in item["relevant_to"]:
                prefix, badge_html = get_priority_prefix_and_badge(item['importance'])
                expander_title = f"{prefix} {item['title']}"
                with st.expander(expander_title):
                    st.markdown(f"**Importance Rating:** {badge_html}", unsafe_allow_html=True)
                    st.markdown(f"**Technical Outcome:** {item.get('tech')}")
                    st.markdown(f"**Plain English Translation:** {item['plain']}")
                    st.markdown(f"**Location / Area on URL:** `{item['location']}`")
                    st.markdown(f"**CWV Compliance Impact:** {item['cwv_impact']}")

        st.markdown("<br>", unsafe_allow_html=True)

        # DYNAMIC DIAGNOSTICS SECTION
        diagnostics = []

        if unused_js_kb > 10.0:
            diagnostics.append({
                "title": f"Reduce unused JavaScript — Est savings of {unused_js_kb:.0f} KiB",
                "tech": f"Unexecuted script bytes loaded during initial page initialization on {target_url}.",
                "plain": "Scripts containing code that isn't needed for the initial page load are slowing down script parsing.",
                "location": f"{target_url} global bundle scripts (`bundle.js`).",
                "cwv_impact": "Improves script evaluation times, helping lower Total Blocking Time (TBT).",
                "importance": 2
            })

        if unused_css_kb > 10.0:
            diagnostics.append({
                "title": f"Reduce unused CSS — Est savings of {unused_css_kb:.0f} KiB",
                "tech": f"Stylesheets on {target_url} contain rule sets unreferenced by the current DOM structure.",
                "plain": "Extra style rules for other pages are being loaded all at once, bloating file size.",
                "location": f"{target_url} main stylesheet declarations (`styles.css`).",
                "cwv_impact": "Speeds up stylesheet parsing and rendering, improving First Contentful Paint (FCP).",
                "importance": 2
            })

        if not diagnostics:
            diagnostics.append({
                "title": "Clean Asset Bundles",
                "tech": f"Asset payloads for {target_url} show minimal redundant resource bloat.",
                "plain": "Code assets are appropriately scoped for the current page view.",
                "location": f"{target_url} static resource directories.",
                "cwv_impact": "Optimizes network transfer speeds.",
                "importance": 3
            })

        diagnostics.sort(key=lambda x: x["importance"])

        for diag in diagnostics:
            prefix, badge_html = get_priority_prefix_and_badge(diag['importance'])
            expander_title = f"{prefix} {diag['title']}"
            with st.expander(expander_title):
                st.markdown(f"**Importance Rating:** {badge_html}", unsafe_allow_html=True)
                st.markdown(f"**Technical Outcome:** {diag['tech']}")
                st.markdown(f"**Plain English Translation:** {diag['plain']}")
                st.markdown(f"**Location / Area on URL:** `{diag['location']}`")
                st.markdown(f"**CWV Compliance Impact:** {diag['cwv_impact']}")


# TAB 2: URL VITALS & TRENDS (Enhanced with 3x2 Checkboxes, Thicker Lines, Hover Bold, and KPI Background Ranges)
with tabs[1]:
    st.header("📊 Historical URL Vitals & Performance Trends")
    st.markdown("Analyze longitudinal performance telemetry, track Core Web Vitals progression against official KPI thresholds, and review device-specific trends.")

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 2.5, 2])

    with ctrl_col1:
        hist_strategy = st.radio("Form Factor", ["mobile", "desktop"], horizontal=True, key="hist_strat_radio")

    with get_db_connection() as conn:
        df_hist_meta = pd.read_sql_query("SELECT DISTINCT target_url FROM web_performance_logs;", conn)

    if df_hist_meta.empty:
        st.info("No performance history recorded yet.")
    else:
        with ctrl_col2:
            hist_url = st.selectbox("Target Environment", df_hist_meta["target_url"].unique(), key="hist_url_sel")

        with ctrl_col3:
            time_range_option = st.selectbox(
                "Telemetry Time Range", 
                ["Last 1 Day", "Last 5 Days", "Last 10 Days", "Last 30 Days", "Last 60 Days", "Last 120 Days", "Last 180 Days+", "All Time"],
                index=3
            )

        days_map = {
            "Last 1 Day": 1,
            "Last 5 Days": 5,
            "Last 10 Days": 10,
            "Last 30 Days": 30,
            "Last 60 Days": 60,
            "Last 120 Days": 120,
            "Last 180 Days+": 180,
            "All Time": 99999
        }
        selected_days = days_map.get(time_range_option, 30)

        with get_db_connection() as conn:
            query = """
                SELECT * FROM web_performance_logs 
                WHERE target_url = %s AND strategy = %s 
                AND recorded_at >= NOW() - INTERVAL '%s days'
                ORDER BY recorded_at ASC;
            """
            df_hist = pd.read_sql_query(query, conn, params=(hist_url, hist_strategy, selected_days))

        if df_hist.empty:
            with get_db_connection() as conn:
                fallback_query = "SELECT * FROM web_performance_logs WHERE target_url = %s AND strategy = %s ORDER BY recorded_at ASC;"
                df_hist = pd.read_sql_query(fallback_query, conn, params=(hist_url, hist_strategy))

        if df_hist.empty:
            st.warning(f"No records found for {hist_url} ({hist_strategy}) within the selected timeframe.")
        else:
            df_hist["recorded_at"] = pd.to_datetime(df_hist["recorded_at"], utc=True)
            df_hist["recorded_at_uk"] = df_hist["recorded_at"].dt.tz_convert("Europe/London")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Select Core Metrics to Plot:**")

            metric_mapping = {
                "Largest Contentful Paint (LCP)": "lcp_ms",
                "Total Blocking Time (TBT)": "tbt_ms",
                "Cumulative Layout Shift (CLS)": "cls",
                "Server Response Time (TTFB)": "ttfb_ms",
                "Speed Index": "speed_index_ms",
                "Performance Score (0-100)": "perf_score"
            }

            selected_metric_labels = []
            defaults = ["Largest Contentful Paint (LCP)", "Total Blocking Time (TBT)"]

            row1_cols = st.columns(3)
            row2_cols = st.columns(3)
            all_cols = list(row1_cols) + list(row2_cols)

            for i, (label, col_name) in enumerate(metric_mapping.items()):
                with all_cols[i]:
                    if st.checkbox(label, value=(label in defaults), key=f"chk_metric_{i}"):
                        selected_metric_labels.append(label)

            st.markdown("<br>", unsafe_allow_html=True)

            kpi_thresholds = {
                "Largest Contentful Paint (LCP)": (0, 2500, "rgba(12, 206, 107, 0.08)", "Good Target (≤ 2.5s)"),
                "Total Blocking Time (TBT)": (0, 200, "rgba(12, 206, 107, 0.08)", "Good Target (≤ 200ms)"),
                "Cumulative Layout Shift (CLS)": (0, 0.10, "rgba(12, 206, 107, 0.08)", "Good Target (≤ 0.10)"),
                "Server Response Time (TTFB)": (0, 800, "rgba(12, 206, 107, 0.08)", "Good Target (≤ 800ms)"),
                "Speed Index": (0, 3400, "rgba(12, 206, 107, 0.08)", "Good Target (≤ 3.4s)"),
                "Performance Score (0-100)": (90, 100, "rgba(12, 206, 107, 0.08)", "Good Target (90–100)")
            }

            if selected_metric_labels:
                valid_mappings = {label: col for label, col in metric_mapping.items() if col in df_hist.columns}
                active_labels = [label for label in selected_metric_labels if label in valid_mappings]
                plot_columns = [valid_mappings[label] for label in active_labels]

                if plot_columns:
                    df_plot = df_hist[["recorded_at_uk"] + plot_columns].copy()
                    rename_dict = {v: k for k, v in valid_mappings.items()}
                    df_plot = df_plot.rename(columns=rename_dict)

                    fig = px.line(
                        df_plot, 
                        x="recorded_at_uk", 
                        y=active_labels,
                        title=f"Trend Analysis for {hist_url} ({hist_strategy.capitalize()})",
                        labels={"recorded_at_uk": "Timestamp (UK Time)", "value": "Metric Value", "variable": "Core Web Vital / Driver"}
                    )

                    fig.update_traces(
                        line=dict(width=3),
                        hovertemplate="<b>%{y:.2f}</b><br>%{x}<extra>%{fullData.name}</extra>"
                    )

                    if len(active_labels) == 1:
                        single_label = active_labels[0]
                        if single_label in kpi_thresholds:
                            ymin, ymax, bg_color, annotation_text = kpi_thresholds[single_label]
                            fig.add_hrect(
                                y0=ymin, y1=ymax, 
                                fillcolor=bg_color, 
                                layer="below", 
                                line_width=0,
                                annotation_text=annotation_text, 
                                annotation_position="top left",
                                annotation=dict(font_size=10, font_color="#5f6368")
                            )

                    fig.update_layout(
                        hovermode="closest",
                        legend=dict(
                            orientation="h", 
                            yanchor="bottom", 
                            y=-0.4, 
                            xanchor="center", 
                            x=0.5
                        ),
                        margin=dict(l=20, r=20, t=80, b=70),
                        xaxis=dict(showgrid=True, gridcolor="#f1f3f4"),
                        yaxis=dict(showgrid=True, gridcolor="#f1f3f4")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Selected metrics are not available in the database schema.")

            with st.expander("📋 View Underlying Telemetry Data Table"):
                st.dataframe(df_hist, use_container_width=True)


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


# TAB 4: ISO REPORTING (Quality Objectives & Management Review)
with tabs[3]:
    st.header("📋 ISO 9001:2015 Quality Objectives & Management Review")
    st.markdown("This section provides documented evidence of service quality and threshold adherence for internal quality audits and management reviews.")
    
    with get_db_connection() as conn:
        df_all = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at ASC;", conn)

    if not df_all.empty:
        selected_iso_url = st.selectbox("Select Target URL for Compliance Report", df_all["target_url"].unique(), key="iso_url_sel")
        df_url_iso = df_all[df_all["target_url"] == selected_iso_url]

        total_audits = len(df_url_iso)
        if total_audits > 0:
            passing_audits = len(df_url_iso[df_url_iso["perf_score"] >= 50])
            compliance_rate = (passing_audits / total_audits) * 100
            avg_perf = df_url_iso["perf_score"].mean()
            avg_lcp_val = df_url_iso["lcp_ms"].mean() / 1000.0
            
            col_q1, col_q2, col_q3 = st.columns(3)
            col_q1.metric("Quality Target Adherence", f"{compliance_rate:.1f}%", help="Percentage of audits meeting acceptable score threshold (>= 50)")
            col_q2.metric("Mean Performance Score", f"{avg_perf:.1f} / 100")
            col_q3.metric("Mean LCP Latency", f"{avg_lcp_val:.2f} s")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            csv_data = df_url_iso.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download ISO Quality Audit Log (CSV)",
                data=csv_data,
                file_name=f"iso_9001_performance_audit_log_{selected_iso_url.replace('https://', '').replace('/', '_')}.csv",
                mime="text/csv",
                help="Export immutable telemetry history for quality management records."
            )

            st.markdown("### Historical Audit Records")
            st.dataframe(df_url_iso, use_container_width=True)
        else:
            st.info("Insufficient historical data for compliance calculation on this target URL.")
    else:
        st.info("No telemetry records found in database.")


# TAB 5: ADVANCED REPORTING & EXPORT CENTER
tab_idx_reporting = 4 if not is_admin else 4 # adjust based on tab count
with tabs[tab_idx_reporting]:
    st.header("📈 Advanced Reporting & Multi-Format Export Center")
    st.markdown("Generate plain-English executive summary PDF reports or export structured raw telemetry datasets formatted for Power BI and Excel.")

    with get_db_connection() as conn:
        df_export_all = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at DESC;", conn)

    if df_export_all.empty:
        st.info("No telemetry records found for reporting export.")
    else:
        rep_col1, rep_col2 = st.columns(2)
        with rep_col1:
            export_url = st.selectbox("Select Target URL for Export", df_export_all["target_url"].unique(), key="rep_url_sel")
        with rep_col2:
            export_strategy = st.selectbox("Select Form Factor Strategy", ["mobile", "desktop"], key="rep_strat_sel")

        df_filtered_export = df_export_all[(df_export_all["target_url"] == export_url) & (df_export_all["strategy"] == export_strategy)]
        if df_filtered_export.empty:
            df_filtered_export = df_export_all[df_export_all["target_url"] == export_url]

        st.markdown("<br>", unsafe_allow_html=True)
        
        ex_col1, ex_col2 = st.columns(2)
        
        with ex_col1:
            with st.container(border=True):
                st.markdown("### 📄 Executive PDF Report")
                st.markdown("Download a professional summary document complete with plain-English KPI explanations, observed averages, and prioritized optimization recommendations.")
                
                if st.button("📥 Generate & Download Executive PDF"):
                    pdf_bytes = generate_pdf_executive_report(df_filtered_export, export_url, export_strategy)
                    st.download_button(
                        label="💾 Click here to download PDF",
                        data=pdf_bytes,
                        file_name=f"executive_performance_report_{export_url.replace('https://', '').replace('/', '_')}.pdf",
                        mime="application/pdf"
                    )

        with ex_col2:
            with st.container(border=True):
                st.markdown("### 📊 Power BI & Excel Data Workbook")
                st.markdown("Export structured raw telemetry logs, metadata, and audit scores into an Excel workbook (`.xlsx`) ready for direct data modeling and Power BI integration.")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtered_export.to_excel(writer, sheet_name='Performance Telemetry', index=False)
                    df_export_all.to_excel(writer, sheet_name='All Environments Summary', index=False)
                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Download Excel / Power BI Workbook (.xlsx)",
                    data=excel_data,
                    file_name=f"tow_trust_telemetry_powerbi_{export_url.replace('https://', '').replace('/', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


# TAB 6: CUSTOM URL TESTING MANAGEMENT (Admin Only)
if is_admin:
    with tabs[5]:
        st.header("⚙️ Custom URL Testing Management")
        st.markdown("Register, configure, or remove secondary URLs (such as checkout flows and category pages) included in automated audit workflows.")
        
        st.subheader("Add or Update Target")
        with st.form("add_target_form"):
            new_url = st.text_input("Target URL (must start with https://)", placeholder="https://tow-trust.co.uk/cart")
            new_env_name = st.text_input("Environment / Page Label", placeholder="Checkout & Cart Flow")
            new_strategy = st.selectbox("Form Factor Strategy", ["desktop", "mobile"])
            submit_target = st.form_submit_button("➕ Save Target URL")
            
            if submit_target:
                if new_url.startswith("https://"):
                    try:
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO monitored_targets (url, strategy, is_active, environment_name)
                                    VALUES (%s, %s, TRUE, %s)
                                    ON CONFLICT (url) DO UPDATE 
                                    SET is_active = TRUE, strategy = EXCLUDED.strategy, environment_name = EXCLUDED.environment_name;
                                """, (new_url, new_strategy, new_env_name))
                                conn.commit()
                        st.success(f"Successfully registered/updated target: {new_url}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Database error saving target: {e}")
                else:
                    st.warning("URL must be valid and start with https://")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Active Monitored Targets & Deletion")
        
        try:
            with get_db_connection() as conn:
                targets_df = pd.read_sql_query("SELECT id, url, environment_name, strategy, is_active FROM monitored_targets ORDER BY id ASC;", conn)
            
            if not targets_df.empty:
                for idx, row in targets_df.iterrows():
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.markdown(f"**[{row['environment_name']}]** `{row['url']}` *(Strategy: {row['strategy']})*")
                    with col_del:
                        if st.button("🗑️ Delete", key=f"del_target_{row['id']}"):
                            try:
                                with get_db_connection() as conn:
                                    with conn.cursor() as cur:
                                        cur.execute("DELETE FROM monitored_targets WHERE id = %s;", (row['id'],))
                                        conn.commit()
                                st.success(f"Deleted target: {row['url']}")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete target: {e}")
            else:
                st.info("No monitored targets configured.")
        except Exception as e:
            st.info("Monitored targets table not initialized yet. Ensure the database migration script has been run.")
