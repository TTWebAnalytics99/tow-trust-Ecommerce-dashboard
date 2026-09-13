import os
import requests
import psycopg2

DB_URI = os.getenv("DATABASE_URL")
API_KEY = os.getenv("PAGESPEED_API_KEY")

def run_lighthouse_audit():
    if not DB_URI or not API_KEY:
        print("Missing DATABASE_URL or PAGESPEED_API_KEY.")
        return

    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()

    # Option 2 override: check if an environment variable specifies the target URL directly
    target_url_override = os.getenv("TARGET_URL")
    strategy_override = os.getenv("AUDIT_STRATEGY", "desktop")

    if target_url_override:
        print(f"Using environment override target: {target_url_override} ({strategy_override})")
        targets = [(target_url_override, strategy_override)]
    else:
        cursor.execute("SELECT url, strategy FROM monitored_targets WHERE is_active = TRUE;")
        targets = cursor.fetchall()

    for url, strategy in targets:
        print(f"Auditing {url} ({strategy})...")
        # Request all required category pillars from the PageSpeed Insights API
        api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&key={API_KEY}&strategy={strategy}&category=PERFORMANCE&category=ACCESSIBILITY&category=BEST_PRACTICES&category=SEO"
        
        try:
            response = requests.get(api_url, timeout=90)
            if response.status_code != 200:
                print(f"API Error for {url} [Status {response.status_code}]: {response.text}")
                continue

            data = response.json()
            lh = data.get("lighthouseResult", {})
            audits = lh.get("audits", {})
            categories = lh.get("categories", {})

            # Safely extract score floats (0.0 to 1.0) and scale to 100 integer format
            perf_raw = categories.get("performance", {}).get("score")
            acc_raw = categories.get("accessibility", {}).get("score")
            bp_raw = categories.get("best-practices", {}).get("score")
            seo_raw = categories.get("seo", {}).get("score")

            perf_score = int(perf_raw * 100) if perf_raw is not None else 0
            accessibility_score = int(acc_raw * 100) if acc_raw is not None else 0
            best_practices_score = int(bp_raw * 100) if bp_raw is not None else 0
            seo_score = int(seo_raw * 100) if seo_raw is not None else 0

            lcp_ms = audits.get("largest-contentful-paint", {}).get("numericValue", 0.0)
            tbt_ms = audits.get("total-blocking-time", {}).get("numericValue", 0.0)
            cls = audits.get("cumulative-layout-shift", {}).get("numericValue", 0.0)
            ttfb_ms = audits.get("server-response-time", {}).get("numericValue", 0.0)
            
            unoptimized_images_kb = audits.get("uses-optimized-images", {}).get("numericValue", 0.0) / 1024.0
            unused_css_kb = audits.get("unused-css-rules", {}).get("numericValue", 0.0) / 1024.0
            unused_js_kb = audits.get("unused-javascript", {}).get("numericValue", 0.0) / 1024.0
            third_party_ms = audits.get("third-party-summary", {}).get("numericValue", 0.0)

            cursor.execute("""
                INSERT INTO web_performance_logs 
                (target_url, strategy, perf_score, accessibility_score, best_practices_score, seo_score, 
                 lcp_ms, tbt_ms, cls, ttfb_ms, unoptimized_images_kb, unused_css_kb, unused_js_kb, third_party_main_thread_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (url, strategy, perf_score, accessibility_score, best_practices_score, seo_score, 
                  lcp_ms, tbt_ms, cls, ttfb_ms, unoptimized_images_kb, unused_css_kb, unused_js_kb, third_party_ms))
            conn.commit()
            print(f"Successfully logged metrics for {url}")

        except Exception as e:
            print(f"Failed processing {url}: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_lighthouse_audit()
