"""Offline tests: run with  python -m unittest discover tests"""
import json
import os
import shutil
import tempfile
import unittest

from collector import run
from collector.classify import clean_title, country_of, discipline_of, level_of
from collector.ids import job_id

HERE = os.path.dirname(os.path.abspath(__file__))


class Classify(unittest.TestCase):
    def test_disciplines(self):
        cases = {
            "Senior Planning Manager": "Planning",
            "Lead Planner – Infrastructure": "Planning",
            "Senior Associate - Development Projects Scheduling": "Planning",
            "Project Controls Director": "Project Controls",
            "Delay & Claims Manager": "Claims",
            "Quantity Surveyor (MEP)": "Cost & Commercial",
            "Vice President – Contract Management (Building/Infrastructure)": "Contracts",
            "Project Handover & Closeout Manager": "Project Management",
            "Senior Urban Planner": None,
            "Senior Vice President - Master Planning": None,
            "Financial Planning & Analysis Manager": None,
            "Leasing Executive": None,
            "Project Controls Graduate": None,
            "IT Project Manager": None,
            "Software Delivery Project Manager": None,
            "Engineer - Planning": "Planning",
            "Project Manager (m/f/d) Architecture, Planning & Defense": None,  # defence is out of scope
            "Project Manager (m/f/d) Architecture & Planning": "Project Management",
            "Planning & Controls Manager": "Planning",
            "Senior Planning/Scheduling Engineer": "Planning",
            "Manager - Planning, Khalapur": "Planning",
            "Project Planning - Parel Project": "Planning",
            "Vice President - Project Management": "Project Management",
            "Senior Manager Projects-Data Center": "Project Management",
            "Director-Construction (JKT03)": "Project Management",
            "DGM - Costing & Budgeting (MEP)": "Cost & Commercial",
            "Senior Town Planner - Policy Planning": None,
        }
        for title, want in cases.items():
            self.assertEqual(discipline_of(title), want, title)

    def test_country(self):
        self.assertEqual(country_of("SA", "Medina"), "Saudi Arabia")
        self.assertEqual(country_of("", "NEOM, Tabuk Province"), "Saudi Arabia")
        self.assertEqual(country_of("", "Abu Dhabi"), "UAE")
        self.assertEqual(country_of("", "Doha"), "Qatar")
        self.assertEqual(country_of("CA", "Calgary"), "Canada")
        self.assertEqual(country_of("", "Tampa, FL"), "United States")
        self.assertEqual(country_of("", "London, United Kingdom"), "United Kingdom")
        self.assertEqual(country_of("GB", "Manchester"), "United Kingdom")
        self.assertEqual(country_of("", "Bengaluru, Karnataka, India"), "India")
        self.assertIsNone(country_of("", "Remote"))
        # US state and Canadian province codes are not country codes
        self.assertEqual(country_of("", "Chicago, IL"), "United States")   # not Israel
        self.assertEqual(country_of("", "Denver, CO"), "United States")    # not Colombia
        self.assertEqual(country_of("", "Indianapolis, IN"), "United States")  # not India
        self.assertEqual(country_of("", "Victoria, BC"), "Canada")
        self.assertEqual(country_of("", "Adelaide, SA"), "Australia")
        self.assertEqual(country_of("", "Riyadh, SA"), "Saudi Arabia")
        self.assertEqual(country_of("", "Sydney, New South Wales"), "Australia")
        self.assertEqual(country_of("", "Albuquerque, New Mexico"), "United States")

    def test_city(self):
        self.assertEqual(run.clean_city("Riyadh, Saudi Arabia", "Saudi Arabia"), "Riyadh")
        self.assertEqual(run.clean_city("Saudi Arabia", "Saudi Arabia"), "")
        self.assertEqual(run.clean_city("Other cities in Saudi Arabia", "Saudi Arabia"), "")
        self.assertEqual(run.clean_city("2 Locations", "Saudi Arabia"), "")
        self.assertEqual(run.clean_city("Abu Dhabi", "UAE"), "Abu Dhabi")

    def test_level(self):
        self.assertEqual(level_of("Project Controls Director"), "Director")
        self.assertEqual(level_of("Planning Manager"), "Manager")
        self.assertEqual(level_of("Senior Planner"), "Senior")
        self.assertEqual(level_of("Planning Engineer"), "Mid")
        self.assertEqual(level_of("Assistant Project Manager"), "Mid")
        self.assertEqual(level_of("Assistant Director - Planning"), "Director")

    def test_scope_and_titles(self):
        for t in ["Entry-Level Construction Manager", "Federal Programs Army Project Director", "PMO Digital Lead",
                  "Insurance Claims Adjuster", "Credit Risk Manager", "Project Manager (m/f/d) Planning & Defence"]:
            self.assertIsNone(discipline_of(t), t)
        self.assertEqual(discipline_of("Student Accommodation Project Manager"), "Project Management")
        self.assertEqual(discipline_of("Pre-Contract Quantity Surveyor"), "Cost & Commercial")
        self.assertEqual(discipline_of("Head of Planning"), "Planning")
        self.assertEqual(clean_title("Job Title: Cost Control Lead"), "Cost Control Lead")
        self.assertEqual(clean_title("Senior Project Manager (M3)"), "Senior Project Manager")
        self.assertEqual(clean_title("Planner (5990814)"), "Planner")

    def test_skills_read(self):
        from collector import skills
        sk, yrs = skills.read("<p>Minimum 12 years. Primavera P6, FIDIC, EOT claims, PMP.</p>")
        self.assertEqual(skills.labels(sk), ["Primavera P6", "EOT", "Claims", "FIDIC", "PMP"])
        self.assertEqual(yrs, 12)
        self.assertEqual(skills.read("short text")[0], "")

    def test_job_id_stable(self):
        self.assertEqual(job_id("AtkinsRéalis", "R-167472"), "atkinsrealis-r-167472")
        self.assertEqual(job_id("Turner & Townsend", "ABC"), "turner-and-townsend-abc")


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "site"))
        shutil.copy(os.path.join(HERE, "..", "employers.json"), self.tmp)
        self._root, run.ROOT = run.ROOT, self.tmp

    def tearDown(self):
        run.ROOT = self._root
        shutil.rmtree(self.tmp)

    def out(self):
        with open(os.path.join(self.tmp, "data", "jobs.json")) as f:
            return json.load(f)["jobs"]

    def test_replay_run(self):
        run.main(["--replay", os.path.join(HERE, "fixtures")])
        jobs = self.out()
        titles = sorted(j["title"] for j in jobs)
        self.assertEqual(titles, sorted([
            "Senior Associate - Development Projects Scheduling",
            "Vice President – Contract Management (Building/Infrastructure)",
            "Project Handover & Closeout Manager – Infrastructure",
            "Quantity Surveyor (MEP)",
            "Planning Engineer",
            "Project Controls Director",
            "Project Planner (Saudi National)",
            "Senior Estimator",             # WSP, Calgary - worldwide now
            "Senior Planner",               # Parsons, Tampa - worldwide now
            "Project Manager - Highways",   # AECOM, Manchester
        ]))
        # IT project manager is outside construction & infrastructure
        self.assertFalse(any(j["title"] == "IT Project Manager" for j in jobs))
        uk = next(j for j in jobs if j["title"] == "Project Manager - Highways")
        self.assertEqual((uk["country"], uk["region"], uk["city"]), ("United Kingdom", "Europe", "Manchester"))
        # every job links straight to its posting
        for j in jobs:
            self.assertTrue(j["url"].startswith("https://"), j)
            self.assertNotIn(j["url"].rstrip("/"), ["https://www.parsons.com", "https://aecom.com"])
        wd = next(j for j in jobs if j["title"] == "Project Controls Director")
        self.assertEqual(wd["url"], "https://parsons.wd5.myworkdayjobs.com/en-US/Search/job/Riyadh/Project-Controls-Director_R178431")
        # website data file written
        with open(os.path.join(self.tmp, "site", "jobs.js")) as f:
            self.assertTrue(f.read().startswith("window.JOBS_DATA = "))

    def test_closed_jobs_drop_and_first_seen_kept(self):
        fx = os.path.join(HERE, "fixtures")
        run.main(["--replay", fx])
        first = {j["id"]: j["firstSeen"] for j in self.out()}
        # second run: Aldar now lists only one job -> the other Aldar job is gone
        alt = os.path.join(self.tmp, "fx2")
        shutil.copytree(fx, alt)
        with open(os.path.join(alt, "aldar.json")) as f:
            d = json.load(f)
        key = next(iter(d))
        d[key] = d[key][:1]
        with open(os.path.join(alt, "aldar.json"), "w") as f:
            json.dump(d, f)
        run.main(["--replay", alt])
        second = {j["id"]: j["firstSeen"] for j in self.out()}
        self.assertFalse(any(k.startswith("aldar-4d233360") for k in second))
        for jid, seen in second.items():
            self.assertEqual(seen, first[jid])

    def test_failed_employer_keeps_recent_jobs(self):
        fx = os.path.join(HERE, "fixtures")
        run.main(["--replay", fx])
        alt = os.path.join(self.tmp, "fx3")
        shutil.copytree(fx, alt)
        os.remove(os.path.join(alt, "wsp.json"))  # WSP site "down"
        run.main(["--replay", alt])
        self.assertTrue(any(j["emp"] == "WSP" for j in self.out()))
        with open(os.path.join(self.tmp, "data", "run-report.md")) as f:
            self.assertIn("| WSP | FAILED |", f.read())

    def test_excluded_country(self):
        j = run.normalise({"name": "X"}, {"id": "1", "title": "Contract Manager", "location": "Tel Aviv",
                                          "url": "https://example.com/1"}, "2026-10-30")
        self.assertIsNone(j)

    def test_rejects_non_https_links(self):
        j = run.normalise({"name": "X"}, {"id": "1", "title": "Planning Manager", "location": "Riyadh",
                                          "url": "javascript:alert(1)"}, "2026-10-30")
        self.assertIsNone(j)

    def test_unconnected_employer_kept_and_drop_guard(self):
        fx = os.path.join(HERE, "fixtures")
        run.main(["--replay", fx])
        path = os.path.join(self.tmp, "data", "jobs.json")
        with open(path) as f:
            d = json.load(f)
        today = d["jobs"][0]["checked"]
        d["jobs"].append({"id": "mace-1", "title": "Planning Manager", "emp": "Mace", "type": "PMC", "disc": "Planning",
                          "level": "Manager", "city": "London", "country": "United Kingdom", "region": "Europe",
                          "url": "https://careers.macegroup.com/gb/en/job/1/x", "posted": "", "checked": today})
        # pretend AECOM had 40 roles last time; the replay finds 1, so the run must keep the old ones
        for i in range(40):
            d["jobs"].append({**d["jobs"][-1], "id": f"aecom-old{i}", "emp": "AECOM", "url": "https://jobs.smartrecruiters.com/AECOM2/x"})
        with open(path, "w") as f:
            json.dump(d, f)
        run.main(["--replay", fx])
        jobs = self.out()
        self.assertTrue(any(j["id"] == "mace-1" for j in jobs))
        self.assertEqual(sum(j["id"].startswith("aecom-old") for j in jobs), 40)


