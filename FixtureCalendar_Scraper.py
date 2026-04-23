"""
HKJC Fixture Calendar Scraper — extracts annual race-day calendar.

Source: https://racing.hkjc.com/racing/information/Chinese/Racing/Fixture.aspx?calyear=Y&calmonth=M
The calendar is SPA-rendered — active race days carry inline <a href="...LocalResults.aspx?RaceDate=..."> links
or a cell class that marks them clickable. We iterate months and capture the active dates.

Output: data/fixtures/fixtures.csv with columns:
    date (YYYY-MM-DD), season_year, month, day, weekday, venue_hint, timing, captured_at

Run:
    python FixtureCalendar_Scraper.py                 # current year + next year
    python FixtureCalendar_Scraper.py --year 2026     # specific year
    python FixtureCalendar_Scraper.py --years 2025,2026
"""

import argparse
import os
import re
import sys
import time
import traceback
from datetime import date, datetime, timezone
from typing import List, Dict

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService

# ---- browser paths (honor env overrides, fall back to Nix defaults for Replit parity) ----
CHROMIUM_PATH = os.environ.get(
    "CHROMIUM_PATH",
    "/nix/store/qa9cnw4v5xkxyip6mb9kxqfq1z4x2dx1-chromium-138.0.7204.100/bin/chromium",
)
CHROMEDRIVER_PATH = os.environ.get(
    "CHROMEDRIVER_PATH",
    "/nix/store/8zj50jw4w0hby47167kqqsaqw4mm5bkd-chromedriver-unwrapped-138.0.7204.100/bin/chromedriver",
)

FIXTURE_URL = "https://racing.hkjc.com/racing/information/Chinese/Racing/Fixture.aspx"
PAGE_TIMEOUT = 20
OUTPUT_DIR = os.path.join("data", "fixtures")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "fixtures.csv")


def make_driver():
    opts = webdriver.ChromeOptions()
    for flag in [
        "--headless=new", "--disable-gpu", "--no-sandbox",
        "--disable-dev-shm-usage", "--window-size=1280,900",
        "--disable-extensions", "--disable-background-networking",
    ]:
        opts.add_argument(flag)
    if CHROMIUM_PATH and os.path.exists(CHROMIUM_PATH):
        opts.binary_location = CHROMIUM_PATH
    service_kwargs = {}
    if CHROMEDRIVER_PATH and os.path.exists(CHROMEDRIVER_PATH):
        service_kwargs["executable_path"] = CHROMEDRIVER_PATH
    return webdriver.Chrome(service=ChromeService(**service_kwargs), options=opts)


def _try_hhhp(anchor) -> str:
    """Return href of anchor if it looks like a race result link, else empty."""
    try:
        href = anchor.get_attribute("href") or ""
        if "RaceDate=" in href:
            return href
    except Exception:
        pass
    return ""


