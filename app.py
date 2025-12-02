import os
import json
import pandas as pd
from pypdf import PdfReader
import google.generativeai as genai

# --- CONFIGURATION ---
API_KEY = "you-api-key-here"
MODEL_NAME = "gemini-2.0-flash" 

# --- 1. FILE READING ---
def extract_text_from_pdf(pdf_path):
    """
    Reads the PDF file and merges all pages into one long string.
    """
    try:
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        return full_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

# --- 2. QUERY GEMINI ---
def query_gemini_for_structured_data(text_content):
    """
    Sends text to Google Gemini 2.0 Flash to get perfect JSON.
    """
    if "YOUR_GOOGLE_API_KEY_HERE" in API_KEY:
        print("❌ Error: You forgot to paste your Google API Key in the code!")
        return None

    genai.configure(api_key=API_KEY)
    
    generation_config = {
        "temperature": 0.1,
        "response_mime_type": "application/json", # Forces Gemini to output JSON
    }

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        system_instruction="""
        You are an expert Data Extraction AI. 
        Your task is to convert the user's resume text into a structured JSON list.
        
        RULES:
        1. Extract 100% of the information. Do not summarize or omit anything.
        2. Format the output as a LIST of objects.
        3. Each object must have these keys: "Category", "Key", "Value", "Comments".
        4. "Comments" should include the tag found in the text.
        """
    )

    try:
        response = model.generate_content(text_content)
        # Since we enforced JSON mode, response.text should be valid JSON.
        return json.loads(response.text)

    except Exception as e:
        print(f"Error querying Gemini: {e}")
        return None

# --- 3. MAIN EXECUTION ---
def main():
    input_file = "Data Input.pdf"
    output_file = "Candidate_Output.xlsx"
    
    print(f"--- Processing {input_file} ---")
    
    raw_text = extract_text_from_pdf(input_file)
    if not raw_text:
        return

    print(f"Sending text to {MODEL_NAME}...")
    
    json_data = query_gemini_for_structured_data(raw_text)

    if json_data:
        print("✅ Data received! Generating Excel...")
        
        df = pd.DataFrame(json_data)
        
        # Organize and filter columns
        cols = ["Category", "Key", "Value", "Comments"]
        final_cols = [c for c in cols if c in df.columns]
        df = df[final_cols]
            
        df.to_excel(output_file, index=False)
        print(f"✅ Success! File saved as {output_file}")
    else:
        print("❌ Failed to get data.")

if __name__ == "__main__":
    main()
