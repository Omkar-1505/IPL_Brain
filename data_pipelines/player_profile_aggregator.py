import os
import json
import pandas as pd
import glob
import re
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class PlayerProfileAggregator:
    def __init__(self):
        # Master schema holding everything: Stats, Fielding, Tactics, and Matchups
        self.stats_schema = {
            'Player_Name': '', 
            'Role': 'New Addition', 
            'Country': 'Unknown',
            'Primary_Batting_Phase': 'Middle Order Anchor', 
            
            # Fielding data
            'Total_Drops': 0,
            'Catches_By_Pos': Counter(), 
            'Drops_By_Pos': Counter(),
            
            # AI Tactics
            'Aggregated_Flaws': set(), 
            'Aggregated_Tactics': set(),
            
            # Quantitative metrics
            'Runs': 0, 'Balls_Faced': 0, 'Wickets': 0, 'Balls_Bowled': 0,
            'Runs_Conceded': 0, 'Pressure_Bat_SR': 0.0, 'Pressure_Bowl_Econ': 0.0,
            
            # Venues and Matchups
            '_venue_impact': defaultdict(int),
            'Top_3_Target_Bowlers': [],
            'Top_3_Dangerous_Bowlers': [], 
            'Top_3_Nightmare_Batters': [],
            
            # Internal calculation states
            '_death_runs': 0, '_death_balls_faced': 0,
            '_death_runs_conc': 0, '_death_balls_bowled': 0,
            '_phase_counts': {'Powerplay': 0, 'Middle': 0, 'Death': 0}
        }
        self.profiles = defaultdict(lambda: self.stats_schema.copy())
        self.surname_map = defaultdict(list)

    def _ensure_player(self, name):
        """Forces dictionary initialization for a specific name."""
        if name not in self.profiles:
            self.profiles[name] = self.stats_schema.copy()
            self.profiles[name]['Player_Name'] = name
            # Re-initialize nested objects to avoid reference sharing
            self.profiles[name]['_venue_impact'] = defaultdict(int)
            self.profiles[name]['_phase_counts'] = {'Powerplay': 0, 'Middle': 0, 'Death': 0}
            self.profiles[name]['Aggregated_Flaws'] = set()
            self.profiles[name]['Aggregated_Tactics'] = set()
            self.profiles[name]['Catches_By_Pos'] = Counter()
            self.profiles[name]['Drops_By_Pos'] = Counter()

    def build_name_index(self):
        for name in self.profiles.keys():
            parts = str(name).split()
            if parts: self.surname_map[parts[-1].lower()].append(name)

    def resolve_name(self, raw_name):
        raw_name = str(raw_name).strip()
        if not raw_name: return raw_name
        if raw_name in self.profiles: return raw_name
        parts = raw_name.split()
        if len(parts) > 1:
            first_initial = parts[0][0].lower()
            surname = parts[-1].lower()
            candidates = self.surname_map.get(surname, [])
            if len(candidates) == 1: return candidates[0]
            for cand in candidates:
                if cand.split()[0].lower().startswith(first_initial): return cand
        return raw_name

    def parse_historical_highlights(self, filename="IPL_Match_Highlights_Commentary.csv"):
        csv_path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(csv_path): 
            print(f"⚠️ Warning: {filename} not found. Skipping 2008-2020 fielding data.")
            return
            
        print(f"📖 NLP Scanning historical commentary for Catches & Drops...")
        df = pd.read_csv(csv_path, low_memory=False)
        
        positions = [r'long\s?on', r'long\s?off', r'deep mid\s?wicket', r'mid\s?wicket', r'mid\s?on', r'mid\s?off', r'square leg', r'deep square leg', r'fine leg', r'short fine leg', r'third man', r'short third man', r'point', r'backward point', r'deep point', r'cover', r'extra cover', r'deep cover', r'slip', r'first slip', r'second slip', r'gully', r'sweeper cover']
        pos_regex = r'(' + '|'.join(positions) + r')'

        catch_pattern = re.compile(r'(?:caught|c)\s+(?:by\s+)?([A-Z][A-Za-z\s\.-]+?)\s+(?:at|in|near|on)\s+(?:the\s+)?' + pos_regex, re.IGNORECASE)
        drop_pattern = re.compile(r'(?:dropped|put down|spills)\s+(?:a catch\s+)?(?:by\s+)?([A-Z][A-Za-z\s\.-]+?)\s+(?:at|in|near|on)\s+(?:the\s+)?' + pos_regex, re.IGNORECASE)
        
        if 'Commentary' in df.columns:
            for text in df['Commentary'].dropna():
                catch_match = catch_pattern.search(str(text))
                if catch_match:
                    fielder = self.resolve_name(catch_match.group(1).strip())
                    self._ensure_player(fielder)
                    self.profiles[fielder]['Catches_By_Pos'][catch_match.group(2).strip().lower()] += 1
                
                drop_match = drop_pattern.search(str(text))
                if drop_match:
                    fielder = self.resolve_name(drop_match.group(1).strip())
                    self._ensure_player(fielder)
                    self.profiles[fielder]['Drops_By_Pos'][drop_match.group(2).strip().lower()] += 1
                    self.profiles[fielder]['Total_Drops'] += 1

    def parse_tactical_jsons(self):
        print("🔍 Scanning 2021-2026 JSON Tactical Databases...")
        json_files = glob.glob(os.path.join(BASE_DIR, "*.json"))
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for match in data:
                        for insight in match.get('insights', []):
                            if insight.get('batter'):
                                batter = self.resolve_name(insight.get('batter'))
                                self._ensure_player(batter)
                                self.profiles[batter]['Aggregated_Flaws'].add(insight.get('tactical_flaw', ''))
                                self.profiles[batter]['Aggregated_Tactics'].add(insight.get('optimal_tactic', ''))
                        
                        for error in match.get('fielding_errors', []):
                            if error.get('fielder') and error.get('error_type') == 'Dropped Catch':
                                fielder = self.resolve_name(error.get('fielder'))
                                self._ensure_player(fielder)
                                self.profiles[fielder]['Total_Drops'] += 1
                                pos = error.get('position', '').lower()
                                if pos: self.profiles[fielder]['Drops_By_Pos'][pos] += 1
            except Exception as e: 
                pass

    def process_cricsheet_stats(self, csv_filename="ipl_ball_by_ball.csv"):
        csv_path = os.path.join(BASE_DIR, csv_filename)
        if not os.path.exists(csv_path): return
        print(f"📈 Crunching metrics, Venues, and H2H Matchups from {csv_filename}...")
        df = pd.read_csv(csv_path, low_memory=False)
        
        rename_map = {'batter': 'striker', 'batter_runs': 'runs_off_bat', 'wicket_player_out': 'player_dismissed', 'wicket_kind': 'wicket_type'}
        df.rename(columns=rename_map, inplace=True)
        
        df['runs_conceded'] = df['total_runs'] - df.get('legbyes', 0) - df.get('byes', 0)
        df['bowler_wicket'] = df['player_dismissed'].notna() & (~df['wicket_type'].isin(['run out', 'retired hurt', 'obstructing the field']))
        df['is_death'] = df['over'] >= 15 if 'over' in df.columns else False
        
        if 'over' in df.columns:
            df['phase'] = pd.cut(df['over'], bins=[-1, 5, 14, 20], labels=['Powerplay', 'Middle', 'Death'])
        else:
            df['phase'] = 'Middle'

        for _, row in df.iterrows():
            striker = row['striker']
            bowler = row['bowler']
            venue = str(row.get('venue', 'Unknown Stadium'))
            phase = row['phase']
            
            self._ensure_player(striker)
            self._ensure_player(bowler)
            
            runs_scored = row['runs_off_bat']
            self.profiles[striker]['Runs'] += runs_scored
            self.profiles[striker]['Balls_Faced'] += 1
            self.profiles[striker]['_venue_impact'][venue] += runs_scored 
            self.profiles[striker]['_phase_counts'][phase] += 1
            
            if row['is_death']:
                self.profiles[striker]['_death_runs'] += runs_scored
                self.profiles[striker]['_death_balls_faced'] += 1

            self.profiles[bowler]['Balls_Bowled'] += 1
            self.profiles[bowler]['Runs_Conceded'] += row['runs_conceded']
            
            if row['bowler_wicket']:
                self.profiles[bowler]['Wickets'] += 1
                self.profiles[bowler]['_venue_impact'][venue] += 25 # Wickets = heavy venue impact points
                
            if row['is_death']:
                self.profiles[bowler]['_death_runs_conc'] += row['runs_conceded']
                self.profiles[bowler]['_death_balls_bowled'] += 1

        print("  -> Generating Head-to-Head Clash Matrix...")
        df['batter_out'] = df['player_dismissed'] == df['striker']
        matchups = df.groupby(['striker', 'bowler']).agg(
            runs=('runs_off_bat', 'sum'), balls=('ball_number', 'count'), outs=('batter_out', 'sum')
        ).reset_index()
        
        valid_matchups = matchups[matchups['balls'] >= 12].copy()
        valid_matchups['sr'] = (valid_matchups['runs'] / valid_matchups['balls']) * 100

        for batter in valid_matchups['striker'].unique():
            b_data = valid_matchups[valid_matchups['striker'] == batter]
            targets = b_data.sort_values(by='sr', ascending=False).head(3)
            self.profiles[batter]['Top_3_Target_Bowlers'] = targets['bowler'].tolist()
            
            threats = b_data.sort_values(by=['outs', 'sr'], ascending=[False, True]).head(3)
            self.profiles[batter]['Top_3_Dangerous_Bowlers'] = threats['bowler'].tolist()

        for bowler in valid_matchups['bowler'].unique():
            bw_data = valid_matchups[valid_matchups['bowler'] == bowler]
            nightmares = bw_data.sort_values(by=['sr', 'outs'], ascending=[False, True]).head(3)
            self.profiles[bowler]['Top_3_Nightmare_Batters'] = nightmares['striker'].tolist()

    def generate_clash_tactics_for_batter(self, flaws_set):
        """Generates dynamic pace and spin tactics based on AI flaws (How to BOWL to this batter)."""
        flaws_str = " ".join(flaws_set).lower()
        pace_tactic = ""
        spin_tactic = ""
        
        if 'spin' in flaws_str or 'turn' in flaws_str or 'googly' in flaws_str:
            spin_tactic = "Target primary weakness: Exploit the spinning ball, use variations in flight and turn away from the bat."
            pace_tactic = "Alternate Tactic (Pace): Bowl hard lengths outside off-stump. Use off-cutters rolling fingers over the seam to disrupt timing."
        elif 'pace' in flaws_str or 'bounce' in flaws_str or 'ribs' in flaws_str or 'helmet' in flaws_str:
            pace_tactic = "Target primary weakness: Exploit raw pace. Use well-directed bouncers at the body and yorkers to trap them."
            spin_tactic = "Alternate Tactic (Spin): Toss it up wide of off-stump. Force them to generate their own power by taking the pace off."
        else:
            pace_tactic = "Execute standard death-over strategies: wide yorkers and back-of-a-length slower balls."
            spin_tactic = "Vary pace and trajectory. Aim for the rough patches to induce a false shot."
            
        return pace_tactic, spin_tactic

    def generate_clash_tactics_against_bowler(self, stats):
        """Generates advice for a Batter on how to face this specific Bowler."""
        econ = round(stats['Runs_Conceded'] / (stats['Balls_Bowled'] / 6), 2) if stats['Balls_Bowled'] > 0 else 9.0
        death_econ = round(stats['_death_runs_conc'] / (stats['_death_balls_bowled'] / 6), 2) if stats['_death_balls_bowled'] > 0 else 0.0
        
        tactic = "Play out his deliveries on merit and wait for loose balls. "
        
        if econ <= 6.8:
            tactic = "Elite threat. Treat with immense respect. Focus on rotating the strike and do not take unnecessary aerial risks. "
        elif death_econ > 10.5:
            tactic = "Prime target for the death overs. Attack him aggressively late in the innings as he loses his length under pressure. "
        elif econ >= 9.0:
            tactic = "Target this bowler aggressively. High economy rate suggests frequent boundary deliveries. Look for gaps early. "

        if stats['Top_3_Nightmare_Batters']:
            tactic += f"Historically, {stats['Top_3_Nightmare_Batters'][0]} completely owns this bowler. Emulate that aggressive footprint."
            
        return tactic

    def export_to_csv(self, output_filename="players.csv"):
        print(f"\n💾 Formatting and Exporting Dual-Sided Combat Database to {output_filename}...")
        export_data = []
        
        for player, stats in self.profiles.items():
            if stats['Balls_Faced'] == 0 and stats['Balls_Bowled'] == 0: continue 

            # Role Classification
            role = "Unknown"
            if stats['Balls_Faced'] > 100 and stats['Balls_Bowled'] > 120: role = 'All-Rounder'
            elif stats['Balls_Bowled'] > 120: role = 'Bowler'
            elif stats['Balls_Faced'] > 30: role = 'Batsman'
            else: role = 'New Addition'

            # Primary Phase
            phase_counts = stats['_phase_counts']
            primary_phase = "Middle Order"
            if sum(phase_counts.values()) > 0:
                primary_phase = max(phase_counts, key=phase_counts.get)
                if primary_phase == "Powerplay": primary_phase = "Top Order Aggressor"
                elif primary_phase == "Middle": primary_phase = "Middle Order Anchor"
                elif primary_phase == "Death": primary_phase = "Death Over Finisher"

            # Stadium Ranking (Best to Worst)
            sorted_venues = sorted(stats['_venue_impact'].items(), key=lambda item: item[1], reverse=True)
            best_venues = [v[0] for v in sorted_venues if v[0] != 'Unknown Stadium' and v[1] > 50][:4]
            venue_string = " > ".join(best_venues) if best_venues else "Neutral Venues"

            # Fielding Positions
            best_pos = stats['Catches_By_Pos'].most_common(1)[0][0].title() if stats['Catches_By_Pos'] else "Unknown"
            loose_pos = stats['Drops_By_Pos'].most_common(1)[0][0].title() if stats['Drops_By_Pos'] else "None"

            # Clash Tactics (Dual-Sided)
            pace_tactic, spin_tactic = self.generate_clash_tactics_for_batter(stats['Aggregated_Flaws'])
            batting_against_him = self.generate_clash_tactics_against_bowler(stats)

            # Core Stats
            bat_sr = round((stats['Runs'] / stats['Balls_Faced']) * 100, 1) if stats['Balls_Faced'] > 0 else 0
            death_bat_sr = round((stats['_death_runs'] / stats['_death_balls_faced']) * 100, 1) if stats['_death_balls_faced'] > 0 else 0
            bowl_econ = round(stats['Runs_Conceded'] / (stats['Balls_Bowled'] / 6), 2) if stats['Balls_Bowled'] > 0 else 0
            death_bowl_econ = round(stats['_death_runs_conc'] / (stats['_death_balls_bowled'] / 6), 2) if stats['_death_balls_bowled'] > 0 else 0

            # Isolate Top Rivals for easy UI access
            top_threat_bowler = stats['Top_3_Dangerous_Bowlers'][0] if stats['Top_3_Dangerous_Bowlers'] else "None"
            top_nightmare_batter = stats['Top_3_Nightmare_Batters'][0] if stats['Top_3_Nightmare_Batters'] else "None"

            # Generate the Coach's Tape Summary
            tape = f"{player} is a {primary_phase}. Strongest at {best_venues[0] if best_venues else 'most grounds'}."
            if role in ['Batsman', 'All-Rounder'] and top_threat_bowler != "None":
                tape += f" Beware of {top_threat_bowler} who owns this matchup."
            if role in ['Bowler', 'All-Rounder'] and top_nightmare_batter != "None":
                tape += f" Keep away from {top_nightmare_batter} who hits them at will."

            export_data.append({
                'Player_Name': player,
                'Full_Name': '',     
                'Country': '',       
                'Role': role,
                'Primary_Batting_Phase': primary_phase,
                'Best_to_Worst_Venues': venue_string,
                
                'General_Fielding_Position': best_pos,
                'Loose_Fielding_Position': loose_pos,
                'Total_Dropped_Catches': stats['Total_Drops'],
                
                # Combat / Clash Data
                'Clash_Pace_Tactic': pace_tactic,
                'Clash_Spin_Tactic': spin_tactic,
                'Batting_Against_Him_Tactic': batting_against_him,
                'Coach_Tape_Suggestion': tape,
                
                # H2H Targets
                'Primary_Threat_Bowler': top_threat_bowler,
                'Primary_Nightmare_Batter': top_nightmare_batter,
                
                # Baseline
                'Overall_Bat_SR': bat_sr,
                'Pressure_Bat_SR_Death': death_bat_sr,
                'Overall_Bowl_Econ': bowl_econ,
                'Pressure_Bowl_Econ_Death': death_bowl_econ,
                'Wickets': stats['Wickets'],
                'Balls_Bowled': stats['Balls_Bowled']
            })

        df = pd.DataFrame(export_data)
        df = df.sort_values(by=['Overall_Bat_SR', 'Wickets'], ascending=False)
        output_path = os.path.join(BASE_DIR, output_filename)
        df.to_csv(output_path, index=False)
        print(f"✅ SUCCESS! Created Dual-Sided Profiles in {output_filename}")

if __name__ == "__main__":
    builder = PlayerProfileAggregator()
    # 1. Load Catches/Drops
    builder.parse_historical_highlights("IPL_Match_Highlights_Commentary.csv")
    # 2. Load AI Flaws
    builder.parse_tactical_jsons()
    # 3. Load Stats & Venues
    builder.process_cricsheet_stats("ipl_ball_by_ball.csv")
    # 4. Export
    builder.export_to_csv("players.csv")