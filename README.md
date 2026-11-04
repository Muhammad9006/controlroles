# ControlRoles (controlroles.com)

A worldwide job board for project controls roles in construction, infrastructure and energy: planning, project controls,
cost and commercial, contracts, claims, risk and project management.
Twice a day it reads employers' own careers sites, keeps the relevant roles, drops closed ones and publishes the website.
Every listing links straight to the job on the employer's site.

Running cost: **free** on GitHub (Actions + Pages). The domain costs about $10–15 a year.

---

## 1. Put it on GitHub (about 30 minutes, no coding)

1. **Create a GitHub account** at github.com if you don't have one.
2. **Create a repository**: click **New**, name it `controlroles`, choose **Public**
   (free GitHub Pages needs a public repository), click **Create repository**.
3. **Upload the files**: on the empty repository page click **uploading an existing file**, drag in
   everything from this folder, including the hidden `.github` folder, and click **Commit changes**.
   - If your computer hides `.github`: **Add file → Create new file**, name it `.github/workflows/collect.yml`
     and paste in that file's contents.
   - Don't upload a `site/jobs` folder, `site/sitemap.xml` or `site/robots.txt` if you have them: the robot builds those.
   - Expect the first automatic run to show a red ✗ at "deploy". That's normal: the website isn't switched on yet.
4. **Switch the website on**: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
5. **Run it once**: **Actions → Collect jobs → Run workflow**. The first run can take up to an hour.
   When it finishes, **Settings → Pages** shows the address (for example `https://<you>.github.io/controlroles/`).

After that it runs by itself at about 06:17 and 18:17 Riyadh time. No passwords or secret keys are needed.

## 2. Connect controlroles.com

1. **Verify the domain** (stops anyone else using it on GitHub): your profile picture → **Settings → Pages →
   Add a domain** → `controlroles.com`. GitHub shows a TXT record: add it at your domain registrar, then click **Verify**.
2. **At your registrar's DNS settings**, add:
   - four **A** records for `controlroles.com`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - a **CNAME** record for `www` pointing to `<your-github-username>.github.io`
3. **Repository → Settings → Pages → Custom domain**: type `controlroles.com` → **Save**.
   When the DNS check turns green (minutes to a few hours), tick **Enforce HTTPS**.
4. **Google**: add the site in Google Search Console and submit `https://controlroles.com/sitemap.xml`.

## 3. Email and job-alert sign-ups

- **hello@controlroles.com** is the contact address on the site (About, employers, alerts). Set up free forwarding to
  your own inbox at your registrar (for example Cloudflare Email Routing or ImprovMX) **before launch**.
- **Alert sign-ups**: until you connect a form service, the alert form opens a pre-filled email to hello@controlroles.com,
  so no sign-up is lost. To collect sign-ups automatically, create a free form at a service such as Formspree, Tally or
  Basin, copy its endpoint address, and paste it into `site/index.html` at `const ALERTS_FORM_URL = "";`
  (search for that line). The robot does **not** send emails yet: sending the weekly or daily alert emails needs a
  newsletter service (for example MailerLite or Buttondown) as a later step.

## 4. Launch offer (Pro free) and turning payments on

Pro is free for everyone during the launch. When you add a payment gateway, open `site/index.html`, find
`const LAUNCH_FREE_PRO = true;` and change it to `false`: the normal prices and the waitlist wording come back.
Note: Pro is unlocked inside the page, so real paid access will need a payment/login service at that point.

## 5. Check each run

**Actions → Collect jobs → the latest run** shows a table:

| Employer | Status | Jobs read | Kept | Note |
|---|---|---|---|---|
| Aldar | ok | 41 | 6 | |
| Parsons | FAILED | 0 | 0 | HTTPError 404. Check tenant/site settings in employers.json. |

- **FAILED**: the employer's site was down or its settings are wrong. Its last jobs stay up for 3 days, then drop off.
  Failed employers also show as a yellow warning on the run.
- **not connected**: roles that were imported by hand for an employer without a connector. They stay up for 21 days
  after their last check, then drop off, unless the employer gets a connector or is imported again.

## 6. Employers

Edit `employers.json` on GitHub (pencil icon).
- `"enabled": true` collects the employer, `false` pauses it.
- `"remove": true` takes an employer and all its roles off the board at the next run (use this for removal requests).

Collected automatically now:

