
import google.generativeai as genai
import json
import csv
import os
import re
import time  # Import time module for delay

# Configure Gemini API Key
genai.configure(api_key="AIzaSyCdBk2we_8zBFhzhi_QJqzr1qywXMGqqxo")  # Replace with actual API key

def extract_json_from_response(response_text):
    """Extracts valid JSON from response text using regex."""
    json_match = re.search(r"```json\s*(\{.*\})\s*```", response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)  # Extract JSON content inside triple backticks
    return response_text.strip()  # Assume response is JSON without formatting

def extract_information(text):
    """Extracts company details using Gemini AI."""
    prompt = """Extract the following details from the given text,fetch the data accurately:
    - Company's mission statement or core values
    - Products or services offered
    - Founding year and founders
    - Headquarters location
    - Key executives or leadership team members
    - Notable awards or recognitions
    Provide structured JSON output without extra text or formatting."""
    
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([prompt, text])

        if not response or not response.text.strip():
            print("Error: Empty response from API")
            return None

        # Extract valid JSON content
        cleaned_json = extract_json_from_response(response.text)

        # Ensure valid JSON
        return json.loads(cleaned_json)
    
    except json.JSONDecodeError:
        print("Error: Invalid JSON response")
        return None
    except Exception as e:
        print(f"Error extracting data: {str(e)}")
        return None

# Directory containing scraped text files
scraped_dir = "scraped_websites_text"
output_csv = "company_details.csv"

# Prepare CSV headers
csv_headers = [
    "Company", "Mission Statement", "Products/Services", "Founded Year & Founders",
    "Headquarters", "Leadership", "Awards/Recognitions"
]

# Process and extract data
company_data = []

for filename in os.listdir(scraped_dir):
    if filename.endswith(".txt"):
        company_name = filename.replace(".txt", "")  # Extract company name
        with open(os.path.join(scraped_dir, filename), "r", encoding="utf-8") as file:
            scraped_text = file.read()

        extracted_info = extract_information(scraped_text)

        if extracted_info:
            company_data.append([
                company_name,
                extracted_info.get("mission_statement", "N/A"),
                ", ".join(map(str, extracted_info.get("products_or_services") or ["N/A"])),
                extracted_info.get("founding_year_and_founders", "N/A"),
                extracted_info.get("headquarters_location", "N/A"),
                ", ".join(map(str, extracted_info.get("key_executives") or ["N/A"])),
                ", ".join(map(str, extracted_info.get("notable_awards") or ["N/A"]))
            ])
        else:
            print(f"Skipping {company_name}, failed to extract data.")

        time.sleep(3)  # Introduce a 3-second delay between API requests

# Write extracted data to CSV
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(csv_headers)  # Write headers
    writer.writerows(company_data)  # Write data

print(f"Extracted details saved to {output_csv}")


