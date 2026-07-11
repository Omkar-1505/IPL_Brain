import time
import os
import json
import csv
import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from curl_cffi import requests

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LINKS_FILE = os.path.join(BASE_DIR, "2026_links.txt")
CATCHES_CSV = os.path.join(BASE_DIR, 'master_ipl_catches.csv')
DROPS_CSV = os.path.join(BASE_DIR, 'all_drops_raw.csv')
FAILED_LOG = os.path.join(BASE_DIR, 'failed_matches.log')

def get_processed_match_ids(filename):
    if not os.path.exists(filename): return set()
    ids = set()
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.add(row['match_id'])
    return ids

def scavenger_hunt(data_obj, wickets, drops, match_id, match_players):
    """Hunts the commentary JSON arrays for dropped catches and wickets."""
    if isinstance(data_obj, dict):
        text_node = data_obj.get('commentText') or data_obj.get('text') or data_obj.get('title')
        if text_node:
            raw_html = text_node.get('html', '') if isinstance(text_node, dict) else str(text_node)
            clean_text = raw_html if raw_html.startswith('http') else BeautifulSoup(raw_html, 'html.parser').get_text()

            if clean_text.strip():
                # Catch Drop Detection (Only found in commentary)
                drop_match = re.search(r'(?:dropped|put down) by ([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)', clean_text)
                if drop_match:
                    drops.append({
                        'match_id': match_id, 'over': data_obj.get('oversActual', 'Unknown'), 
                        'fielder': drop_match.group(1).strip(), 'bowler': 'Unknown', 'commentary': clean_text
                    })

        for val in data_obj.values():
            scavenger_hunt(val, wickets, drops, match_id, match_players)
    elif isinstance(data_obj, list):
        for item in data_obj:
            scavenger_hunt(item, wickets, drops, match_id, match_players)

def scorecard_hunter(data_obj, wickets, match_id):
    """Hunts the hidden Scorecard JSON to guarantee we extract 100% of the wickets."""
    if isinstance(data_obj, dict):
        # The magic key: ESPNcricinfo stores the exact text like "c Kohli b Siraj" here
        if 'dismissalText' in data_obj and data_obj.get('isOut'):
            text = str(data_obj.get('dismissalText', '')).strip()
            batsman = data_obj.get('player', {}).get('longName', 'Unknown')
            
            if text and text.lower() != 'not out':
                # Prevent duplicates
                if not any(w.get('batsman') == batsman for w in wickets):
                    wickets.append({
                        'match_id': match_id,
                        'over': 'Scorecard',
                        'batsman': batsman,
                        'bowler': text, # Storing the full dismissal string here for parsing
                        'dismissal': 'caught' if 'c ' in text.lower() or 'caught' in text.lower() else 'other',
                        'commentary': text
                    })
                    
        for val in data_obj.values():
            scorecard_hunter(val, wickets, match_id)
    elif isinstance(data_obj, list):
        for item in data_obj:
            scorecard_hunter(item, wickets, match_id)

def scrape_match(url, match_id):
    try:
        resp = requests.get(url, impersonate="chrome", timeout=15)
        if resp.status_code != 200: raise Exception(f"HTTP {resp.status_code}")
        
        wickets, drops, players = [], [], set()
        
        # 1. Bypass BeautifulSoup and rip the JSON out using Regex
        json_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text, re.DOTALL)
        if json_match:
            json_data = json.loads(json_match.group(1))
            scavenger_hunt(json_data, wickets, drops, match_id, players) # Gets the drops
            scorecard_hunter(json_data, wickets, match_id) # GUARANTEES the wickets
            
        # 2. The Ultimate Safety Net (Raw Text Scan)
        if not wickets and not drops:
            clean_text = re.sub(r'<style.*?</style>|<script.*?</script>|<[^>]+>', ' ', resp.text, flags=re.DOTALL)
            
            # Wicket Fallback
            wicket_matches = re.finditer(r'(?:\bc\b|\bcaught\b)\s+([^\s]+(?:\s[^\s]+)?)\s+\bb\b\s+([A-Z][a-z]+)', clean_text)
            for match in wicket_matches:
                wickets.append({'match_id': match_id, 'over': 'Fallback', 'batsman': 'Unknown', 'bowler': match.group(2), 'dismissal': 'caught', 'commentary': match.group(0)})
                
            # Drops Fallback
            drop_matches = re.finditer(r'((?:dropped|put down) by ([A-Z][a-z]+(?:\s[A-Z][a-z]+)?))', clean_text)
            for match in drop_matches:
                drops.append({'match_id': match_id, 'over': 'Fallback', 'fielder': match.group(2).strip(), 'bowler': 'Unknown', 'commentary': match.group(1)})
        
        if not wickets and not drops: 
            print(f"   -> Warning: Found 0 wickets/drops. Might be rain-abandoned.")
            
        return wickets, drops
    except Exception as e:
        with open(FAILED_LOG, 'a') as f: f.write(f"{match_id} | {url} | {e}\n")
        print(f"   -> ERROR: {e}")
        return None, None

def save_to_csv(data, file):
    if not data: return
    file_exists = os.path.exists(file)
    with open(file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if not file_exists: writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    processed_ids = get_processed_match_ids(CATCHES_CSV)
    
    with open(LINKS_FILE, 'r') as f: 
        urls = [l.strip() for l in f if l.strip()]
    
    print(f"Found {len(urls)} links. {len(processed_ids)} already processed.")
    
    for idx, url in enumerate(urls, 1):
        mid = str(idx)
        if mid in processed_ids: 
            continue
        
        print(f"Scraping Match {mid}/{len(urls)}...")
        w, d = scrape_match(url, mid)
        
        if w is not None:
            # FIXED FILTER: Now checks the actual commentary text for 'caught' or 'c '
            caught_only = []
            for wicket in w:
                text_to_check = str(wicket.get('dismissal', '')) + " " + str(wicket.get('commentary', ''))
                if 'caught' in text_to_check.lower() or 'c ' in text_to_check.lower():
                    caught_only.append(wicket)

            if caught_only: 
                save_to_csv(caught_only, CATCHES_CSV)
                print(f"   -> Saved {len(caught_only)} catches.")
            else:
                print(f"   -> Saved 0 catches.")
                
            if d: 
                save_to_csv(d, DROPS_CSV)
                print(f"   -> Saved {len(d)} drops!")
        
        time.sleep(2)