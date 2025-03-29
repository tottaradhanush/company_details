import google.generativeai as genai
import json
import os
import re
import time
import csv
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def extract_json_from_response(response_text):
    """Extract valid JSON from response text using regex or direct parsing."""
    try:
        return json.loads(response_text)  # Try direct JSON parsing
    except json.JSONDecodeError:
        # Extract JSON wrapped inside triple backticks (if present)
        json_match = re.search(r"```json\s*(\{.*\})\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
    return None  # Return None if JSON parsing fails

def extract_information(text):
    """Extract company details using Gemini AI."""
    prompt = """Extract the following details accurately from the given text:
    - Company's mission statement or core values
    - Products or services offered
    - Founding year and founders
    - Headquarters location
    - Key executives or leadership team members
    - Notable awards or recognitions
    Return the information as a **structured JSON object**.
    
    Example JSON format:
    ```json
    {
        "mission_statement": "Our mission is to innovate technology...",
        "products_or_services": ["AI Solutions", "Cloud Services"],
        "founding_year_and_founders": "Founded in 1995 by John Doe and Jane Smith.",
        "headquarters_location": "San Francisco, CA, USA",
        "key_executives": ["CEO: Alice Johnson", "CTO: Bob Martin"],
        "notable_awards": ["Best AI Company 2022", "Tech Innovation Award 2021"]
    }
    ```
    Ensure all fields are included.
    """

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([prompt, text])

        if not response or not response.text.strip():
            print("Empty response from API")
            return None

        # Extract valid JSON content
        cleaned_json = extract_json_from_response(response.text)

        if cleaned_json:
            return cleaned_json
        else:
            print("Gemini did not return valid JSON.")
            return None
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None

# Directory containing scraped text files
scraped_dir = "scraped_websites_text"
output_json = "company_details.json"
output_csv = "company_details.csv"

# Store extracted data in a dictionary
company_data = {}

for filename in os.listdir(scraped_dir):
    if filename.endswith(".txt"):
        # Extract company name and clean it
        company_name = filename.replace(".txt", "")
        company_name = re.sub(r"^www_|_com$", "", company_name)  

        with open(os.path.join(scraped_dir, filename), "r", encoding="utf-8") as file:
            scraped_text = file.read()

        extracted_info = extract_information(scraped_text)

        if extracted_info:
            company_data[company_name] = {
                "mission_statement": extracted_info.get("mission_statement", "N/A"),
                "products_or_services": extracted_info.get("products_or_services", ["N/A"]),
                "founding_year_and_founders": extracted_info.get("founding_year_and_founders", "N/A"),
                "headquarters_location": extracted_info.get("headquarters_location", "N/A"),
                "key_executives": extracted_info.get("key_executives", ["N/A"]),
                "notable_awards": extracted_info.get("notable_awards", ["N/A"])
            }
        else:
            print(f"Skipping {company_name}, failed to extract data.")

        time.sleep(2)  # Reduce delay to 2 seconds

# Print extracted data before writing to JSON
print("\nExtracted Company Data:\n", json.dumps(company_data, indent=4))


# Define CSV headers
csv_headers = [
    "company_name", "mission_statement", "products_or_services",
    "founding_year_and_founders", "headquarters_location",
    "key_executives", "notable_awards"
]

# Write extracted data to CSV file
with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    
    # Write header row
    writer.writerow(csv_headers)
    
    # Write company data rows
    for company, details in company_data.items():
        writer.writerow([
            company,
            details["mission_statement"],
            "; ".join(details["products_or_services"]),  # Join list elements with "; "
            details["founding_year_and_founders"],
            details["headquarters_location"],
            "; ".join(details["key_executives"]),  # Join list elements with "; "
            "; ".join(details["notable_awards"])  # Join list elements with "; "
        ])

print(f"\nExtracted details saved to {output_csv}")