| Employer | Careers system |
|---|---|
| AECOM | SmartRecruiters |
| Aldar | Lever |
| AtkinsRéalis | Workday |
| Cumming Group | Workday |
| DAMAC | Oracle |
| HKA | Teamtailor |
| Hill International | Oracle |
| Honeywell | Oracle |
| Iron Mountain | Workday |
| JASARA PMC | Workable |
| JLL | Workday |
| KBR | Workday |
| KEO International | Jibe |
| Larsen & Toubro | PeopleStrong |
| McDermott | Oracle |
| Orascom Construction | Oracle |
| PMA Consultants | Lever |
| Parsons | Workday |
| Sobha | PeopleStrong |
| Surbana Jurong | Workday |
| Turner & Townsend | SmartRecruiters |
| WSP | Oracle |
| Wood | Oracle |

Need a connector (their roles were imported by hand and drop off 21 days after the last import): Alstom, Amey, Arcadis, Arup, Baker Construction, Balfour Beatty, Bechtel, Compass Project Consulting, Currie & Brown, Dar, Egis, EllisDon, Fluor, Gleeds, HDR, Hassan Allam Holding, Jacobs, Kier, Kiewit, Leighton Asia, Mace, Mott MacDonald, Penspen, Protecnium, SYSTRA, TBH, VINCI, Wates, Webuild, Worley.

To add an employer, find its careers system from any job link:

| If a job's address looks like… | system | settings |
|---|---|---|
| `jobs.lever.co/aldar/…` | `lever` | `"account": "aldar"` |
| `parsons.wd5.myworkdayjobs.com/Search/job/…` | `workday` | `"tenant": "parsons", "wd": "wd5", "site": "Search"` |
| `jobs.smartrecruiters.com/AECOM2/…` | `smartrecruiters` | `"account": "AECOM2"` |
| `xxxx.fa.ca3.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2001/job/…` | `oracle` | `"host": "xxxx.fa.ca3.oraclecloud.com", "site": "CX_2001"` |
| `apply.workable.com/company-name/j/…` | `workable` | `"account": "company-name"` |
| `boards.greenhouse.io/company/jobs/…` | `greenhouse` | `"account": "company"` |
| `careers.company.com/jobs/1234-title` (Teamtailor) | `teamtailor` | `"host": "careers.company.com"` |
| `company.peoplestrong.com/job/detail/…` | `peoplestrong` | `"host": "company.peoplestrong.com"` |

Other systems (SAP SuccessFactors, Taleo, Eploy, Zoho Recruit, Phenom…) need a new connector: ask Claude to add one
and give it a job link from that employer.

## 7. Adding jobs by hand (featured / paid posts)

Jobs you add yourself are read from **one** of these, twice a day:

1. **A Google Sheet (easiest).** Make a sheet with the same columns as `manual_jobs.csv`, then
   *File → Share → Publish to web → (that sheet's tab only) → Comma-separated values (.csv) → Publish*,
   and paste the link into `settings.json` as `"manual_jobs_csv_url": "<link>"`.
   The published tab is public: keep employer emails or payment details in a different, unpublished tab.
2. **`manual_jobs.csv` in this project**: open the file on GitHub, click the pencil, add a line, **Commit changes**.

Columns: `title, company, url, city, country, discipline, seniority, company_type, posted, featured_until, remove_after`.
Only `title`, `company` and `url` (https://) are required. Dates are `YYYY-MM-DD`.
- `featured_until`: pinned to the top with a **Featured** badge until this date.
- `remove_after`: the job disappears after this date.
- Start a title with `#` to switch a row off.

If the sheet can't be read on a run, the last run's hand-added jobs are kept.

## 8. Files

```
employers.json                  employers and their careers-system settings
settings.json                   site address and the optional Google Sheet link
manual_jobs.csv                 jobs added by hand
collector/                      the robot: run.py (main run), connectors/ (one per careers system),
                                classify.py (what counts as relevant), pages.py (a page per job for Google)
site/index.html                 the website (reads site/jobs.js, which each run writes)
site/404.html                   sends links to closed jobs back to the board
data/jobs.json, data/state.json the job history (keep these in the repository)
.github/workflows/collect.yml   the twice-daily schedule
tests/                          offline checks; run with: python -m pytest -q tests
```

## Good practice

- The robot reads only public job listings, identifies itself as ControlRolesBot, runs twice a day and links every role
  back to the employer. Honour any removal request (`"remove": true`).
- Before charging users, register the business and publish full privacy and payment terms. If you store emails of Saudi
  users, follow the Saudi Personal Data Protection Law (PDPL).
