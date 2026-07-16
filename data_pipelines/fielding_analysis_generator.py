import json
import csv
import pandas as pd
import re
import os
from collections import defaultdict, Counter

# MAPPING: Standardize names to ensure Rohit Sharma, R Sharma, and Rohit are the same person.
# Add any missing names here if you notice they are still splitting.
NAME_MAP = {
    "R Sharma": "Rohit Sharma", "Rohit": "Rohit Sharma",
    "S Yadav": "Suryakumar Yadav", "SKY": "Suryakumar Yadav",
    "H Pandya": "Hardik Pandya", "Hardik": "Hardik Pandya",
    "J Bumrah": "Jasprit Bumrah", "Bumrah": "Jasprit Bumrah",
    "I Kishan": "Ishan Kishan", "Kishan": "Ishan Kishan",
    "M Dhoni": "MS Dhoni", "Dhoni": "MS Dhoni",
    "V Kohli": "Virat Kohli", "Kohli": "Virat Kohli",
    "A de Villiers": "AB de Villiers", "ABD": "AB de Villiers",
    "G Maxwell": "Glenn Maxwell", "Maxwell": "Glenn Maxwell",
    "F du Plessis": "Faf du Plessis", "Faf": "Faf du Plessis",
    "S Iyer": "Shreyas Iyer", "Iyer": "Shreyas Iyer",
    "S Narine": "Sunil Narine", "Narine": "Sunil Narine",
    "A Russell": "Andre Russell", "Russell": "Andre Russell",
    "R Pant": "Rishabh Pant", "Pant": "Rishabh Pant",
    "D Warner": "David Warner", "Warner": "David Warner",
    "K Rahul": "KL Rahul", "Rahul": "KL Rahul",
    "S Dhawan": "Shikhar Dhawan", "Dhawan": "Shikhar Dhawan",
    "S Gill": "Shubman Gill", "Gill": "Shubman Gill"
}

def normalize(name):
    return NAME_MAP.get(name.strip(), name.strip())

# Strict list of real fielding positions
VALID_POSITIONS = [
    'slip', 'gully', 'point', 'cover', 'extra cover', 'mid-off', 
    'mid-on', 'mid-wicket', 'square leg', 'fine leg', 'third man'
]

def analyze_fielding():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_store = defaultdict(lambda: {'catches': 0, 'drops': 0, 'pos_catches': Counter()})

    # 1. Process JSONs (2021-2026)
    json_files = ['2021.json', '2022.json', '2023.json', '2024.json', '2025.json', '2026.json']
    for jfile in json_files:
        path = os.path.join(BASE_DIR, jfile)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for match in data:
                    for error in match.get('fielding_errors', []):
                        if error.get('error_type') == 'Dropped Catch':
                            name = normalize(error.get('fielder', 'Unknown'))
                            data_store[name]['drops'] += 1

    # 2. Process Highlights CSV (2008-2020)
    csv_path = os.path.join(BASE_DIR, 'IPL_Match_Highlights_Commentary.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        pattern = re.compile(r'(?:caught|c|dropped)\s+(?:by\s+)?([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:at|in|near)\s+([a-z\s]+)', re.IGNORECASE)
        
        for text in df['Commentary'].dropna():
            match = pattern.search(str(text))
            if match:
                name = normalize(match.group(1).strip())
                pos = match.group(2).strip().lower()
                if 'dropped' in str(text).lower():
                    data_store[name]['drops'] += 1
                else:
                    data_store[name]['catches'] += 1
                    data_store[name]['pos_catches'][pos] += 1

    # 3. Export Authentic Data
    with open('fielding_analysis_final.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Player_Name', 'Primary_Fielding_Position', 'Total_Catches', 'Total_Drops'])
        for name, stats in data_store.items():
            primary_pos = stats['pos_catches'].most_common(1)[0][0].title() if stats['pos_catches'] else "Unknown"
            writer.writerow([name, primary_pos, stats['catches'], stats['drops']])

    print("✅ fielding_analysis_final.csv generated.")

if __name__ == "__main__":
    analyze_fielding()