if __name__ == "__main__":
    unittest.main()


class Manual(unittest.TestCase):
    def test_parse(self):
        from collector import manual
        text = ("title,company,url,city,country,discipline,seniority,company_type,posted,featured_until,remove_after\n"
                "Senior Planner,Test Co,https://example.com/a,Riyadh,Saudi Arabia,,,Developer,2026-10-30,2026-11-30,\n"
                "Cost Manager,AECOM,https://example.com/b,Dubai,UAE,,,,,2026-10-01,\n"
                "# switched off,X,https://example.com/x,,,,,,,,\n"
                "Gone,Z,https://example.com/z,,,,,,,,2026-01-01\n"
                "No link,Q,,,,,,,,,\n")
        jobs, problems = manual.parse(text, "2026-10-31", {"AECOM": "PMC"})
        self.assertEqual([j["title"] for j in jobs], ["Senior Planner", "Cost Manager"])
        self.assertTrue(jobs[0]["featured"])
        self.assertEqual(jobs[0]["disc"], "Planning")
        self.assertNotIn("featured", jobs[1])  # featuring ended
        self.assertEqual(len(problems), 1)


class Facts(unittest.TestCase):
    def test_read(self):
        from collector import facts
        self.assertEqual(facts.read("Quantity Surveyor (Saudi National)"), {"elig": ["nat"]})
        f = facts.read("Senior Scheduler", "Must be a U.S. citizen. Secret clearance required. Salary range: $95,000 - $125,000 per year.")
        self.assertEqual(f["elig"], ["citizen", "clearance"])
        self.assertEqual(f["pay"], [95000, 125000, "USD", "year"])
        self.assertEqual(facts.read("Planner", "We are unable to provide visa sponsorship.")["elig"], ["nosponsor"])
        self.assertEqual(facts.read("Project Manager - Data Center")["sector"], ["datacentre"])
        self.assertNotIn("sector", facts.read("Planner", "Power BI dashboards. Power BI reports. Team building, building trust."))


