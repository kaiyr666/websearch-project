import os
from serpapi import GoogleSearch
from openai import AsyncOpenAI
import json

# Initialize OpenAI Async Client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_jobs_serp(query: str, location: str, limit: int = 50):
    """
    Searches for jobs using SerpApi with pagination.
    """
    all_jobs = []
    start = 0
    
def search_jobs_serp(query: str, location: str, limit: int = 50):
    """
    Searches for jobs using SerpApi with token-based pagination.
    """
    all_jobs = []
    next_page_token = None
    
    print(f"[DEBUG] Starting SerpApi Search. Query: '{query}', Location: '{location}', Target Limit: {limit}")

    # Helper to clean params
    def get_params(token=None, use_date=True):
        p = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "api_key": os.getenv("SERPAPI_API_KEY"),
        }
        if use_date:
            p["chips"] = "date_posted:today"
        
        if token:
            p["next_page_token"] = token
        
        return p

    strict_mode = True # Try with date filter first
    
    while len(all_jobs) < limit:
        params = get_params(next_page_token, strict_mode)
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            jobs_results = results.get("jobs_results", [])
            
            # Fallback Logic on First Page
            if not jobs_results and not next_page_token and strict_mode:
                print("[DEBUG] Strict 'today' filter returned 0 jobs. Retrying without date filter...")
                strict_mode = False
                continue # Retry same page (token is None) without date

            if not jobs_results:
                print(f"[DEBUG] No more jobs found.")
                # Debug info if error
                if "error" in results:
                    print(f"[DEBUG] SerpApi Error: {results['error']}")
                break
                
            all_jobs.extend(jobs_results)
            print(f"[DEBUG] Fetched {len(jobs_results)} jobs. Total so far: {len(all_jobs)}")
            
            # Pagination
            pagination = results.get("serpapi_pagination", {})
            next_page_token = pagination.get("next_page_token")
            
            if not next_page_token:
                print("[DEBUG] No next_page_token found. End of results.")
                break
                
        except Exception as e:
            print(f"[DEBUG] SerpApi Error: {e}")
            break
            
    return all_jobs[:limit]

async def analyze_job_match(resume_text: str, job_description: str, job_title: str):
    """
    Uses AsyncOpenAI to analyze the match between resume and job description.
    Returns: { "score": int, "justification": str }
    """
    # ... (rest of the function remains similar but we can add logging if needed, 
    # currently main.py handles the result logging)
    
    prompt = f"""
    You are an expert recruiter. Analyze the fit between the following Resume and Job Description.
    
    Job Title: {job_title}
    
    Job Description (Markdown): 
    {job_description[:15000]}... (truncated if necessary)
    
    Resume Content: 
    {resume_text[:4000]}... (truncated)
    
    Task:
    1. Determine a Match Score (0-100) based on skills, experience, and requirements.
    2. Provide a "Justification" (max 2 sentences) explaining WHY.
    
    Output JSON only: {{ "score": <int>, "justification": "<string>" }}
    """

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a JSON-only outputting assistant. Be strict with JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"[DEBUG] OpenAI Analysis Error for '{job_title}': {e}")
        return {"score": 0, "justification": f"Error analyzing match: {str(e)}"}
