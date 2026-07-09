import requests
from bs4 import BeautifulSoup
import time
import os # <-- Add the 'os' module here
import re # <-- Add regex module for URL extraction
from curl_cffi import requests

def crawl_season_links(season_results_url, output_filename="season_links.txt"):
    """
    Crawls the Cricinfo Results page to find all 'ball-by-ball' links.
    Saves them to a text file for the scraper to consume.
    """
    
    print(f"Crawling: {season_results_url}")
    
    # Added a try-except block to handle server drops without crashing the whole program
    try:
        # We use impersonate="chrome" to perfectly fake the browser fingerprint and bypass the 403
        response = requests.get(season_results_url, impersonate="chrome", timeout=15)
    except Exception as e:
        print(f"❌ Connection error while trying to reach the site. Skipping...")
        print(f"Error details: {e}\n")
        return
    
    if response.status_code != 200:
        print(f"Failed to access results page. Status: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    match_urls = []
    
    # Extract the exact series slug (e.g., 'ipl-2026-1510719') from the input URL
    series_slug_match = re.search(r'/series/([^/]+)', season_results_url)
    series_slug = series_slug_match.group(1) if series_slug_match else "[^/]+"
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # PRO-TRICK: Dynamic Regex that STRICTLY matches the current series AND contains '-vs-'
        # This ignores news articles, points tables, and other tournaments entirely!
        match = re.search(rf'(/series/{series_slug}/[^/]+-vs-[^/]+-\d+)', href)
        if match:
            base_match_url = match.group(1)
            full_url = f"https://www.espncricinfo.com{base_match_url}/ball-by-ball-commentary"
            
            if full_url not in match_urls:
                match_urls.append(full_url)
    
    # BULLETPROOF PATH LOGIC: Get the exact directory where crawler.py lives
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Strip away any bad folder names from the dictionary and just keep the filename
    safe_filename = os.path.basename(output_filename) 
    final_save_path = os.path.join(script_dir, safe_filename)
    
    with open(final_save_path, 'w') as f:
        for url in match_urls:
            f.write(url + '\n')
            
    print(f"Successfully found {len(match_urls)} matches. Saved to {final_save_path}\n")

if __name__ == "__main__":
    # Example of putting MULTIPLE Season URLs!
    # Because of the fix above, you only need to put the filename now!
    seasons_to_crawl = {
        "2026_links.txt": "https://www.espncricinfo.com/series/ipl-2026-1510719/match-results",
        # You can add older seasons here once you find their exact match-results URLs!
        # "2025_links.txt": "...",
    }

    print("Starting batch crawl for multiple seasons...\n")
    
    for output_file, url in seasons_to_crawl.items():
        crawl_season_links(url, output_filename=output_file)
        time.sleep(3) # CRITICAL: Wait 3 seconds between seasons so we don't look like a bot!
        
    print("All seasons crawled successfully!")