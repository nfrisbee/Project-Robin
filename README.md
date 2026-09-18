# Project-Robin

Emails Robin when a new admin/operations job appears within 25 miles of
Riverton, UT, paying $80,000-$95,000/year, hybrid or in-office (not fully
remote). Runs for free on GitHub Actions once a day - your computer
doesn't need to be on.

**How this is different from Career-Ping:** Career-Ping watches a fixed
list of named companies. Robin doesn't have a target company list - she
wants ANY local employer that's hiring for the right kind of role. So
instead of checking company career pages one by one, this searches
[Adzuna](https://www.adzuna.com), a job aggregator that indexes postings
from thousands of employers, filtered by title, location, radius, and
salary all at once.

## 1. Get a free Adzuna API key (2 minutes)

1. Go to https://developer.adzuna.com/ and click **Register**.
2. After signing up, your dashboard shows an **App ID** and **App Key** -
   copy both.
3. Free tier is about **1,000 calls/month** (~33/day). This bot uses 14
   calls per run (one per job title searched) and is scheduled to run
   once daily = ~420 calls/month, leaving room for manual test runs.
   Don't change the schedule to run more often than daily without
   keeping this limit in mind (see the workflow file's comments).

## 2. Get a Gmail "app password" (2 minutes)

Same as Career-Ping - you can reuse the same Gmail account/app password
you already set up for that project if you'd like, since an app
password isn't tied to a specific script or repo.

If setting up fresh:
1. Turn on 2-Step Verification: https://myaccount.google.com/security
2. Create an app password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password shown - you won't see it again.

## 3. Create a GitHub repo

1. Go to https://github.com/new, create a new **private** repo (e.g.
   `Project-Robin`).
2. Upload all the files from this folder into it.

**Mac users:** if you're dragging files from Finder, press **Cmd+Shift+.**
first to show hidden files - otherwise the `.github` folder (which
contains the scheduling file) won't be visible to drag in, and the
automation won't run. This tripped up Career-Ping's setup, worth
avoiding here too.

## 4. Add your secrets

**Settings -> Secrets and variables -> Actions -> New repository secret.**
Add all five:

| Name | Value |
|---|---|
| `ADZUNA_APP_ID` | from step 1 |
| `ADZUNA_APP_KEY` | from step 1 |
| `SMTP_EMAIL` | the Gmail address you made the app password for |
| `SMTP_APP_PASSWORD` | the 16-character app password from step 2 |
| `ALERT_TO_EMAIL` | `rawrbin157@gmail.com` |

## 5. Turn it on

**Actions tab -> "Check jobs for Robin" -> Run workflow -> Run workflow**
(green button). Click into the run to watch it go - a green checkmark
means it worked. To see what it actually found, expand the **"Run job
check"** step and scroll to the bottom of the log - it prints a line
like `Found X new matching posting(s).`

## Making changes: job titles, location, salary, and remote rules

Everything Robin might want to tune lives in plain, readable lists in
`search_config.py` - edit directly on GitHub.com (pencil icon on the
file -> edit -> Commit changes), same as Career-Ping.

**Job titles** - `TITLE_KEYWORDS` near the top. Add or remove a quoted
line to add/remove a title. Keep in mind: **each title is a separate
Adzuna API call**, so adding titles eats into the monthly call budget
faster (14 titles x 30 daily runs = ~420 calls/month currently; adding
5 more pushes that to ~570/month, still fine, but worth knowing).

```python
TITLE_KEYWORDS = [
    "Office Manager",
    "Executive Assistant",
    "Community Relations Manager",   # <- adding a new one is this easy
    ...
]
```

**Location/radius** - `LOCATION` and `DISTANCE_MILES`. Change the city
or the mile radius:
```python
LOCATION = "Riverton, UT"
DISTANCE_MILES = 25
```

**Salary range** - `SALARY_MIN` and `SALARY_MAX`. Also
`INCLUDE_UNLISTED_SALARY` - set to `False` if Robin would rather only
see postings that explicitly state a salary in range (many admin roles
don't list one, so `True` casts a wider net).

**Remote/hybrid/in-office rules** - `REMOTE_EXCLUDE_KEYWORDS`. A posting
is dropped if it matches one of these phrases, UNLESS it also mentions
"hybrid" anywhere (hybrid always wins, since that's explicitly wanted).
Add a phrase here if a fully-remote posting is slipping through.

## Running it locally (optional - for testing before pushing changes)

### Mac
```bash
cd ~/Project-Robin
pip3 install -r requirements.txt
export ADZUNA_APP_ID="your_app_id"
export ADZUNA_APP_KEY="your_app_key"
export SMTP_EMAIL="you@gmail.com"
export SMTP_APP_PASSWORD="your16charapppassword"
export ALERT_TO_EMAIL="rawrbin157@gmail.com"
python3 job_alert.py
```

### Windows
```bat
cd C:\Users\you\Project-Robin
pip install -r requirements.txt
set ADZUNA_APP_ID=your_app_id
set ADZUNA_APP_KEY=your_app_key
set SMTP_EMAIL=you@gmail.com
set SMTP_APP_PASSWORD=your16charapppassword
set ALERT_TO_EMAIL=rawrbin157@gmail.com
python job_alert.py
```

## How duplicate-prevention works

`seen_jobs.json` stores the IDs of every posting already emailed, so
re-runs don't repeat themselves. Same pattern as Career-Ping: the
GitHub Actions workflow commits the updated file back to the repo after
every run, so no separate database is needed.

## A few honest limitations

- **Salary data is inconsistent.** Many smaller/local employers don't
  post a salary at all - `INCLUDE_UNLISTED_SALARY = True` means those
  still get through (better to over-include than have Robin miss a
  good fit), but it also means not every alert will show a real number.
- **"Hybrid" detection is text-based**, not a structured field for
  every posting - it's checking whether the word appears in the title
  or description, so an unusually-worded posting could occasionally be
  mis-filtered. Worth a skim of what comes through.
- **Adzuna's free tier can run dry.** If you see "HTTP 429" errors in
  the workflow log, that means the monthly call limit was hit - it'll
  resume automatically once the quota resets, or you can request a
  higher limit from Adzuna directly.