def test_benefits_from_posting():
    from collector.facts import read
    gulf = ("Package: housing allowance, transport allowance, annual air tickets for you and your family, "
            "medical insurance, end of service gratuity and 30 days annual leave.")
    f = read("Senior Planner", gulf)
    assert {"housing", "transport", "flights", "medical", "family", "eosb", "leave"} <= set(f["ben"])
    assert f["leave"] == 30
    uk = "You will have experience with pension schemes. We offer 25 days holiday, a pension and private medical insurance."
    f = read("Cost Manager", uk)
    assert set(f["ben"]) == {"medical", "pension", "leave"} and f["leave"] == 25
    assert "ben" not in read("Project Manager", "Must have 10 years experience in P6 and FIDIC.")


def test_gulf_all_inclusive_package():
    from collector.facts import read
    f = read("Planner", "Salary: SAR 25,000 all-inclusive monthly package. Medical insurance and annual air ticket.")
    assert f["pay"] == [25000, 25000, "SAR", "month"]
    assert "inclusive" in f["ben"] and "flights" in f["ben"]


def test_job_pages_have_jobposting_data():
    import json, re
    from collector.pages import page
    j = {"id": "wsp-123", "title": "Senior Planner", "emp": "WSP", "city": "Riyadh", "country": "Saudi Arabia", "disc": "Planning",
         "level": "Senior", "type": "PMC", "posted": "2026-10-30", "checked": "2026-10-31", "url": "https://example.com/job/123"}
    h = page(j, "https://controlroles.com")
    ld = json.loads(re.search(r'application/ld\+json">(.*?)</script>', h, re.S).group(1))
    assert ld["@type"] == "JobPosting" and ld["validThrough"].startswith("2027-01-28")
    assert 'rel="canonical" href="https://controlroles.com/jobs/wsp-123.html"' in h


