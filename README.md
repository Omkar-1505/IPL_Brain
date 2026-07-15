IPLBrain: Elite Tactical Command Center

[!IMPORTANT]
IPLBrain is an advanced tactical dashboard designed for T20 Cricket Franchise Head Coaches and analytical departments. It moves beyond standard quantitative analytics and introduces Qualitative AI Intelligence. By parsing historical match commentary, isolating fielding errors, and analyzing coach's tape, the system simulates one-on-one matchups and auto-drafts optimal playing XIs based on empirical data.

The Importance of the Project

[!NOTE]
The Industry Gap: In modern T20 cricket, data is highly fragmented. Analytics teams can easily ascertain baseline metrics (such as runs and strike rates), but they often struggle to quantify the specific methods of scoring, isolate fielding liabilities by exact field position, or determine the precise bowling tactics that induce false shots.

Problems Encountered & Solved

Hidden Fielding Data: Standard databases do not track "dropped catches by fielding position."

Resolution: This project builds a proprietary dataset by extracting this specific metric from unstructured text.

Bot-Protected Data: Major cricket repositories utilize heavy security (e.g., Cloudflare) to block automated scrapers.

Resolution: This project implements advanced anti-bot bypass techniques to securely access necessary data without detection.

Data Silos: A player's current mega-auction team, historical metrics, and tactical flaws are stored in completely different formats and locations.

Resolution: IPLBrain consolidates these into a centralized analytical hub using a normalized ultra-merge algorithm.

[!TIP]
The Unified Solution: IPLBrain acts as a centralized command center. It scrapes live text commentary, utilizes Natural Language Processing (NLP) to extract fielding errors, employs Google Gemini to formulate tactical countermeasures, and visualizes the aggregated data in a high-performance React dashboard.

Technology Stack

Backend Data Pipeline (Python)

Data Processing: pandas, numpy

Anti-Bot Web Scraping: curl_cffi (impersonates standard browser headers to bypass 403 Forbidden errors), playwright (headless browser automation), beautifulsoup4

Natural Language Processing (NLP): Python re (Regex Engine)

AI Integration: google-generativeai (Gemini 1.5 Flash), youtube-transcript-api

Frontend UI Architecture (React)

Framework: React 18 + Vite

Styling: Tailwind CSS (Fluid responsive design, dynamic gradients)

Animations: framer-motion

Data Visualization: recharts

Icons: lucide-react

Core Processes & Algorithms

The backend intelligence engine is powered by four distinct data pipelines:

1. Hard Data Extraction

Using Pandas, the engine processes over 250,000+ historical deliveries (ipl_ball_by_ball.csv) to calculate baseline metrics.

Death Over Algorithms: Filters data for overs >= 15 to calculate "Pressure Strike Rates" and "Pressure Economy."

Head-to-Head Matchups: Groups data by striker and bowler. It applies a minimum statistical threshold (e.g., 12 balls faced) and sorts by Strike Rate and Dismissals to isolate the Top 3 "Dangerous Bowlers" and "Nightmare Batters" for every player.

2. Anti-Bot Web Scraping

Cricket websites often nest their commentary inside complex JSON blocks injected into the HTML.

The Impersonator: Using curl_cffi with impersonate="chrome", the script mimics a legitimate human browser session to fetch raw HTML without triggering security protocols.

Recursive JSON Hunting: A recursive Python function iterates through the __NEXT_DATA__ JSON tree, extracting any string that resembles ball-by-ball commentary text, avoiding the brittleness of hardcoded dictionary keys.

3. NLP Fielding Abstraction

Once the raw commentary text is extracted, an NLP engine scans it for proprietary fielding metrics.

Regex Pattern Matching: It utilizes dynamic Regular Expressions to identify phrases cross-referenced against 20+ standard fielding zones.

Output: Generates fielding_analysis.csv, assigning every player an optimal "Strong Zone" and a quantifiable "Liability Zone."

4. AI Tactical Enrichment

Coach's Tape Generation: Scripts scrape post-match analysis transcripts, feeding them to a Large Language Model. The AI structures this unstructured text into strict JSON arrays detailing tactical approaches against specific players.

Missing Data Fallback: A REST API script automatically queries the AI to identify full names and nationalities for uncapped rookies drafted in the 2026 Mega Auction.

Frontend UI Architecture

The React application merges teams.csv (the current roster truth), players.csv (historical stats and tactics), and fielding_analysis.csv using a Normalized Surname "Ultra-Merge" algorithm. It powers three primary modules:

1. The Tactical War Room

Match Modes: Custom Match or IPL Match modes with stadium selection.

The Draft: Users select 15 opponent players.

AI Auto-Draft (Coach Review): An algorithm evaluates the user's available franchise pool, calculating an impact score based on Strike Rate and Wicket-taking ability to automatically draft the optimal Playing XI and 5 Impact Subs to counter the selected opponents.

Strategic Matchup Grid: Generates dynamic analysis cards showing specific pace and spin plans for the selected opponent players.

2. Clash Arena (1v1 Combat Simulator)

Allows analysts to simulate any Batter or All-Rounder vs. any Bowler or All-Rounder matchup.

Dynamically filters the UI based on established roles.

Displays simultaneous countermeasures, factoring in the selected stadium's pitch conditions.

3. Master Stats Hub

A responsive, searchable player directory.

Displays comprehensive profile cards featuring:

Full Name, Nationality, and Current Franchise.

Death Over vs. Overall metrics.

Best Stadiums and optimal fielding deployments.

Head-to-Head Nemesis data.

[!WARNING]
Deployment Instructions

Backend Generation: Execute the Python scripts inside the /backend/data_pipeline/ directory to scrape data and generate the required CSV files.

Frontend Initialization: Ensure players.csv, fielding_analysis.csv, and teams.csv are placed in the public/ directory of the React application before running npm run dev.
