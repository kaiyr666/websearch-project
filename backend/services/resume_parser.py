from fastapi import UploadFile, File, HTTPException
import pypdf
import io

async def parse_resume_content(file: UploadFile) -> str:
    """
    Extracts text from a persistent PDF file or an in-memory UploadFile.
    """
    if file.content_type not in ["application/pdf", "application/x-pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")
    
    try:
        content = await file.read()
        pdf_file = io.BytesIO(content)
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Basic cleanup: remove excessive whitespace
        return text.strip()
    except Exception as e:
        print(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse resume content.")