def test_requirements_reader():
    from collector.skills import read_full, labels
    f = read_full("Bachelor's degree in Civil Engineering or Quantity Surveying. Minimum 10 years of experience, "
                  "of which 5 years in the GCC. Primavera P6, FIDIC and PMP. Fluent English and Arabic.")
    assert f["yrs"] == 10 and "yrsMax" not in f and f["deg"] == "B:civil,qs"
    assert {"Primavera P6", "FIDIC", "PMP", "Arabic"} <= set(labels(f["sk"]))
    f = read_full("HNC or degree in Mechanical engineering with 8 to 12 years in planning")
    assert (f["yrs"], f["yrsMax"]) == (8, 12) and f["deg"] == "D:mechanical"
    assert "yrs" not in read_full("Great team, hybrid working.")


def test_requirement_lines_are_clean():
    from collector import reqlines
    text = ('<li type="disc">Degree in quantity surveying or cost management</li>'
            "<li>Here's what we're looking for: Minimum 8 years of planning experience on major projects</li>"
            '<li style="color:red">Join our award-winning culture today</li>')
    got = reqlines.lines(text)
    assert got[0] == "Degree in quantity surveying or cost management"
    assert got[1].startswith("Minimum 8 years")
    assert not any("culture" in l or "=" in l for l in got)


