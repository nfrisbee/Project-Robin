#!/usr/bin/env python3
"""
Project-Robin job alert bot.

Searches Adzuna (a job aggregator covering thousands of employers) for
admin/operations roles near Riverton, UT within Robin's salary range,
hybrid or in-office only, and emails her when a NEW one appears.

Run manually:
    python job_alert.py

Environment variables required (set as GitHub Actions secrets):
    ADZUNA_APP_ID      - from developer.adzuna.com (free signup)
    ADZUNA_APP_KEY     - from developer.adzuna.com (free signup)
    SMTP_EMAIL         - Gmail address to send FROM
    SMTP_APP_PASSWORD  - a Gmail "app password" (NOT your normal password)
    ALERT_TO_EMAIL     - the address to send alerts TO (Robin's email)

State is kept in seen_jobs.json so re-runs don't re-email jobs already
sent. The GitHub Actions workflow commits this file back after each run.
"""

import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import requests

from search_config import (
    TITLE_KEYWORDS,
    LOCATION,
    DISTANCE_MILES,
    SALARY_MIN,
    SALARY_MAX,
    INCLUDE_UNLISTED_SALARY,
    REMOTE_EXCLUDE_KEYWORDS,
)

STATE_FILE = Path(__file__).parent / "seen_jobs.json"
REQUEST_TIMEOUT = 20
COUNTRY = "us"
RESULTS_PER_PAGE = 50
MAX_PAGES_PER_KEYWORD = 2  # safety cap; local 25mi searches rarely need more


def load_seen():
    if STATE_FILE.exists():
        try:
            return set(json.loads(STATE_FILE.read_text()))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()


def save_seen(seen_ids):
    STATE_FILE.write_text(json.dumps(sorted(seen_ids), indent=2))


def passes_remote_filter(title, description):
    text = f"{title} {description}".lower()
    if "hybrid" in text:
        return True
    if any(kw in text for kw in REMOTE_EXCLUDE_KEYWORDS):
        return False
    return True


def fetch_adzuna(keyword, app_id, app_key):
    jobs = []
    for page in range(1, MAX_PAGES_PER_KEYWORD + 1):
        url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/{page}"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": RESULTS_PER_PAGE,
            "what": keyword,
            "title_only": keyword,
            "where": LOCATION,
            "distance": DISTANCE_MILES,
            "salary_min": SALARY_MIN,
            "salary_max": SALARY_MAX,
            "salary_include_unknown": "1" if INCLUDE_UNLISTED_SALARY else "0",
            "sort_by": "date",
        }
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} from Adzuna for keyword '{keyword}'")
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        for j in results:
            salary_min = j.get("salary_min")
            salary_max = j.get("salary_max")
            if salary_min and salary_max:
                salary_display = f"${salary_min:,.0f} - ${salary_max:,.0f}"
            else:
                salary_display = "Not listed"
            jobs.append({
                "id": str(j.get("id", j.get("redirect_url", ""))),
                "title": j.get("title", ""),
                "company": (j.get("company") or {}).get("display_name", "Unknown company"),
                "location": (j.get("location") or {}).get("display_name", ""),
                "url": j.get("redirect_url", ""),
                "salary": salary_display,
                "description": j.get("description", ""),
            })
        if len(results) < RESULTS_PER_PAGE:
            break
    return jobs


def collect_new_matches(app_id, app_key):
    seen = load_seen()
    new_matches = []
    errors = []
    seen_this_run = set()  # avoid duplicate emails when 2+ keywords match the same job

    for keyword in TITLE_KEYWORDS:
        try:
            jobs = fetch_adzuna(keyword, app_id, app_key)
        except Exception as e:
            errors.append(f"'{keyword}' search: {e}")
            continue

        for job in jobs:
            if job["id"] in seen_this_run:
                continue
            if not passes_remote_filter(job["title"], job["description"]):
                continue
            if job["id"] in seen:
                continue
            seen_this_run.add(job["id"])
            new_matches.append({
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "salary": job["salary"],
                "url": job["url"],
            })
            seen.add(job["id"])

    save_seen(seen)
    return new_matches, errors


def send_email(matches, errors):
    smtp_email = os.environ["SMTP_EMAIL"]
    smtp_password = os.environ["SMTP_APP_PASSWORD"]
    to_email = os.environ["ALERT_TO_EMAIL"]

    subject = f"💼 {len(matches)} new job posting(s) for Robin"
    lines = []
    for m in matches:
        lines.append(
            f"{m['title']} - {m['company']}\n"
            f"Location: {m['location']}\n"
            f"Salary: {m['salary']}\n"
            f"{m['url']}\n"
        )
    if errors:
        lines.append("\n---\nSearches that couldn't be completed this run:")
        lines.extend(f"- {e}" for e in errors)
    body = "\n".join(lines)

    msg = MIMEMultipart()
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, to_email, msg.as_string())


def main():
    try:
        app_id = os.environ["ADZUNA_APP_ID"]
        app_key = os.environ["ADZUNA_APP_KEY"]
    except KeyError as e:
        print(f"Missing environment variable: {e}. Set ADZUNA_APP_ID and ADZUNA_APP_KEY.")
        sys.exit(1)

    matches, errors = collect_new_matches(app_id, app_key)

    print(f"Found {len(matches)} new matching posting(s).")
    for m in matches:
        print(f"  - {m['title']} @ {m['company']} ({m['location']}, {m['salary']}) -> {m['url']}")
    if errors:
        print(f"\n{len(errors)} searches could not be completed:")
        for e in errors:
            print(f"  ! {e}")

    if matches:
        try:
            send_email(matches, errors)
            print("Email sent.")
        except KeyError as e:
            print(f"Missing environment variable: {e}. Set SMTP_EMAIL, SMTP_APP_PASSWORD, ALERT_TO_EMAIL.")
            sys.exit(1)
    else:
        print("Nothing new - no email sent.")


if __name__ == "__main__":
    main()
