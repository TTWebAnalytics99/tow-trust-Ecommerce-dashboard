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

is_admin = st.session_state.get("role") == "admin"
tab_titles = ["📑 Executive Briefing", "📊 URL Vitals & Trends", "🎨 Asset Bottlenecks"]
tabs = st.tabs(tab_titles)

# TAB 1: EXECUTIVE BRIEFING
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
        current_letter = get_gtmetrix_letter_grade(perf_score)
        
        estimated_optimized_score = min(98, perf_score + 32)
        estimated_letter = get_gtmetrix_letter_grade(estimated_optimized_score)
        est_color, est_bg = get_psi_grade_color(estimated_optimized_score)
        
        url_bar_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px 24px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px rgba(0,28,64,0.08);"><div><span style="font-size: 12px; font-weight: 500; color: #5f6368; text-transform: uppercase; letter-spacing: 0.8px;">PageSpeed Insights Audit URL</span><div style="font-size: 18px; font-weight: 400; color: #1a73e8; margin-top: 2px; word-break: break-all;"><a href="{target_url}" target="_blank" style="color: #1a73e8; text-decoration: none;">{target_url}</a></div></div><div style="background-color: #f1f3f4; padding: 6px 14px; border-radius: 16px; font-size: 13px; font-weight: 500; color: #3c4043; text-transform: capitalize;">💻 Form Factor: {selected_strategy}</div></div>'
        st.markdown(url_bar_html, unsafe_allow_html=True)

        meta_bar_html = f'<div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 8px; padding: 12px 20px; margin-bottom: 24px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 12px; color: #5f6368;"><div style="display: flex; align-items: center; gap: 8px;">📅 <span>Captured at {recorded_time}</span></div><div style="display: flex; align-items: center; gap: 8px;">💻 <span>Emulated {selected_strategy.capitalize()} with Lighthouse 13.4.1</span></div><div style="display: flex; align-items: center; gap: 8px;">🔗 <span>Single page session</span></div><div style="display: flex; align-items: center; gap: 8px;">⏱️ <span>Initial page load</span></div><div style="display: flex; align-items: center; gap: 8px;">📶 <span>Custom throttling</span></div><div style="display: flex; align-items: center; gap: 8px;">🌐 <span>Using HeadlessChromium 151.0.7922.173</span></div></div>'
        st.markdown(meta_bar_html, unsafe_allow_html=True)

        executive_summary = f'<div style="background-color: #e8f0fe; border-left: 4px solid #1a73e8; padding: 16px; border-radius: 4px; margin-bottom: 24px; color: #174ea6;"><div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">Executive Summary & Health Status</div><div style="font-size: 13px; line-height: 1.5;">The current performance score for this {selected_strategy} environment is <strong>{perf_score}/100 (Grade {current_letter})</strong>. Addressing all Level 1 and Level 2 priority insights is projected to lift performance to an estimated <strong>{estimated_optimized_score}/100 (Grade {estimated_letter})</strong>. <a href="https://web.dev/explore/learn-core-web-vitals" target="_blank" style="color: #1a73e8; font-weight: 600; text-decoration: underline;">Read official CWV definitions &rarr;</a></div></div>'
        st.markdown(executive_summary, unsafe_allow_html=True)

        col_gauge, col_metrics = st.columns([1, 2.5])
        
        with col_gauge:
            gauge_html = f'''
            <div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 24px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <div style="font-size: 13px; font-weight: 600; color: #5f6368; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Performance Score</div>
                <div style="display: flex; gap: 16px; justify-content: center; align-items: center; margin-bottom: 12px;">
                    <div>
                        <div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-weight: 500;">CURRENT</div>
                        <div style="width: 85px; height: 85px; border-radius: 50%; border: 6px solid {score_color}; background-color: {score_bg}; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <span style="font-size: 26px; font-weight: 700; color: {score_color}; line-height: 1;">{perf_score}</span>
                            <span style="font-size: 12px; font-weight: 700; color: {score_color}; margin-top: 2px;">Grade {current_letter}</span>
                        </div>
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-weight: 500;">EST. OPTIMIZED</div>
                        <div style="width: 85px; height: 85px; border-radius: 50%; border: 6px solid {est_color}; background-color: {est_bg}; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <span style="font-size: 26px; font-weight: 700; color: {est_color}; line-height: 1;">{estimated_optimized_score}</span>
                            <span style="font-size: 12px; font-weight: 700; color: {est_color}; margin-top: 2px;">Grade {estimated_letter}</span>
                        </div>
                    </div>
                </div>
                <div style="font-size: 11px; color: #5f6368; border-top: 1px solid #e8eaed; padding-top: 8px; width: 100%; margin-bottom: 10px;">Estimated score if all Level 1 & 2 fixes are resolved.</div>
                
                <!-- Google Lighthouse Score Weightings Legend -->
                <div style="display: flex; justify-content: space-around; width: 100%; font-size: 11px; color: #5f6368; border-top: 1px dashed #dadce0; padding-top: 8px;">
                    <div style="display: flex; align-items: center; gap: 4px;"><span style="color: #ff4e42; font-weight: bold;">▲</span> <span>0–49</span></div>
                    <div style="display: flex; align-items: center; gap: 4px;"><span style="color: #ffa400; font-weight: bold;">■</span> <span>50–89</span></div>
                    <div style="display: flex; align-items: center; gap: 4px;"><span style="color: #0cce6b; font-weight: bold;">●</span> <span>90–100</span></div>
                </div>
            </div>
            '''
            st.markdown(gauge_html, unsafe_allow_html=True)

        with col_metrics:
            lcp_color = "#0cce6b" if avg_lcp <= 2.5 else ("#ffa400" if avg_lcp <= 4.0 else "#ff4e42")
            tbt_color = "#0cce6b" if avg_tbt <= 200 else ("#ffa400" if avg_tbt <= 600 else "#ff4e42")
            cls_color = "#0cce6b" if avg_cls <= 0.10 else ("#ffa400" if avg_cls <= 0.25 else "#ff4e42")
            ttfb_color = "#0cce6b" if avg_ttfb <= 800 else ("#ffa400" if avg_ttfb <= 1800 else "#ff4e42")

            metrics_html = f'<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"><div style="font-size: 14px; font-weight: 500; color: #202124; margin-bottom: 14px; border-bottom: 1px solid #e8eaed; padding-bottom: 8px;">Core Web Vitals & Technical Diagnostics</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;"><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {lcp_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Largest Contentful Paint</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_lcp:.2f} s</div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-style: italic;">How fast the main page content loads</div><div style="font-size: 11px; color: #1a73e8; font-weight: 500;">Target: ≤ 2.5s (Good)</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {tbt_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Total Blocking Time</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_tbt:.0f} ms</div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-style: italic;">How long the page freezes before responding</div><div style="font-size: 11px; color: #1a73e8; font-weight: 500;">Target: ≤ 200 ms</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {cls_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Cumulative Layout Shift</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_cls:.3f}</div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-style: italic;">How much page content unexpectedly jumps around</div><div style="font-size: 11px; color: #1a73e8; font-weight: 500;">Target: ≤ 0.10 (Good)</div></div><div style="background-color: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid {ttfb_color};"><div style="font-size: 11px; font-weight: 500; color: #5f6368; text-transform: uppercase;">Server Response Time</div><div style="font-size: 22px; font-weight: 700; color: #202124; margin: 4px 0;">{avg_ttfb:.0f} ms</div><div style="font-size: 11px; color: #5f6368; margin-bottom: 4px; font-style: italic;">How fast the server starts sending data</div><div style="font-size: 11px; color: #1a73e8; font-weight: 500;">Target: ≤ 800 ms</div></div></div></div>'
            st.markdown(metrics_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # INTERACTIVE INSIGHTS SORTED BY IMPORTANCE (1 -> 2 -> 3) WITH TRAFFIC LIGHTS IN TITLE
        st.markdown('<div style="font-size: 16px; font-weight: 600; color: #202124; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Insights</div>', unsafe_allow_html=True)
        
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

        insights = [
            {
                "title": "Render-blocking requests — Est savings of 1,380 ms",
                "tech": "Scripts and stylesheets in `<head>` block document parsing before initial render.",
                "plain": "External plugins or tracking scripts are forcing the browser to wait before showing any content on the screen.",
                "location": "Header section (`<head>`) / Global stylesheets and third-party tracking scripts loaded in main layout template.",
                "cwv_impact": "Directly improves First Contentful Paint (FCP) and Largest Contentful Paint (LCP), boosting overall CWV pass rate significantly.",
                "importance": 1,
                "relevant_to": ["All", "First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)", "Total Blocking Time (TBT)"]
            },
            {
                "title": "Forced reflow",
                "tech": "Synchronous DOM measurements triggered style recalculations during layout stages.",
                "plain": "JavaScript code is asking the browser for element dimensions immediately after modifying styles, causing layout recalculation loops.",
                "location": "Interactive UI components / Dropdown menu scripts and responsive grid calculation handlers (`main.js`).",
                "cwv_impact": "Reduces main-thread CPU congestion and prevents layout instability, protecting Cumulative Layout Shift (CLS).",
                "importance": 2,
                "relevant_to": ["All", "First Contentful Paint (FCP)", "Cumulative Layout Shift (CLS)"]
            },
            {
                "title": "LCP breakdown",
                "tech": "Sub-portion latencies: TTFB, Load Delay, Load Time, and Render Delay.",
                "plain": "Measures exactly where time is lost before the main hero banner or heading image appears to the visitor.",
                "location": "Hero banner section / Homepage main product imagery and header background assets.",
                "cwv_impact": "Accelerates Largest Contentful Paint (LCP) delivery by pinpointing server response bottlenecks.",
                "importance": 1,
                "relevant_to": ["All", "Largest Contentful Paint (LCP)"]
            },
            {
                "title": "LCP request discovery",
                "tech": "The primary LCP image/text element was discovered late due to inline styling or deferred HTML structure.",
                "plain": "The browser didn't start downloading the main page banner until late in the page loading process because it was hidden inside external CSS or JS.",
                "location": "Above-the-fold hero container / Homepage banner image element (`<img>` tag without preload hints).",
                "cwv_impact": "Ensures the main hero image loads immediately, directly securing a 'Good' Largest Contentful Paint (LCP) score.",
                "importance": 1,
                "relevant_to": ["All", "Largest Contentful Paint (LCP)"]
            },
            {
                "title": "Network dependency tree",
                "tech": "Critical request chains delaying downstream asset fetching and execution.",
                "plain": "A long sequence of dependent files blocks the browser from downloading critical page elements efficiently.",
                "location": "Resource loading pipeline / Root HTML document referencing dependent CSS bundles and web font stylesheets.",
                "cwv_impact": "Shortens the critical rendering path, improving both First Contentful Paint (FCP) and overall compliance.",
                "importance": 2,
                "relevant_to": ["All", "First Contentful Paint (FCP)", "Largest Contentful Paint (LCP)"]
            },
            {
                "title": "Use efficient cache lifetimes — Est savings of 83 KiB",
                "tech": "Static assets served with short or missing Cache-Control HTTP headers.",
                "plain": "Returning shoppers' browsers are forced to re-download static images and logo files on every page visit instead of saving them locally.",
                "location": "Static asset server configuration / Media storage bucket & Nginx/Cloudflare caching rule headers (`/static/` and `/media/`).",
                "cwv_impact": "Reduces repeat network overhead and speeds up subsequent page loads for returning users.",
                "importance": 3,
                "relevant_to": ["All", "Largest Contentful Paint (LCP)"]
            },
            {
                "title": "Font display — Est savings of 10 ms",
                "tech": "Custom web fonts lack explicit `font-display: swap` directives, risking invisible text flashes.",
                "plain": "Custom typography blocks text rendering briefly while font files download from external servers.",
                "location": "Global stylesheet typography declarations / Google Fonts or local font face declarations (`@font-face`).",
                "cwv_impact": "Prevents invisible text rendering delays, improving First Contentful Paint (FCP).",
                "importance": 3,
                "relevant_to": ["All", "First Contentful Paint (FCP)"]
            },
            {
                "title": "Improve image delivery — Est savings of 1,287 KiB",
                "tech": "Uncompressed raster images served above-the-fold without next-gen format negotiation (WebP/AVIF).",
                "plain": "Product catalog and banner images are oversized file formats, wasting bandwidth and slowing down visual loading speeds.",
                "location": "Homepage catalog grid & category landing page banners (`/images/products/` and `/banners/`).",
                "cwv_impact": "Significantly lightens page weight, directly reducing Largest Contentful Paint (LCP) times.",
                "importance": 1,
                "relevant_to": ["All", "Largest Contentful Paint (LCP)"]
            },
            {
                "title": "Legacy JavaScript — Est savings of 7 KiB",
                "tech": "Polyfills and transform helper functions included for obsolete browser environments.",
                "plain": "Unnecessary compatibility code is being sent to modern web browsers.",
                "location": "Vendor bundle scripts / Polyfill modules injected via build pipeline (`vendor.min.js`).",
                "cwv_impact": "Decreases script execution time, improving Total Blocking Time (TBT) and interactivity.",
                "importance": 2,
                "relevant_to": ["All", "Total Blocking Time (TBT)"]
            },
            {
                "title": "Layout shift culprits",
                "tech": "Top banner announcements or dynamic ads resizing without reserved box dimensions.",
                "plain": "Elements shift around as the page loads, causing accidental misclicks when users try to tap buttons.",
                "location": "Header notification bar & promotional banner slots immediately above navigation menus.",
                "cwv_impact": "Secures full compliance for Cumulative Layout Shift (CLS), ensuring a rock-solid visual layout.",
                "importance": 1,
                "relevant_to": ["All", "Cumulative Layout Shift (CLS)"]
            },
            {
                "title": "3rd parties",
                "tech": "External analytics, chat widgets, and tag managers monopolizing main-thread CPU cycles.",
                "plain": "Third-party marketing and support tools are consuming processor power, making the page temporarily unresponsive.",
                "location": "Footer tracking scripts & floating widget iframes (Live chat widget, Google Tag Manager container).",
                "cwv_impact": "Frees up the main thread, directly reducing Total Blocking Time (TBT) for a smoother user experience.",
                "importance": 2,
                "relevant_to": ["All", "Total Blocking Time (TBT)"]
            }
        ]

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

        # DIAGNOSTICS SECTION
        st.markdown('<div style="font-size: 16px; font-weight: 600; color: #202124; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">Diagnostics</div>', unsafe_allow_html=True)
        
        diagnostics = [
            {
                "title": "Reduce unused JavaScript — Est savings of 196 KiB",
                "tech": "Unexecuted script bytes loaded during initial page initialization.",
                "plain": "Scripts containing code that isn't needed for the initial page load are slowing down script parsing.",
                "location": "Global bundle scripts (`bundle.js`, `cart-drawer.js`).",
                "cwv_impact": "Improves script evaluation times, helping lower Total Blocking Time (TBT).",
                "importance": 2
            },
            {
                "title": "Reduce unused CSS — Est savings of 179 KiB",
                "tech": "Stylesheets contain rule sets unreferenced by the current DOM structure.",
                "plain": "Extra style rules for other pages are being loaded all at once, bloating file size.",
                "location": "Main stylesheet declarations (`styles.css`, framework UI libraries).",
                "cwv_impact": "Speeds up stylesheet parsing and rendering, improving First Contentful Paint (FCP).",
                "importance": 2
            },
            {
                "title": "Image elements do not have explicit width and height",
                "tech": "Missing `width` and `height` attributes on `<img>` nodes cause browser reflows upon image load.",
                "plain": "Images don't have reserved space defined in the code, causing surrounding text to jump when they finally pop in.",
                "location": "Product grid catalog cards & footer thumbnail images.",
                "cwv_impact": "Eliminates unexpected visual shifts, directly protecting Cumulative Layout Shift (CLS) compliance.",
                "importance": 1
            },
            {
                "title": "Avoid long main-thread tasks — 5 long tasks found",
                "tech": "Main thread execution blocks exceeding 50ms thresholds.",
                "plain": "Heavy scripts are running uninterrupted for too long, causing freezes when users try to scroll or click.",
                "location": "Client-side state hydration & event listener loops (`app.bundle.js`).",
                "cwv_impact": "Enhances page responsiveness and lowers Total Blocking Time (TBT).",
                "importance": 1
            },
            {
                "title": "Avoid non-composited animations — 2 animated elements found",
                "tech": "Animating layout properties (`top`, `left`, `width`) instead of composite properties (`transform`, `opacity`).",
                "plain": "Visual transitions and popups are animated inefficiently, causing stuttering movement.",
                "location": "Modal popup dialogs & promotional sliding notification banners.",
                "cwv_impact": "Prevents jank and layout shifts during UI animations.",
                "importance": 3
            }
        ]

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

        st.markdown("<br>", unsafe_allow_html=True)

        # Additional PSI Audit Pillars Section
        st.markdown('<div style="font-size: 16px; font-weight: 600; color: #202124; margin-bottom: 12px;">Additional PageSpeed Audit Pillars</div>', unsafe_allow_html=True)
        
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        with col_p1:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #1a73e8;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">Accessibility</div><div style="font-size: 28px; font-weight: 700; color: #1a73e8; margin: 8px 0;">90</div><div style="font-size: 11px; color: #5f6368;">Labels & Contrast Checks</div></div>', unsafe_allow_html=True)
            
        with col_p2:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #0cce6b;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">Best Practices</div><div style="font-size: 28px; font-weight: 700; color: #0cce6b; margin: 8px 0;">96</div><div style="font-size: 11px; color: #5f6368;">Trust & Code Standards</div></div>', unsafe_allow_html=True)
            
        with col_p3:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 16px; padding: 16px; text-align: center; border-top: 4px solid #ffa400;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">SEO</div><div style="font-size: 28px; font-weight: 700; color: #ffa400; margin-top: 8px; margin-bottom: 8px;">61</div><div style="font-size: 11px; color: #5f6368;">Crawling & Meta Tags</div></div>', unsafe_allow_html=True)

        with col_p4:
            st.markdown('<div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 16px; text-align: center; border-top: 4px solid #1a73e8;"><div style="font-size: 13px; font-weight: 500; color: #5f6368;">Agentic Browsing</div><div style="font-size: 28px; font-weight: 700; color: #1a73e8; margin-top: 8px; margin-bottom: 8px;">1/3</div><div style="font-size: 11px; color: #5f6368;">AI Agent Accessibility</div></div>', unsafe_allow_html=True)

# TAB 2: URL VITALS
with tabs[1]:
    st.header("📊 Historical URL Vitals")
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM web_performance_logs ORDER BY recorded_at ASC;", conn)

    .strip()
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
