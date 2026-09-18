"""
Project-Robin search configuration.

Unlike Career-Ping (which watches a fixed list of named companies),
this searches ANY employer via the Adzuna job aggregator - because
Robin wants local admin/ops roles at whatever company happens to be
hiring, not a specific watchlist of companies.

Edit the lists below to change what counts as a match. No coding
knowledge needed - just add or remove quoted lines, same as Career-Ping.
"""

# ---- What Adzuna searches for ----
# Each of these is run as its own separate search (Adzuna's API doesn't
# support "any of these titles" in one query), then results are combined
# and de-duplicated. More keywords = more API calls per run, so keep an
# eye on the total (see README for Adzuna's free-tier call limit).
TITLE_KEYWORDS = [
    "Office Manager",
    "Executive Assistant",
    "Business Operations Manager",
    "Administrative Manager",
    "Administrative Director",
    "Office Administrator",
    "Operations Coordinator",
    "Operations Specialist",
    "Practice Manager",
    "Facilities Manager",
    "Executive Coordinator",
    "Workplace Experience Manager",
    "HR Office Manager",
    "General Manager",
]

# ---- Where ----
LOCATION = "Riverton, UT"
DISTANCE_MILES = 25  # Adzuna's "distance" param is in miles for the US market

# ---- Salary ----
SALARY_MIN = 80000
SALARY_MAX = 95000
# If True, postings with no salary listed are still included (many admin
# roles don't post a number) - set to False if you'd rather only see
# postings that explicitly state a salary in range.
INCLUDE_UNLISTED_SALARY = True

# ---- Remote/hybrid/in-office rules ----
# Robin wants hybrid or in-office - NOT fully remote. Logic:
#   - if the posting explicitly says "hybrid" anywhere -> always keep
#   - else if it matches one of the phrases below -> drop (fully remote)
#   - else -> keep (assume in-office/unspecified, benefit of the doubt)
REMOTE_EXCLUDE_KEYWORDS = [
    "fully remote", "100% remote", "remote only", "remote-first",
    "remote position", "work from home only", "work from anywhere",
    "this is a remote position", "remote (us)", "fully-remote",
]
