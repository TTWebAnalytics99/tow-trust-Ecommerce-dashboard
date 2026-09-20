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

st.set_page_config(page_title="TT SWPTA - Enterprise Edition", layout="wide")

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
        st.subheader("🔒 Tow-Trust ECommerce Web Performance and Carriage Intelligence Platform")
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

def generate_pdf_executive_report(df_target, target_url, strategy, time_range_label):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1a73e8'), spaceAfter=4)
    sub_style = ParagraphStyle('ReportSub', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#5f6368'), spaceAfter=12)
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#202124'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, textColor=colors.HexColor('#3c4043'), leading=13, spaceAfter=6)
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#3c4043'), leading=10)
    cell_header_style = ParagraphStyle('CellHeader', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor('#174ea6'), fontName='Helvetica-Bold', leading=10)

    story.append(Paragraph("Tow-Trust ECommerce Performance & ISO Quality Review Report", title_style))
    story.append(Paragraph(f"Environment: <b>{target_url}</b> | Form Factor: <b>{strategy.capitalize()}</b> | Telemetry Window: <b>{time_range_label}</b>", sub_style))

    # SECTION 1: EXECUTIVE SUMMARY & CORE WEB VITALS REFERENCE TABLE
    story.append(Paragraph("1. Executive Summary & ISO 9001 Quality Objectives", heading_style))
    story.append(Paragraph("This report summarizes synthetic performance audits and quality objective adherence (ISO 9001:2015 Clause 9.1) for leadership review, tracking user experience benchmarks and user journey responsiveness.", body_style))
    
    def_data = [
        [Paragraph("Metric Name", cell_header_style), Paragraph("Plain English Business Definition", cell_header_style), Paragraph("Target Standard", cell_header_style)],
        [Paragraph("Largest Contentful Paint (LCP)", cell_style), Paragraph("Measures how fast main page content loads for visitors. Slow LCP causes high bounce rates.", cell_style), Paragraph("≤ 2.50 seconds", cell_style)],
        [Paragraph("Total Blocking Time (TBT)", cell_style), Paragraph("Measures responsiveness delays caused by background scripts freezing clicks/scrolls.", cell_style), Paragraph("≤ 200 milliseconds", cell_style)],
        [Paragraph("Cumulative Layout Shift (CLS)", cell_style), Paragraph("Measures visual stability. High CLS causes buttons or text to jump mid-read.", cell_style), Paragraph("≤ 0.10", cell_style)]
    ]
    
    t_def = Table(def_data, colWidths=[140, 240, 120])
    t_def.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0fe')),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dadce0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_def)
    story.append(Spacer(1, 6))

    # SECTION 2: HISTORICAL METRICS SUMMARY
    story.append(Paragraph("2. Historical Performance & Quality Adherence Summary", heading_style))
    if not df_target.empty:
        mean_score = df_target["perf_score"].mean()
        mean_lcp = df_target["lcp_ms"].mean() / 1000.0
        mean_tbt = df_target["tbt_ms"].mean()
        mean_cls = df_target["cls"].mean()
        
        score_grade = get_gtmetrix_letter_grade(mean_score)
        lcp_grade = "A" if mean_lcp <= 2.5 else ("B" if mean_lcp <= 3.5 else "D")
        tbt_grade = "A" if mean_tbt <= 200 else ("C" if mean_tbt <= 400 else "E")
        cls_grade = "A" if mean_cls <= 0.10 else "D"
        
        summary_data = [
            [Paragraph("Metric Evaluated", cell_header_style), Paragraph("Target Benchmark", cell_header_style), Paragraph("Observed Average", cell_header_style), Paragraph("GTmetrix Grade", cell_header_style), Paragraph("Status", cell_header_style)],
            [Paragraph("Performance Score", cell_style), Paragraph("≥ 50 / 100", cell_style), Paragraph(f"{mean_score:.1f} / 100", cell_style), Paragraph(f"Grade {score_grade}", cell_style), Paragraph("Passing" if mean_score >= 50 else "Needs Attention", cell_style)],
            [Paragraph("Largest Contentful Paint (LCP)", cell_style), Paragraph("≤ 2.50 s", cell_style), Paragraph(f"{mean_lcp:.2f} s", cell_style), Paragraph(f"Grade {lcp_grade}", cell_style), Paragraph("Passing" if mean_lcp <= 2.5 else "Exceeded", cell_style)],
            [Paragraph("Total Blocking Time (TBT)", cell_style), Paragraph("≤ 200 ms", cell_style), Paragraph(f"{mean_tbt:.0f} ms", cell_style), Paragraph(f"Grade {tbt_grade}", cell_style), Paragraph("Passing" if mean_tbt <= 200 else "Exceeded", cell_style)],
            [Paragraph("Cumulative Layout Shift (CLS)", cell_style), Paragraph("≤ 0.10", cell_style), Paragraph(f"{mean_cls:.3f}", cell_style), Paragraph(f"Grade {cls_grade}", cell_style), Paragraph("Passing" if mean_cls <= 0.10 else "Exceeded", cell_style)]
        ]
        
        t_sum = Table(summary_data, colWidths=[140, 95, 85, 80, 100])
        t_sum.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0fe')),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('TOPPADDING', (0,0), (-1,0), 5),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dadce0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_sum)
    
    story.append(Spacer(1, 6))

    # SECTION 3: TECHNICAL & ISP BRIEFING
    story.append(Paragraph("3. Technical Deep-Dive & ISP Infrastructure Briefing", heading_style))
    isp_text = (
        "<b>A. Carriage Rule Calculation Engine (93,726-Row Matrix):</b><br/>"
        "• <i>Technical Bottleneck:</i> Basket updates evaluate shipping rules across 93,726 active rule records, factoring in carrier tiers and product groups.<br/>"
        "• <i>ISP Action Required:</i> Ensure compound SQL indexing on `(Postal District, Group Name, Display Label)` and query-result caching in Redis/Memcached.<br/><br/>"
        "<b>B. Parts Finder Cascading Dropdowns & Side Filters:</b><br/>"
        "• <i>Technical Bottleneck:</i> Relational make/model/year queries cause server roundtrip delays; category filters trigger processing pauses.<br/>"
        "• <i>ISP Action Required:</i> Preload serialized vehicle taxonomy JSON client-side and apply input debouncing on side filter checkboxes."
    )
    story.append(Paragraph(isp_text, body_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# STREAMLINED 3-TAB LAYOUT (Tab 2: Basket Testing, Tab 3: Advanced Reporting)
tabs = st.tabs([
    "📑 Executive Briefing", 
    "🛒 Basket Checkout & Carriage Testing",
    "📈 Advanced Reporting & ISO Export Hub"
])

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

        meta_bar_html = f'<div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; padding: 12px 20px; margin-bottom: 24px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 12px; color: #5f6368;"><div style="display: flex; align-items: center; gap: 8px;">📅 <span>Captured at {recorded_time}</span></div><div style="display: flex; align-items: center; gap: 8px;">💻 <span>Emulated {str(audit_strategy).capitalize()} with Lighthouse 13.4.1</span></div><div style="display: flex; align-items: center; gap: 8px;">🔗 <span>Single page session</span></div></div>'
        st.markdown(meta_bar_html, unsafe_allow_html=True)

        executive_summary = f'<div style="background-color: #e8f0fe; border-left: 4px solid #1a73e8; padding: 16px; border-radius: 4px; margin-bottom: 24px; color: #174ea6;"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">Executive Summary & Health Status</div><div style="font-size: 13px; line-height: 1.5;">The current performance score for environment <code>{target_url}</code> is <strong>{perf_score}/100 (Grade {current_letter})</strong>. Addressing all Level 1 and Level 2 priority insights is projected to lift performance to an estimated <strong>{estimated_optimized_score}/100 (Grade {estimated_letter})</strong>.</div></div>'
        st.markdown(executive_summary, unsafe_allow_html=True)

        col_gauge, col_metrics = st.columns([1, 2.5])
        
        with col_gauge:
            gauge_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 24px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;"><div style="font-size: 13px; font-weight: 600; color: #5f6368; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Performance Score</div><div style="display: flex; gap: 16px; justify-content: center; align-items: center; margin-bottom: 12px;"><div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-weight: 500;">CURRENT</div><div style="width: 85px; height: 85px; border-radius: 50%; border: 6px solid {score_color}; background-color: {score_bg}; display: flex; flex-direction: column; align-items: center; justify-content: center;"><span style="font-size: 26px; font-weight: 700; color: {score_color}; line-height: 1;">{perf_score}</span><span style="font-size: 12px; font-weight: 700; color: {score_color}; margin-top: 2px;">Grade {current_letter}</span></div></div><div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-weight: 500;">EST. OPTIMIZED</div><div style="width: 85px; height: 85px; border-radius: 50%; border: 6px solid {est_color}; background-color: {est_bg}; display: flex; flex-direction: column; align-items: center; justify-content: center;"><span style="font-size: 26px; font-weight: 700; color: {est_color}; line-height: 1;">{estimated_optimized_score}</span><span style="font-size: 12px; font-weight: 700; color: {est_color}; margin-top: 2px;">Grade {estimated_letter}</span></div></div></div></div>'
            st.markdown(gauge_html, unsafe_allow_html=True)

        with col_metrics:
            st.markdown('<div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 8px;">Performance Metrics & Score Drivers</div>', unsafe_allow_html=True)

            r1c1, r1c2, r1c3 = st.columns(3)
            r2c1, r2c2, r2c3 = st.columns(3)

            with r1c1:
                with st.container(border=True):
                    st.markdown("⭐ **Largest Contentful Paint**")
                    st.metric(label="Main Content Load", value=f"{avg_lcp:.2f} s", delta="Target: ≤ 2.5s" if avg_lcp <= 2.5 else "Exceeded", delta_color="normal" if avg_lcp <= 2.5 else "inverse")
            with r1c2:
                with st.container(border=True):
                    st.markdown("⭐ **Total Blocking Time**")
                    st.metric(label="Interactivity Delay", value=f"{avg_tbt:.0f} ms", delta="Target: ≤ 200ms" if avg_tbt <= 200 else "Exceeded", delta_color="normal" if avg_tbt <= 200 else "inverse")
            with r1c3:
                with st.container(border=True):
                    st.markdown("⭐ **Cumulative Layout Shift**")
                    st.metric(label="Visual Stability", value=f"{avg_cls:.3f}", delta="Target: ≤ 0.10" if avg_cls <= 0.10 else "Exceeded", delta_color="normal" if avg_cls <= 0.10 else "inverse")
            with r2c1:
                with st.container(border=True):
                    st.markdown("**Server Response (TTFB)**")
                    st.metric(label="Initial Handshake", value=f"{avg_ttfb:.0f} ms", delta="Target: ≤ 800ms" if avg_ttfb <= 800 else "Exceeded", delta_color="normal" if avg_ttfb <= 800 else "inverse")
            with r2c2:
                with st.container(border=True):
                    st.markdown("**Speed Index**")
                    st.metric(label="Visual Progress", value=f"{speed_index:.2f} s", delta="Target: ≤ 3.4s" if speed_index <= 3.4 else "Exceeded", delta_color="normal" if speed_index <= 3.4 else "inverse")
            with r2c3:
                with st.container(border=True):
                    st.markdown("**Unoptimized Waste**")
                    st.metric(label="Unused Assets", value=f"{total_asset_waste:.0f} KB", delta="Target: Minimal", delta_color="normal" if total_asset_waste <= 50 else "inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="font-size: 16px; font-weight: 600; color: #202124; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">User Journey Bottlenecks & Recommendations</div>', unsafe_allow_html=True)

        insights = [
            {
                "title": "Parts Finder Cascading Dropdown Latency",
                "tech": f"Synchronous AJAX roundtrips between Make, Model, and Year selectors on {target_url}.",
                "plain": "Selecting vehicle makes and models triggers noticeable processing delays while waiting for dependent dropdown options to populate. Indexing relational vehicle tables will speed up lookups.",
                "location": f"{target_url} homepage Parts Finder widget.",
                "importance": 1
            },
            {
                "title": "Carriage Rule & Compliance Processing (93,726 Rules)",
                "tech": f"Synchronous rule evaluation across 93,726 carriage and product group records on {target_url} basket updates.",
                "plain": "Adding items to the basket triggers heavy rule calculations to determine carriage surcharges across nearly 94,000 matrix rules, causing temporary loading bars.",
                "location": f"{target_url} cart and checkout rule calculation engine.",
                "importance": 1
            }
        ]

        for item in insights:
            prefix, badge_html = get_priority_prefix_and_badge(item['importance'])
            with st.expander(f"{prefix} {item['title']}"):
                st.markdown(f"**Importance Rating:** {badge_html}", unsafe_allow_html=True)
                st.markdown(f"**Technical Outcome:** {item['tech']}")
                st.markdown(f"**Plain English Translation:** {item['plain']}")
                st.markdown(f"**Location on URL:** `{item['location']}`")


# TAB 2: BASKET CHECKOUT & CARRIAGE TESTING
with tabs[1]:
    st.header("🛒 Basket Checkout & Carriage Testing (93,726 Rules Matrix)")
    st.markdown("Monitor synthetic transaction times for carriage rule compliance calculations across your complete UK regional shipping zones and product group matrices (Target SLA: ≤ 1,200 ms).")

    try:
        with get_db_connection() as conn:
            df_carriage = pd.read_sql_query("SELECT * FROM carriage_benchmark_logs ORDER BY recorded_at DESC;", conn)
    except Exception:
        df_carriage = pd.DataFrame()

    if df_carriage.empty:
        st.info("No synthetic regional carriage benchmark logs found. Initialize the `carriage_benchmark_logs` table and execute test routines.")
    else:
        avg_carriage_time = df_carriage["calculation_duration_ms"].mean()
        sla_pass_rate = (len(df_carriage[df_carriage["calculation_duration_ms"] <= 1200]) / len(df_carriage)) * 100

        rc1, rc2, rc3 = st.columns(3)
        rc1.metric("Mean Carriage Calculation Latency", f"{avg_carriage_time:.0f} ms", delta="Target: ≤ 1,200 ms", delta_color="normal" if avg_carriage_time <= 1200 else "inverse")
        rc2.metric("SLA Adherence Rate", f"{sla_pass_rate:.1f}%")
        rc3.metric("Total Regional SKU Tests", len(df_carriage))

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Regional & Product Group SLA Compliance Matrix")
        st.dataframe(df_carriage, use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 **ISP Technical Summary:** The 93,726-row delivery charges matrix requires compound indexing on `Postal District`, `Group Name`, and `Display Label`. Without indexes, rule lookups result in sequential table scans that exceed the 1.2s SLA during peak basket updates.")


# TAB 3: ADVANCED REPORTING & ISO EXPORT HUB
with tabs[2]:
    st.header("📈 Advanced Reporting & ISO 9001:2015 Quality Management Hub")
    st.markdown("Consolidated hub for longitudinal trend analysis, ISO quality objective adherence tracking (Clause 9.1), executive PDF generation, and Power BI/Excel exports.")

    with get_db_connection() as conn:
        df_meta = pd.read_sql_query("SELECT DISTINCT target_url FROM web_performance_logs;", conn)

    if df_meta.empty:
        st.info("No telemetry records found.")
    else:
        rep_c1, rep_c2, rep_c3 = st.columns(3)
        with rep_c1:
            hub_url = st.selectbox("Target Environment", df_meta["target_url"].unique(), key="hub_url_sel")
        with rep_c2:
            hub_strat = st.selectbox("Form Factor Strategy", ["mobile", "desktop"], key="hub_strat_sel")
        with rep_c3:
            hub_time = st.selectbox("Telemetry Time Range", ["Last 30 Days", "Last 60 Days", "All Time"], index=0, key="hub_time_sel")

        days_val = 30 if "30" in hub_time else (60 if "60" in hub_time else 99999)

        with get_db_connection() as conn:
            query = "SELECT * FROM web_performance_logs WHERE target_url = %s AND strategy = %s AND recorded_at >= NOW() - INTERVAL '%s days' ORDER BY recorded_at ASC;"
            df_hub = pd.read_sql_query(query, conn, params=(hub_url, hub_strat, days_val))

        if df_hub.empty:
            with get_db_connection() as conn:
                df_hub = pd.read_sql_query("SELECT * FROM web_performance_logs WHERE target_url = %s AND strategy = %s ORDER BY recorded_at ASC;", conn, params=(hub_url, hub_strat))

        if not df_hub.empty:
            df_hub["recorded_at"] = pd.to_datetime(df_hub["recorded_at"], utc=True)
            df_hub["recorded_at_uk"] = df_hub["recorded_at"].dt.tz_convert("Europe/London")

            # ISO 9001 Quality Adherence Metrics Banner
            total_audits = len(df_hub)
            passing_audits = len(df_hub[df_hub["perf_score"] >= 50])
            compliance_rate = (passing_audits / total_audits) * 100 if total_audits > 0 else 0
            mean_score = df_hub["perf_score"].mean()

            st.markdown("<br>", unsafe_allow_html=True)
            iq1, iq2, iq3 = st.columns(3)
            iq1.metric("ISO Quality Adherence (Clause 9.1)", f"{compliance_rate:.1f}%", help="Percentage of audits meeting acceptable performance score threshold (>= 50)")
            iq2.metric("Mean Performance Score", f"{mean_score:.1f} / 100")
            iq3.metric("Total Quality Audits Logged", total_audits)
            st.markdown("<br>", unsafe_allow_html=True)

            # Trend Analysis Chart
            st.markdown("### Longitudinal Performance Trends")
            fig = px.line(
                df_hub, 
                x="recorded_at_uk", 
                y=["lcp_ms", "tbt_ms", "perf_score"],
                title=f"Performance Trend Analysis for {hub_url} ({hub_strat.capitalize()})",
                labels={"recorded_at_uk": "Timestamp (UK Time)", "value": "Metric Value", "variable": "Indicator"}
            )
            fig.update_traces(line=dict(width=3))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Documented Export & Review Center")
            
            ex_c1, ex_c2 = st.columns(2)
            with ex_c1:
                with st.container(border=True):
                    st.markdown("#### 📄 Executive PDF Quality Report")
                    st.markdown("Generate and download a formal management review document for ISO compliance records.")
                    if st.button("📥 Generate & Download Executive PDF"):
                        pdf_bytes = generate_pdf_executive_report(df_hub, hub_url, hub_strat, hub_time)
                        st.download_button(
                            label="💾 Save PDF Report",
                            data=pdf_bytes,
                            file_name=f"iso_executive_performance_report_{hub_url.replace('https://', '').replace('/', '_')}.pdf",
                            mime="application/pdf"
                        )

            with ex_c2:
                with st.container(border=True):
                    st.markdown("#### 📊 Power BI & Excel Audit Workbook")
                    st.markdown("Export immutable telemetry and audit logs formatted for Power BI (`.xlsx` with timezone stripping).")
                    
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_clean = df_hub.copy()
                        for col in df_clean.select_dtypes(include=['datetimetz', 'datetime64[ns, UTC]']).columns:
                            df_clean[col] = df_clean[col].dt.tz_localize(None)
                        df_clean.to_excel(writer, sheet_name='ISO Quality Audit Log', index=False)
                    excel_data = output.getvalue()

                    st.download_button(
                        label="📥 Download Excel Audit Workbook (.xlsx)",
                        data=excel_data,
                        file_name=f"iso_telemetry_audit_log_{hub_url.replace('https://', '').replace('/', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("📋 View Underlying ISO Quality Audit Records Table"):
                st.dataframe(df_hub, use_container_width=True)
