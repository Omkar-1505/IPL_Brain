<div align="center">

# IPL Tactical Command Center & AI Coach

[![React](https://img.shields.io/badge/React-18.2.0-blue.svg?style=for-the-badge&logo=react)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg?style=for-the-badge&logo=python)](#)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC.svg?style=for-the-badge&logo=tailwind-css)](#)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-AI-orange.svg?style=for-the-badge&logo=google)](#)

</div>

> [!IMPORTANT]  
> **The Project Vision:** In modern franchise cricket, standard analytical platforms focus solely on baseline quantitative metrics (runs, averages, strike rates). This project bridges the industry gap by introducing **Qualitative AI Intelligence**. It provides a professional-grade dashboard that simulates Head-to-Head matchups, abstracts hidden fielding data, and utilizes artificial intelligence to **autonomously draft optimal playing XIs** based on empirical vulnerabilities.

---

## 🛑 Core Challenges Encountered & Solved

Building a centralized intelligence hub required overcoming several critical data engineering bottlenecks:

1. **Hidden Fielding Data:** Standard cricket databases do not track granular fielding metrics such as "dropped catches by specific field positions."
   * *Resolution:* Developed the `NLP Regex Extractor` to parse unstructured text and autonomously build a proprietary dataset.
2. **Bot-Protected Data:** Major sports networks utilize sophisticated security (e.g., Cloudflare) to block automated data scrapers.
   * *Resolution:* Engineered an `Anti-Bot Evasion Pipeline` utilizing high-level browser impersonation headers to securely access restricted HTML.
3. **Data Fragmentation:** A player's current auction franchise, historical ball-by-ball metrics, and qualitative tactical flaws exist in completely isolated formats.
   * *Resolution:* Implemented the `Ultra-Merge Algorithm` in React to normalize names and fuse these disparate datasets into a unified player profile.

---

## ⚙️ Technology Stack

### Frontend Architecture
* **Core Framework:** `React 18` paired with `Vite` for rapid module bundling.
* **Styling & Animation:** `Tailwind CSS v4` for fluid, responsive layouts and `Framer Motion` for hardware-accelerated transitions.
* **Data Visualization:** `Recharts` for rendering phase-based match analytics.

### Backend Data Engineering
* **Data Processing:** `Pandas` and `NumPy` for high-performance vectorized operations.
* **Web Scraping:** `curl_cffi` (for TLS fingerprint spoofing) and `Playwright` (for executing hidden Javascript tabs).
* **Text Parsing:** `BeautifulSoup4` and Python's native `re` (Regular Expressions) module.

### Artificial Intelligence
* **Language Model:** `Google Generative AI SDK (Gemini 1.5 Flash)` for high-speed tactical abstraction.
* **Transcript Extraction:** `youtube-transcript-api` for pulling raw coach analysis dialogue.

---

## 🧠 Processes & Algorithms

The backend intelligence is driven by a multi-stage data abstraction pipeline:

### 1. Hard Data Extraction (`Ball-by-Ball Processing Algorithm`)
The system ingests massive CSV datasets (e.g., `ipl_ball_by_ball.csv`) containing hundreds of thousands of historical deliveries. 
* Uses **Pandas Aggregation** to calculate baseline metrics.
* Applies a **Death Over Filter** (overs 16-20) to calculate specific **Pressure Strike Rates** and **Pressure Economy**.
* Generates a **Head-to-Head Matrix** to identify the `Top 3 Target Bowlers` and `Top 3 Nightmare Batters` for every player based on strike rate and dismissal frequency thresholds.

### 2. Web Scraping (`Recursive JSON Hunter`)
Cricket websites nest live commentary inside deeply nested, frequently changing JSON blocks injected into the DOM.
* **Impersonation:** The `curl_cffi` module mimics legitimate user sessions to fetch the raw HTML.
* **Recursion:** The `Recursive JSON Hunter` algorithm iterates through the `__NEXT_DATA__` tree. Instead of relying on brittle, hardcoded dictionary keys, it dynamically searches for string values containing commentary formats, making the scraper resistant to website architecture changes.

### 3. NLP Fielding Abstraction (`Regex Metric Engine`)
Once raw commentary is extracted into JSON, it must be quantified.
* The engine applies **Dynamic Pattern Matching** to cross-reference text against 20+ standard fielding zones.
* It searches for linguistic markers (e.g., *"dropped by [Name]"* or *"spills a sitter at point"*).
* Generates `fielding_analysis.csv`, assigning every player a quantifiable **Strong Zone** and a **Liability Zone**.

### 4. AI Tactical Enrichment (`Coach Tape Generator`)
* Pulls raw subtitle text from post-match analysis broadcasts.
* Instructs the **Gemini LLM** to ignore irrelevant dialogue and extract pure tactical insight.
* Forces the AI to output a strictly formatted JSON array detailing specific bowling and batting countermeasures, which is then mapped directly to the player profiles.

---

## 🖥️ User Interface (UI) Modules

The React frontend operates as a premium tactical command center, divided into three core operational modules:

### 1. `The War Room` (Drafting & Simulation)
* **Match Configurations:** Users define the exact parameters, selecting the Stadium and the Opposing Franchise.
* **Opponent Selection:** Users lock in the opposing 11 to 15 players.
* **Intelligent Auto-Drafting:** Triggering the **Coach Review** prompts the `AI Drafting Algorithm` to evaluate the user's available franchise pool. It calculates impact scores based on historical strike rates and wicket-taking ability to autonomously draft the optimal **Playing XI** and **Impact Substitutes** tailored to defeat the selected opponent.

### 2. `Clash Arena` (1v1 Combat Simulator)
* A specialized module for granular **Head-to-Head** analysis.
* Users pair any Batter/All-Rounder against any Bowler.
* The UI outputs a simultaneous, dual-sided tactical brief advising the bowler on where to pitch the ball, and advising the batter on how to survive that specific bowler's death-over variations.

### 3. `Master Stats Hub` (Player Diagnostics)
* A comprehensive, searchable global player directory.
* Renders highly detailed profile cards showcasing:
  * Normalized Full Names and Nationalities.
  * **Venue Diagnostics** (Best to Worst performing stadiums).
  * **Fielding Intelligence** (Optimal deployment zones vs. Liability zones).
  * AI-generated **Coach's Tape Suggestions**.

> [!NOTE]
> **Deployment Protocol:** Ensure the compiled master databases (`players.csv`, `fielding_analysis.csv`, and `teams.csv`) are placed securely in the `public/` directory of the React application before mounting the development server.
```eof
