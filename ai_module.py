# ai_module.py

import os
import json
import traceback
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
import base64
import io
import tempfile
import time

load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class AIAnalysis(BaseModel):
    CorrectedDescription: str = Field(..., description="A professionally rephrased and spell-checked version of the original observation.")
    ImpactOnOperations: str = Field(..., description="Potential impact on operations, safety, or compliance.")
    Likelihood: int = Field(..., ge=1, le=5, description="An integer from 1 (very unlikely) to 5 (very likely).")
    Severity: int = Field(..., ge=1, le=5, description="An integer from 1 (minor) to 5 (critical).")
    CorrectiveAction: str = Field(..., description="A clear, actionable recommendation.")
    DeadlineSuggestion: str = Field(..., description="A realistic deadline (e.g., 'Immediately', '24 Hours', '1 Week').")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        ai_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("AI Module: Gemini 1.5 Pro AI Model initialized successfully.")
    except Exception as e:
        print(f"AI Module ERROR: Could not initialize Gemini: {e}")
        ai_model = None
else:
    print("AI Module WARNING: GEMINI_API_KEY not found in .env file.")
    ai_model = None

def get_ai_analysis(observation_text, area_equipment, industry):
    error_response = {k: "AI Error - Model Not Initialized" for k in AIAnalysis.model_fields.keys()}
    if not ai_model:
        return error_response

    if not industry:
        industry = "General"

    prompt = f"""
    Analyze the following safety observation from the '{industry}' industry.
    Area/Equipment: "{area_equipment}"
    Original Observation: "{observation_text}"

    Your task is to return a SINGLE, VALID JSON object. Do NOT include any text or markdown formatting before or after the JSON object.

    The JSON object must have the following keys:
    1.  "CorrectedDescription": A professionally rephrased and spell-checked version of the original observation.
    2.  "ImpactOnOperations": Describe the potential impact on operations, safety, or compliance.
    3.  "Likelihood": An integer from 1 (very unlikely) to 5 (very likely).
    4.  "Severity": An integer from 1 (minor) to 5 (critical).
    5.  "CorrectiveAction": A clear, actionable recommendation.
    6.  "DeadlineSuggestion": Suggest a realistic deadline (e.g., "Immediately", "24 Hours", "1 Week").
    """
    try:
        flash_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = flash_model.generate_content(prompt)
        raw_ai_text = response.text.strip()

        cleaned_response_text = raw_ai_text
        if cleaned_response_text.startswith("```json"):
            cleaned_response_text = cleaned_response_text[len("```json"):].strip()
        if cleaned_response_text.endswith("```"):
            cleaned_response_text = cleaned_response_text[:-len("```")].strip()

        if not (cleaned_response_text.startswith("{") and cleaned_response_text.endswith("}")):
            first_brace = cleaned_response_text.find('{')
            last_brace = cleaned_response_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                cleaned_response_text = cleaned_response_text[first_brace : last_brace + 1]
            else:
                raise json.JSONDecodeError("No valid JSON structure found in AI response.", cleaned_response_text, 0)

        parsed_json_data = json.loads(cleaned_response_text)
        validated_data = AIAnalysis.model_validate(parsed_json_data)
        return validated_data.model_dump()

    except (json.JSONDecodeError, ValidationError) as je:
        print(f"AI Module JSON/Validation Error: {je}\nText that failed: {cleaned_response_text[:500]}\n{traceback.format_exc()}")
        error_response.update({k: f"AI Error (Parsing)" for k in error_response})
        return error_response
    except Exception as e:
        print(f"AI Module Error in get_ai_analysis: {e}\n{traceback.format_exc()}")
        error_response.update({k: f"AI Error (General)" for k in error_response})
        return error_response