def test_peoplestrong_connector():
    from collector.connectors import peoplestrong
    page = {"totalRecords": 1, "response": [{"jobCode": "LNT/SE/1887692", "jobTitle": "Scheduling Engineer /1029/2B",
             "locationHierarchyComplete": "United Arab Emirates>Dubai>Latifa Bint Hamdan Street, Dubai",
             "jobPostedDate": "2026-10-29", "expRange": "3-8 years", "jobDetailUrl": "https://x.peoplestrong.com/job/detail/LNT_SE_1887692"}]}
    rows = peoplestrong.collect({"host": "x.peoplestrong.com"}, lambda url, data=None: page)
    assert rows[0]["id"] == "LNT_SE_1887692" and rows[0]["title"] == "Scheduling Engineer"
    assert rows[0]["country_hint"] == "United Arab Emirates" and rows[0]["posted"] == "2026-10-29"
    from collector import skills
    assert skills.years_of(peoplestrong.describe({}, rows[0], None)) == (3, 8)


def test_teamtailor_connector(monkeypatch):
    from collector.connectors import teamtailor
    rss = ('<rss xmlns:tt="https://teamtailor.com/locations"><channel><item><title>Delay Analyst</title>'
           '<link>https://careers.hka.com/jobs/8004760-delay-analyst?ref=rss</link><pubDate>Tue, 27 Oct 2026 19:15:47 +0000</pubDate>'
           '<description>&lt;p&gt;10+ years of planning experience&lt;/p&gt;</description>'
           '<tt:locations><tt:location><tt:city>Dubai</tt:city><tt:country>United Arab Emirates</tt:country></tt:location></tt:locations>'
           '</item></channel></rss>')
    monkeypatch.setattr(teamtailor, "_get", lambda url, fetch=None: rss)
    rows = teamtailor.collect({"host": "careers.hka.com"})
    assert rows[0]["id"] == "8004760" and rows[0]["location"] == "Dubai" and rows[0]["posted"] == "2026-10-27"
    assert "10+ years" in teamtailor.describe({}, rows[0])


def test_workday_30_plus_is_unknown_date():
    from collector.connectors import workday
    assert workday._posted("Posted 30+ Days Ago") == ""
    assert workday._posted("Posted 3 Days Ago") != ""


def test_regions_do_not_overlap():
    from collector.countries import region_of
    assert region_of("Saudi Arabia") == "GCC" and region_of("UAE") == "GCC"
    assert region_of("Jordan") == "Middle East (non-GCC)"


def test_job_page_survives_odd_records():
    from collector import pages
    odd = {"id": "x-1", "title": "Planner", "emp": "ACME", "country": "Saudi Arabia", "elig": None, "ben": None,
           "pay": [None, None], "url": "https://example.com", "posted": "bad"}
    html_ = pages.page(odd, "https://controlroles.com")
    assert '"addressCountry": "SA"' in html_ and "baseSalary" not in html_ and "datePosted" not in html_
