import asyncio
import os
from dotenv import load_dotenv

# Force load .env from the parent directory where it logicall is
# Current path: .../backend/verify_backend.py
# .env path: .../.env
from pathlib import Path
current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

from services.job_search import search_jobs_serp, analyze_job_match
from services.jina_reader import fetch_job_content

async def run_verification():
    print("--- 1. Testing Environment Variables ---")
    print(f"SERPAPI_API_KEY present: {bool(os.getenv('SERPAPI_API_KEY'))}")
    print(f"OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
    print(f"JINA_API_KEY present: {bool(os.getenv('JINA_API_KEY'))}")

    print("\n--- 2. Testing SerpApi (limit=2) ---")
    jobs = search_jobs_serp("Software Engineer", "San Francisco, CA", limit=2)
    print(f"Result count: {len(jobs)}")
    if jobs:
        first_job = jobs[0]
        print(f"First Job Found: {first_job.get('title')} at {first_job.get('company_name')}")
        
        # Test Jina on this job
        print("\n--- 3. Testing Jina AI Reader ---")
        link = first_job.get("share_link") or first_job.get("apply_options", [{}])[0].get("link")
        if link:
            print(f"Fetching content for: {link}")
            content = await fetch_job_content(link)
            print(f"Content Length: {len(content)} chars")
            print(f"Preview: {content[:100]}...")
            
            # Test OpenAI
            print("\n--- 4. Testing OpenAI Analysis ---")
            dummy_resume = "Skilled Software Engineer with Python and React experience."
            analysis = await analyze_job_match(dummy_resume, content, first_job.get('title'))
            print(f"Analysis Result: {analysis}")
        else:
            print("Skipping Jina/OpenAI test because first job had no link.")

    else:
        print("CRITICAL: SerpApi returned 0 jobs.")

if __name__ == "__main__":
    asyncio.run(run_verification())
