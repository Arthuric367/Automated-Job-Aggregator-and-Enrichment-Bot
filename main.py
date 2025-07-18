"""
Job Aggregator Bot: Enhanced Logging Example
--------------------------------------------

This version demonstrates how to use the new logging function for detailed diagnostics.

Usage of the new logging function:
- Use `log_job_scrape_start(website)` when starting to scrape a website.
- Use `log_jobs_found(website, count)` after scraping, before filtering.
- Use `log_jobs_matched(website, count)` after filtering.
- Use `log_jobs_rejected(website, rejected_jobs)` where `rejected_jobs` is a list of dicts:
    Each dict: {"title": ..., "reasons": [reason1, reason2, ...]}
- For each rejected job, use `log_job_rejection(website, job_title, reasons)` if you want per-job granularity.

Example log output (using the new logging function):
2025-07-02 10:27:45,117 [INFO] Scraping LinkedIn for jobs...
2025-07-02 10:27:45,117 [INFO] LinkedIn: 25 jobs found before filtering.
2025-07-02 10:27:45,117 [INFO] LinkedIn: 3 jobs matched all criteria.
2025-07-02 10:27:45,117 [INFO] LinkedIn: 22 jobs rejected. Reasons:
2025-07-02 10:27:45,117 [INFO]   - Job 'Backend Developer' rejected: location mismatch (expected 'Remote', got 'Onsite')
2025-07-02 10:27:45,117 [INFO]   - Job 'Data Analyst' rejected: salary below minimum (expected >= 60000, got 50000)

Note: Replace previous ad-hoc logging with these functions in your scraping and filtering code.

Example logging function definitions (place in your logging module):
"""

def log_job_scrape_start(website):
    logging.info(f"Scraping {website} for jobs...")

def log_jobs_found(website, count):
    logging.info(f"{website}: {count} jobs found before filtering.")

def log_jobs_matched(website, count):
    logging.info(f"{website}: {count} jobs matched all criteria.")

def log_jobs_rejected(website, rejected_jobs):
    logging.info(f"{website}: {len(rejected_jobs)} jobs rejected. Reasons:")
    for job in rejected_jobs:
        title = job.get("title", "Unknown")
        for reason in job.get("reasons", []):
            logging.info(f"  - Job '{title}' rejected: {reason}")

def log_job_rejection(website, job_title, reasons):
    for reason in reasons:
        logging.info(f"{website}: Job '{job_title}' rejected: {reason}")

