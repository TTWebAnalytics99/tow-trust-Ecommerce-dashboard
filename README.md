# Tow-Trust Core Web Vitals Monitoring Facility

A streamlined, production-grade telemetry and diagnostics system designed to monitor Google Core Web Vitals (CWV) for automotive e-commerce platforms, optimized for real-time executive reporting and dedicated office display kiosk hardware.
Technical Stack

    Frontend UI: Python, Streamlit (Role-aware: Admin & Read-Only Kiosk tiers)

    Telemetry Engine: Google PageSpeed Insights / Lighthouse API integration

    Database: Neon Serverless PostgreSQL

    Hosting & Deployment: Streamlit Community Cloud

    Office Display Wrapper: Custom HTML/JS client-side redirect (index.html)

Core Architecture & Database Schema

The production database is hosted on Neon PostgreSQL and relies on two primary tables:

1. monitored_targets

Stores URLs actively registered for automated performance scans.

2. web_performance_logs

Stores historical Lighthouse audit telemetry across mobile and desktop viewports.

Dashboard Features (app.py)

    📑 Executive Briefing: Evaluates live operational telemetry against Google Core Web Vitals thresholds (LCP ≤ 2.5s, TBT ≤ 200ms, CLS ≤ 0.10).
          
    📊 Historical URL Vitals: Long-term trend analysis tracking latency and performance shifts over time. 
    
    🎨 Asset Bottlenecks: Highlights unoptimized image waste, unused CSS payloads, and third-party main thread drag.

    ⚡ Ad-Hoc Tester (Admin Only): On-demand Lighthouse audit runner for immediate diagnostics.

Office Kiosk Integration (index.html)

To bypass cloud security restrictions (X-Frame-Options) that block external <iframe> embedding on office display hardware, the system uses a lightweight client-side JavaScript redirect wrapper (index.html) targeting read-only kiosk mode (?mode=kiosk).
