




import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import pandas as pd
import time
import google.generativeai as genai  
import re

from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

output_dir = "scraped_websites_text"
os.makedirs(output_dir, exist_ok=True)

# Function to clean text
def clean_text(text):
    return " ".join(text.split()).strip()

# Function to extract text from a page
def extract_text_from_url(url):
    try:
        print(f"Fetching text from: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
            script.extract()

        return clean_text(soup.get_text())
    except requests.exceptions.RequestException as e:
        print(f" Error fetching {url}: {e}")
        return None

# Function to get all internal links up to a specified depth
def get_all_links(base_url, max_depth=1, visited=None):
    if visited is None:
        visited = set()

    if max_depth < 1:
        return visited  

    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        new_links = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)

            if parsed_url.netloc != urlparse(base_url).netloc or full_url.lower().endswith(".pdf"):
                continue

            if full_url not in visited:
                visited.add(full_url)
                new_links.add(full_url)

        return visited  
    except requests.exceptions.RequestException:
        return visited

# Function to filter relevant links using Gemini AI
def filter_relevant_links(links, questions):
    print(f" Sending {len(links)} links to Gemini for filtering...")

    if not links:
        return []

    prompt = f"""
    Given these website links, check the description of each link and filter out the most relevant ones based on the following questions:

    Questions:
    {questions}

    Links:
    {links}

    Output ONLY a Python list of the most relevant links, nothing else.
    """

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    raw_text = response.text.strip()
    print("\n RAW GEMINI RESPONSE:\n", raw_text, "\n")

    cleaned_text = re.sub(r"```python|```", "", raw_text).strip()

    try:
        relevant_links = eval(cleaned_text)
        if isinstance(relevant_links, list) and all(link.startswith("http") for link in relevant_links):
            print(f" Gemini filtered {len(relevant_links)} relevant links.")
            return relevant_links
        else:
            print(" Gemini did not return a valid list of links.")
            return []
    except Exception as e:
        print(f" Error parsing Gemini response: {e}")
        return []

# Crawl relevant pages
def crawl_relevant_pages(base_url, questions):
    homepage_links = get_all_links(base_url, max_depth=1)  # Get Level 1 links
    print(f" Found {len(homepage_links)} Level 1 links on {base_url}")

    # Filter Level 1 links using Gemini AI
    relevant_links = filter_relevant_links(list(homepage_links), questions)
    
    if not relevant_links:
        print(f" No relevant links found for {base_url}")
        return ""

    # Deep crawl inside relevant links to extract more links
    all_links = set(relevant_links)  
    for relevant_link in relevant_links:
        deep_links = get_all_links(relevant_link, max_depth=1)  # Crawl inside each relevant link
        all_links.update(deep_links)

    print(f" Found {len(all_links)} total links after deep crawling.")

    # Send all collected links back to Gemini for final filtering
    final_relevant_links = filter_relevant_links(list(all_links), questions)

    if not final_relevant_links:
        print(f" No final relevant links found after deep crawling for {base_url}")
        return ""

    visited_urls = set()
    all_text = ""

    for url in final_relevant_links:
        if url in visited_urls:
            continue

        visited_urls.add(url)
        page_text = extract_text_from_url(url)
        if page_text:
            all_text += f"\n{page_text}"

        time.sleep(1)

    return all_text

# Load URLs from Excel file
file_path = "urls2.xlsx"
df = pd.read_excel(file_path, header=None)

url_column = 1  
set_column = 2  

filtered_df = df.iloc[4:, [url_column, set_column]].dropna(how="all")
filtered_df.columns = ["Website URL", "URL Set"]

filtered_df["URL Set"] = pd.to_numeric(filtered_df["URL Set"], errors="coerce")
filtered_df["URL Set"] = filtered_df["URL Set"].fillna(method="ffill").astype(int)

set_number = 3
set_3_urls = filtered_df[filtered_df["URL Set"] == set_number]["Website URL"].tolist()

questions = """
1. What is the company's mission statement or core values?
2. What products or services does the company offer?
3. When was the company founded, and who were the founders?
4. Where is the company's headquarters located?
5. Who are the key executives or leadership team members?
6. Has the company received any notable awards or recognitions?
"""

# Main execution
if __name__ == "__main__":
    for base_url in set_3_urls:
        print(f"\n Starting deep crawl for: {base_url}")
        filtered_text = crawl_relevant_pages(base_url, questions)

        if filtered_text:
            website_name = urlparse(base_url).netloc.replace(".", "_")
            output_file = os.path.join(output_dir, f"{website_name}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(filtered_text)

            print(f" Data saved for {base_url}")

    print("\n Scraping complete. Check 'scraped_websites_text' folder.")
