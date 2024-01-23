from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup, Comment
import re 
import json
from urllib.parse import urljoin, urlparse

def save_to_json(data, filename='scraped_data2.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def process_url(url, driver, existing_urls, level):
    print(f'Processing {url} at level {level}')
    try:
        # Load the page
        driver.get(url)
        time.sleep(2)  # Wait for JavaScript to render

        # Get the page source
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extracting text only from the body tag
        body = soup.find('body')
        
        # If body tag is found, proceed to filter out divs with an ID containing 'cookie'
        if body:
            # Find all div tags with ID containing 'cookie'
            cookie_divs = body.find_all('div', id=re.compile(r'cookie', re.IGNORECASE))

            # Remove these divs from the body
            for div in cookie_divs:
                div.decompose()

            # Extracting text only from the modified body
            texts = body.get_text(separator=' ', strip=True)
        else:
            texts = 'No body text found'

        # Extracting all unique links and filtering out mailto links
        unique_links = set()
        for a in body.find_all('a', href=True) if body else []:
            full_url = urljoin(url, a['href'])
            parsed_link = urlparse(full_url)
            if not a['href'].startswith('mailto:') and parsed_link.scheme and parsed_link.netloc:
                unique_links.add(full_url)

        # Extracting the title and description
        title = soup.title.string if soup.title else 'No title found'
        description = None
        if soup.find("meta", {"name": "description"}):
            description = soup.find("meta", {"name": "description"})["content"]
        elif soup.find("meta", {"property": "og:description"}):
            description = soup.find("meta", {"property": "og:description"})["content"]
        description = description or 'No description found'

        # Add the URL to the set of existing URLs
        existing_urls.add(url)

        return {"url": url, "title": title, "description": description, "texts": texts, "links": list(unique_links), "level": level}
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return {"url": url, "error": str(e), "level": level}


# Set up the Selenium WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Starting URL
start_url = "https://businesshalland.se"

# Data to store scraped information
data = []
existing_urls = set()

# Load existing data if available
try:
    with open('scraped_data2.json', 'r') as f:
        existing_data = json.load(f)
    data.extend(existing_data)
    existing_urls.update([page['url'] for page in existing_data])
except FileNotFoundError:
    print("No existing file found. Starting fresh.")

# Process the starting URL if not already processed
if start_url not in existing_urls:
    start_data = process_url(start_url, driver, existing_urls, 1)
    data.append(start_data)
    save_to_json(data)

# Process links at each level
current_level = 1
max_level = 3  # Set the maximum depth level here

while current_level <= max_level:
    for page in [p for p in data if p["level"] == current_level]:
        for link in page["links"]:
            if link not in existing_urls:
                link_data = process_url(link, driver, existing_urls, current_level + 1)
                if link_data:  # Check if link_data is not None
                    data.append(link_data)
                    save_to_json(data)
                    if "links" in link_data:  # Additional check for 'links' key in link_data
                        next_level_links = set(link_data["links"])
                        existing_urls.update(next_level_links)

    current_level += 1

# Close the driver
driver.quit()