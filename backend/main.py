import os
from dotenv import load_dotenv

# Load environment variables early - BEFORE importing services that might use them at module level 
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import asyncio
from services.job_search import search_jobs_serp, analyze_job_match
from services.jina_reader import fetch_job_content
from services.resume_parser import parse_resume_content
from database.db import init_db, save_search, save_job, get_search_history, get_jobs_by_search

# Initialize FastAPI app
app = FastAPI(title="Job Search Agent API")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    await init_db()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"], # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Client (Sync for simple chat init)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a helpful job search assistant.")

class ChatInitResponse(BaseModel):
    message: str

# Duplicate imports removed

class SearchRequest(BaseModel):
    roles: str
    country: str
    resume_text: str

@app.get("/")
async def root():
    return {"status": "ok", "message": "Job Search Agent Backend is running"}

@app.post("/chat/init", response_model=ChatInitResponse)
async def chat_init():
    """
    Generates an initial greeting using the LLM based on the system prompt.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "Generate a warm, professional, and concise greeting. Ask for Job Roles and Target Country."}
            ],
            max_tokens=150
        )
        greeting = response.choices[0].message.content
        return ChatInitResponse(message=greeting)
    except Exception as e:
        print(f"Error generating greeting: {e}")
        return ChatInitResponse(message="Hello! I'm your AI Job Search Assistant. What roles are you looking for and in which country?")

@app.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """
    Parses a PDF resume and returns the text.
    """
    text = await parse_resume_content(file)
    return {"text": text}

@app.post("/search-jobs")
async def search_jobs(request: SearchRequest):
    """
    Searches for jobs and analyzes match with resume using Jina AI for deep content.
    Fetches up to 50 jobs via pagination and analyzes them with concurrency control.
    """
    print(f"Searching for {request.roles} in {request.country}...")
    
    # 1. Search SerpApi (Sync but handles pagination internally)
    # Fetch up to 50 jobs
    jobs = search_jobs_serp(request.roles, request.country, limit=50)
    
    if not jobs:
        return {"jobs": []}

    # 2. Analyze Matches using Jina + OpenAI (Async/Parallel with Semaphore)
    print(f"Found {len(jobs)} jobs. Analyzing...")

    # Semaphore to limit concurrent requests to avoid rate limits
    semaphore = asyncio.Semaphore(10)

    async def process_job(job):
        async with semaphore:
            title = job.get("title", "Unknown Role")
            company = job.get("company_name", "Unknown")
            
            # FIX: Priority - apply_link > related_links > share_link
            link = (
                job.get("apply_link") or
                (job.get("related_links", [{}])[0].get("link") if job.get("related_links") else None) or
                job.get("share_link")
            )
            
            if not link:
                # print(f"[DEBUG] Skipping {title} - No link found.")
                return None

            # Fetch content with Jina
            # print(f"[DEBUG] Fetching content for: {title}...")
            description_markdown = await fetch_job_content(link)
            
            if not description_markdown:
                 # Fallback to snippet if Jina fails
                 # print(f"[DEBUG] Jina failed for {title}, using snippet.")
                 description_markdown = job.get("description", "")

            # Analyze with LLM
            # print(f"[DEBUG] Analyzing match for: {title}...")
            analysis = await analyze_job_match(request.resume_text, description_markdown, title)
            
            score = analysis.get("score", 0)
            # print(f"[DEBUG] Analyzed {title}: Score {score}")

            if score >= 70: # Strong match threshold
                print(f"[DEBUG] >>> FOUND MATCH: {title} at {company} (Score: {score})")
                return {
                    "role": title,
                    "company": company,
                    "link": link,
                    "score": score,
                    "justification": analysis.get("justification")
                }
            return None

    # Limit to top 50 (already limited by SerpApi call but good safety)
    print(f"[DEBUG] Starting concurrent processing of {len(jobs)} jobs...")
    tasks = [process_job(job) for job in jobs]
    analyzed_jobs = await asyncio.gather(*tasks)
    
    # Filter out Nones
    final_results = [job for job in analyzed_jobs if job is not None]
    
    # Sort by score
    final_results.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"[DEBUG] --- Search Complete ---")
    print(f"[DEBUG] Found {len(final_results)} strong matches.")
    
    # Save to database
    search_id = await save_search(request.roles, request.country, request.resume_text)
    for job in final_results:
        await save_job(search_id, job)
    print(f"[DEBUG] Saved {len(final_results)} jobs to database (search_id={search_id})")
    
    return {"jobs": final_results}


@app.get("/search-history")
async def get_history():
    """
    Returns recent search history with job counts.
    """
    history = await get_search_history(limit=10)
    return {"history": history}

@app.get("/search-results/{search_id}")
async def get_results(search_id: int):
    """
    Returns jobs for a specific search ID.
    """
    jobs = await get_jobs_by_search(search_id)
    return {"jobs": jobs}