def scrape_month(driver, year: int, month: int) -> List[Dict]:
    """Fetch one month's fixture page and extract all active race-day dates."""
    url = f"{FIXTURE_URL}?calyear={year}&calmonth={month:02d}"
    driver.get(url)
    try:
        WebDriverWait(driver, PAGE_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except TimeoutException:
        print(f"  [warn] timeout loading {year}-{month:02d}", flush=True)
        return []

    # Give SPA a moment to render
    time.sleep(1.5)

    rows: List[Dict] = []

    # Strategy 1: look for anchors that link to LocalResults.aspx?RaceDate=DD/MM/YYYY
    anchors = driver.find_elements(By.XPATH, "//a[contains(@href,'RaceDate=')]")
    for a in anchors:
        href = _try_hhhp(a)
        m = re.search(r"RaceDate=(\d{2}/\d{2}/\d{4})", href)
        if not m:
            continue
        dd, mm, yyyy = m.group(1).split("/")
        try:
            d = date(int(yyyy), int(mm), int(dd))
        except ValueError:
            continue
        if d.year != year or d.month != month:
            continue  # only this month's fixtures
        timing, venue_hint = _classify_meeting(d, a)
        rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "season_year": d.year,
            "month": d.month,
            "day": d.day,
            "weekday": d.strftime("%a"),
            "venue_hint": venue_hint,
            "timing": timing,
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    # Dedupe by date (HKJC sometimes surfaces multiple links per day)
    seen = set()
    unique = []
    for r in rows:
        if r["date"] in seen:
            continue
        seen.add(r["date"])
        unique.append(r)
    return unique


def _classify_meeting(d: date, anchor) -> tuple:
    """Infer timing (day/night) and venue hint from anchor context.

    HKJC convention:
      - Wednesday meets = night racing at Happy Valley (usually)
      - Sunday meets = day racing at Sha Tin (usually)
      - Exceptions happen (festivals, special events) — we keep it coarse.
    """
    try:
        txt = (anchor.text or "").strip()
    except Exception:
        txt = ""
    cls = ""
    try:
        cls = (anchor.get_attribute("class") or "").lower()
    except Exception:
        pass

    weekday = d.weekday()  # 0=Mon
    if weekday == 2:  # Wed
        timing, venue = "night", "HV"
    elif weekday == 6:  # Sun
        timing, venue = "day", "ST"
    elif weekday == 5:  # Sat
        timing, venue = "day", "ST"
    else:
        timing, venue = "special", "?"

    if "night" in txt.lower() or "夜" in txt:
        timing = "night"
    if "日" in txt and weekday != 2:
        timing = "day"

    return timing, venue


def scrape_years(years: List[int]) -> pd.DataFrame:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_rows: List[Dict] = []
    driver = None
    try:
        driver = make_driver()
        for y in years:
            for m in range(1, 13):
                print(f"  → {y}-{m:02d}", flush=True)
                rows = scrape_month(driver, y, m)
                all_rows.extend(rows)
                time.sleep(0.5)
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

    df = pd.DataFrame(all_rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def merge_and_save(new_df: pd.DataFrame) -> pd.DataFrame:
    """Merge with existing fixtures.csv, preferring freshest captured_at per date."""
    if not os.path.exists(OUTPUT_CSV):
        new_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        return new_df
    old_df = pd.read_csv(OUTPUT_CSV)
    combined = pd.concat([old_df, new_df], ignore_index=True)
    combined["captured_at"] = combined["captured_at"].astype(str)
    combined = combined.sort_values("captured_at").drop_duplicates(subset=["date"], keep="last")
    combined = combined.sort_values("date").reset_index(drop=True)
    combined.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    return combined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, help="Single year to scrape")
    ap.add_argument("--years", type=str, help="Comma-separated list of years")
    args = ap.parse_args()

    if args.year:
        years = [args.year]
    elif args.years:
        years = sorted({int(y) for y in args.years.split(",") if y.strip()})
    else:
        y_now = date.today().year
        years = [y_now, y_now + 1]

    print(f"[fixture] scraping years: {years}", flush=True)
    try:
        new_df = scrape_years(years)
    except Exception as e:
        print(f"[fixture] FATAL: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)

    if new_df.empty:
        print("[fixture] WARN: zero dates scraped — keeping existing cache untouched", flush=True)
        sys.exit(2)

    merged = merge_and_save(new_df)
    print(f"[fixture] OK: {len(new_df)} new entries, {len(merged)} total in cache", flush=True)
    # Print a preview of next 10 upcoming meets
    today_s = date.today().strftime("%Y-%m-%d")
    upcoming = merged[merged["date"] >= today_s].head(10)
    print("\n=== Next 10 upcoming meets ===")
    for _, r in upcoming.iterrows():
        print(f"  {r['date']} {r['weekday']:>3}  {r['venue_hint']:>2}  {r['timing']}")


if __name__ == "__main__":
    main()