"""
Automated Job Aggregator and Enrichment Bot
-------------------------------------------
Main application entry point.

Features:
- Loads user configuration (job title, location, salary, currency, etc.)
- Scrapes job listings from LinkedIn, JobsDB, Glassdoor
- Enriches job data with company background (Perplexity API)
- Benchmarks salary (Glassdoor)
- Stores structured data in Google Sheet
- Supports on-demand and scheduled runs
- Logs activities and errors

Note: This is a high-level scaffold. Each component should be implemented in its own module/file for production use.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# --- CONFIGURATION ---

CONFIG_FILE = "config.json"
LOG_FILE = "job_aggregator.log"

# --- LOGGING SETUP ---

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# --- USER CONFIGURATION ---

def load_config(config_path: str = CONFIG_FILE) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        # Create a template config if not exists
        template = {
            "job_keywords": ["Software Engineer", "Data Scientist"],
            "location": "Remote",
            "salary_range": "60000-80000",
            "currency": "USD",
            "schedule": None,  # e.g., "daily 08:00"
            "notification": {
                "email": None,
                "slack_webhook": None
            }
        }
        with open(config_path, "w") as f:
            json.dump(template, f, indent=2)
        print(f"Config file created at {config_path}. Please edit it and re-run.")
        sys.exit(0)
    with open(config_path, "r") as f:
        return json.load(f)

# --- SCRAPERS (STUBS) ---

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time

def get_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_linkedin(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    logging.info("Scraping LinkedIn for jobs...")
    jobs = []
    driver = get_webdriver()
    try:
        keywords = "+".join(config.get("job_keywords", []))
        location = config.get("location", "Remote")
        url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0"
        driver.get(url)
        time.sleep(3)
        job_cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")
        for card in job_cards:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "h3")
                company_elem = card.find_element(By.CSS_SELECTOR, "h4")
                location_elem = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                link_elem = card.find_element(By.CSS_SELECTOR, "a")
                job = {
                    "job_title": title_elem.text.strip(),
                    "company_name": company_elem.text.strip(),
                    "location": location_elem.text.strip(),
                    "source_link": link_elem.get_attribute("href"),
                    "source": "LinkedIn"
                }
                jobs.append(job)
            except NoSuchElementException:
                continue
    except Exception as e:
        logging.error(f"LinkedIn scraping error: {e}")
    finally:
        driver.quit()
    logging.info(f"LinkedIn: {len(jobs)} jobs found before filtering.")
    return jobs

def scrape_jobsdb(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    logging.info("Scraping JobsDB for jobs...")
    jobs = []
    driver = get_webdriver()
    try:
        keywords = "+".join(config.get("job_keywords", []))
        location = config.get("location", "")
        url = f"https://www.jobsdb.com/en-hk/jobs/{keywords}/{location}"
        driver.get(url)
        time.sleep(3)
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.sx2jih0.zcydq8h")
        for card in job_cards:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "a.sx2jih0.zcydq84.zcydq8h._17fduda0._17fduda7._17fduda7._17fduda7")
                company_elem = card.find_element(By.CSS_SELECTOR, "span.sx2jih0.zcydq84.zcydq8h._17fduda0._17fduda7._17fduda7._17fduda7")
                location_elem = card.find_element(By.CSS_SELECTOR, "span.sx2jih0.zcydq84.zcydq8h._17fduda0._17fduda7._17fduda7._17fduda7+span")
                job = {
                    "job_title": title_elem.text.strip(),
                    "company_name": company_elem.text.strip(),
                    "location": location_elem.text.strip(),
                    "source_link": title_elem.get_attribute("href"),
                    "source": "JobsDB"
                }
                jobs.append(job)
            except NoSuchElementException:
                continue
    except Exception as e:
        logging.error(f"JobsDB scraping error: {e}")
    finally:
        driver.quit()
    logging.info(f"JobsDB: {len(jobs)} jobs found before filtering.")
    return jobs

def scrape_glassdoor(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    logging.info("Scraping Glassdoor for jobs...")
    jobs = []
    driver = get_webdriver()
    try:
        keywords = "+".join(config.get("job_keywords", []))
        location = config.get("location", "")
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keywords}&locT=C&locId=&locKeyword={location}"
        driver.get(url)
        time.sleep(3)
        job_cards = driver.find_elements(By.CSS_SELECTOR, "li.react-job-listing")
        for card in job_cards:
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "a.jobLink span")
                company_elem = card.find_element(By.CSS_SELECTOR, "div.jobHeader a")
                location_elem = card.find_element(By.CSS_SELECTOR, "span.pr-xxsm")
                link_elem = card.find_element(By.CSS_SELECTOR, "a.jobLink")
                job = {
                    "job_title": title_elem.text.strip(),
                    "company_name": company_elem.text.strip(),
                    "location": location_elem.text.strip(),
                    "source_link": link_elem.get_attribute("href"),
                    "source": "Glassdoor"
                }
                jobs.append(job)
            except NoSuchElementException:
                continue
    except Exception as e:
        logging.error(f"Glassdoor scraping error: {e}")
    finally:
        driver.quit()
    logging.info(f"Glassdoor: {len(jobs)} jobs found before filtering.")
    return jobs

# --- ENRICHMENT (STUBS) ---

def enrich_company_background(company_name: str) -> Dict[str, Any]:
    # TODO: Integrate with Perplexity API
    logging.info(f"Enriching company background for {company_name}...")
    return {
        "industry": None,
        "company_size": None,
        "year_founded": None,
        "notable_info": None
    }

def benchmark_salary(job_title: str, location: str) -> Dict[str, Any]:
    # TODO: Integrate with Glassdoor or other salary APIs
    logging.info(f"Benchmarking salary for {job_title} in {location}...")
    return {
        "average_salary": None,
        "comparison": None  # "above", "below", "within"
    }

# --- GOOGLE SHEETS INTEGRATION (STUB) ---

def append_to_google_sheet(job_entries: List[Dict[str, Any]]):
    # TODO: Implement Google Sheets API integration
    logging.info(f"Appending {len(job_entries)} jobs to Google Sheet...")
    pass

def is_duplicate(job: Dict[str, Any], existing_jobs: List[Dict[str, Any]]) -> bool:
    for existing in existing_jobs:
        if (job["job_title"] == existing["job_title"] and
            job["company_name"] == existing["company_name"] and
            job["source_link"] == existing["source_link"]):
            return True
    return False

# --- MAIN BOT LOGIC ---

def aggregate_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    all_jobs = []
    for scraper in [scrape_linkedin, scrape_jobsdb, scrape_glassdoor]:
        try:
            jobs = scraper(config)
            all_jobs.extend(jobs)
        except Exception as e:
            logging.error(f"Error scraping: {scraper.__name__}: {e}")
    logging.info(f"Total jobs scraped: {len(all_jobs)}")
    return all_jobs

def enrich_and_store_jobs(jobs: List[Dict[str, Any]], config: Dict[str, Any]):
    enriched_jobs = []
    # TODO: Load existing jobs from Google Sheet to check for duplicates
    existing_jobs = []  # Placeholder
    for job in jobs:
        if is_duplicate(job, existing_jobs):
            continue
        # Enrich company background
        company_info = enrich_company_background(job.get("company_name", ""))
        job.update(company_info)
        # Salary benchmarking
        salary_info = benchmark_salary(job.get("job_title", ""), job.get("location", ""))
        job.update(salary_info)
        # Add timestamp
        job["scraped_at"] = datetime.utcnow().isoformat()
        enriched_jobs.append(job)
    append_to_google_sheet(enriched_jobs)
    logging.info(f"Enriched and stored {len(enriched_jobs)} new jobs.")

# --- SCHEDULING (SIMPLE LOOP) ---

def run_bot(config: Dict[str, Any]):
    logging.info("Job Aggregator Bot started.")
    jobs = aggregate_jobs(config)
    enrich_and_store_jobs(jobs, config)
    logging.info("Job Aggregator Bot finished.")

def main():
    config = load_config()
    if config.get("schedule"):
        # Simple scheduling: run at specified time daily
        import schedule
        schedule_time = config["schedule"]  # e.g., "daily 08:00"
        # TODO: Parse schedule_time and set up schedule
        print("Scheduling not fully implemented. Running once for now.")
        run_bot(config)
    else:
        run_bot(config)

if __name__ == "__main__":
    main()
