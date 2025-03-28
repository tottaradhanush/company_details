import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import pandas as pd
import time

# Headers to mimic a browser visit
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Directory to store text files
output_dir = "scraped_websites_text"
os.makedirs(output_dir, exist_ok=True)

# Updated relevant keywords for filtering links
RELEVANT_KEYWORDS = [
    "about", "company", "mission", "values", "ethics", "leadership", "management",
    "team", "founders", "history", "executive", "awards", "recognition", "vision",
    "principles", "board", "governance", "corporate", "innovation", "culture",
    "supplier", "location", "headquarters", "heritage", "about-us", "our-company",
    "linkedin", "company-overview", "company-profile", "who-we-are", "mission-statement"
]

# Function to clean extracted text
def clean_text(text):
    return " ".join(text.split()).strip()

# Function to extract text from a page
def extract_text_from_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted elements
        for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
            script.extract()

        # Extract cleaned text
        text = clean_text(soup.get_text())
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to get only the most relevant links
def get_relevant_links(base_url):
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        relevant_links = []
        visited_paths = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)

            # Ignore external links & PDFs
            if parsed_url.netloc != urlparse(base_url).netloc or full_url.lower().endswith(".pdf"):
                continue

            # Extract path without query parameters
            path_key = parsed_url.path.strip('/').split('?')[0]

            # Check if the link contains relevant keywords and avoid duplicate paths
            if any(keyword in href.lower() for keyword in RELEVANT_KEYWORDS) and path_key not in visited_paths:
                relevant_links.append(full_url)
                visited_paths.add(path_key)  # Store unique paths only

        return relevant_links
    except requests.exceptions.RequestException:
        return []

# Function to crawl only relevant pages (No Relevance Check)
def crawl_relevant_pages(base_url):
    relevant_links = get_relevant_links(base_url)
    visited_urls = set()
    all_text = ""

    for url in relevant_links:
        if url in visited_urls:
            continue

        print(f"Scraping: {url}")
        visited_urls.add(url)

        # Extract text content (No filtering)
        page_text = extract_text_from_url(url)
        if page_text:
            all_text += f"\n{page_text}"

        time.sleep(1)  # Respectful scraping

    return all_text

# Load URLs from Excel file
file_path = "urls2.xlsx"  # Adjust the path if needed
df = pd.read_excel(file_path, header=None)

url_column = 1  
set_column = 2  

filtered_df = df.iloc[4:, [url_column, set_column]].dropna(how="all")
filtered_df.columns = ["Website URL", "URL Set"]  # Rename columns

# Clean "URL Set" and forward-fill missing values
filtered_df["URL Set"] = pd.to_numeric(filtered_df["URL Set"], errors="coerce")
filtered_df["URL Set"] = filtered_df["URL Set"].fillna(method="ffill").astype(int)

# Filter URLs for Set 3
set_number = 3
set_3_urls = filtered_df[filtered_df["URL Set"] == set_number]["Website URL"].tolist()

# Main execution
if __name__ == "__main__":
    for base_url in set_3_urls:
        print(f"Starting website crawl for: {base_url}")
        merged_text = crawl_relevant_pages(base_url)

        # Save to a text file (one per website)
        website_name = urlparse(base_url).netloc.replace(".", "_")
        output_file = os.path.join(output_dir, f"{website_name}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(merged_text)

    print("Scraping complete. Text data saved in 'scraped_websites_text' folder.")