def upload_file_to_gemini(file_content, file_name, mime_type):
    """
    Starts the file upload process to the Gemini API.
    
    IMPORTANT: This function is now NON-BLOCKING. It initiates the upload
    and returns immediately. The file will be in a "PROCESSING" state.
    The calling function is responsible for checking when the file becomes "ACTIVE".
    """
    if not ai_model:
        raise ConnectionError("AI Model is not initialized.")

    temp_path = None
    try:
        decoded_bytes = base64.b64decode(file_content.split(',')[1])

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_name.split('.')[-1]}") as temp_file:
            temp_file.write(decoded_bytes)
            temp_path = temp_file.name

        print(f"Uploading {file_name} from temp path: {temp_path}...")

        # This call initiates the upload but does not wait for it to complete.
        gemini_file = genai.upload_file(path=temp_path, mime_type=mime_type, display_name=file_name)
        
        print(f"Successfully sent {file_name} for upload. State: {gemini_file.state.name}. Gemini File ID: {gemini_file.name}")
        
        # --- CRITICAL FIX ---
        # The original blocking `while` loop has been removed to prevent tying up the server.
        # In a production environment, you should use a background task queue (e.g., Celery with Redis)
        # to handle the polling for 'ACTIVE' status.
        # For this fix, the status check is handled in the calling function (`ask_ai_app.py`)
        # to keep the app functional without adding new dependencies.
        
        return gemini_file

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"Removed temp file: {temp_path}")

def delete_ai_file(gemini_file_id):
    print(f"Deleting file {gemini_file_id} from Gemini service...")
    try:
        genai.delete_file(name=gemini_file_id)
        print(f"Successfully deleted {gemini_file_id}.")
    except Exception as e:
        print(f"Warning: Could not delete file {gemini_file_id} from Gemini. It may have already been removed. Error: {e}")

def get_answer_from_docs(file_objects, user_question, location=None):
    if not ai_model:
        raise ConnectionError("AI Model is not initialized.")

    location_context = f"The user's specified location is '{location}'." if location else "No specific location has been provided."

    prompt = f"""
You are a specialized regulatory and legal research assistant. Your role is to provide full, accurate answers to regulatory, safety, or legal questions using both uploaded documents and your own external research.

**User’s Location Context:** {location_context}

**Answering Rules and Expectations:**

1. **Identify the Regulatory Requirement**
   - Clearly identify what rule, specification, or requirement the user is asking about.
   - Do not restate or summarize the question — answer it directly.

2. **Use All Available Sources**
   - If relevant content is found in uploaded files, extract the specific requirement or clause.
   - If not found in the documents, use your internal knowledge base and external authoritative sources to identify the correct standard or requirement.
   - You must find and include the **actual requirement**, not just references to where it might be found.

3. **Answer Directly, With No Deferral**
   - Do not suggest that the user “consult” or “refer to” a code.
   - Do not say a rule “depends” or is “context-specific” unless legally accurate to do so, and always provide typical or default requirements when possible.
   - Do not say “based on research” without providing the actual content of the regulation.

4. **Always Include the Following:**
   - The **exact requirement or rule**, including specific numbers or thresholds.
   - The **rationale** behind the rule (e.g., fire suppression effectiveness, health risk reduction, evacuation safety).
   - The **exact source citation**, including code name, edition/year, and section or clause number.

5. **Formatting and Output Rules**
   - Use **Markdown**.
   - Use **numbered lists** for steps and procedures.
   - Use **bulleted lists** for conditions, options, or rules.
   - Use **tables** for standards, values, or comparisons.
   - Do not include commentary about files, OCR, image formats, or internal AI processes.

**Important:**
You must provide a complete, usable, self-contained answer. Never redirect the user to find the answer elsewhere. If you have the data, give the rule. If not in the uploaded file, find it and provide it. Always give clear, referenced, professional answers.
    ---
    **User's Question:** "{user_question}"
    """

    try:
        contents_for_api = [prompt, *file_objects]
        response = ai_model.generate_content(contents_for_api)
        return response.text
    except Exception as e:
        print(f"AI Module Error in get_answer_from_docs: {e}\n{traceback.format_exc()}")
        raise ConnectionError(f"An error occurred while generating the AI response: {e}")