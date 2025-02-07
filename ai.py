import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def search_on_gemini(role, company, interviewer_type, difficulty_level, company_type):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = json.load(open("prompts/prompts.json"))
    response = model.generate_content(
        prompt.get('interviewer').format(
            role=role, difficulty_level=difficulty_level, 
            company=company, interviewer_type=interviewer_type, 
            company_type=company_type
        )
    )
    results = json.loads(response.text)
    return results
