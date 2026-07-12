import os
import json
import pandas as pd
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class PlayerProfileAggregator:
    def __init__(self):
        self.profiles = defaultdict(lambda: {
            'Player_Name': '',
            'Role': 'Unknown',
            'Total_Drops': 0,
            'Aggregated_Flaws': set(),
            'Aggregated_Tactics': set(),
            'Runs': 0,
            'Balls_Faced': 0,
            'Wickets': 0,
            'Balls_Bowled': 0,
            'Runs_Conceded': 0,
            'Pressure_Bat_SR': 0.0,
            'Pressure_Bowl_Econ': 0.0,
            'Favorable_Pitch': 'Unknown',
            'Top_3_Target_Bowlers': [],
            'Top_3_Dangerous_Bowlers': []
        })

    def parse_tactical_jsons(self):
        print("🔍 Scanning 2021-2026 JSON Tactical Databases...")
        json_files = glob.glob(os.path.join(BASE_DIR, "*.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for match in data:
                        for insight in match.get('insights', []):
                            batter = insight.get('batter')
                            if batter:
                                self.profiles[batter]['Player_Name'] = batter
                                self.profiles[batter]['Aggregated_Flaws'].add(insight.get('tactical_flaw', ''))
                                self.profiles[batter]['Aggregated_Tactics'].add(insight.get('optimal_tactic', ''))
                        for error in match.get('fielding_errors', []):
                            if error.get('error_type') == 'Dropped Catch':
                                fielder = error.get('fielder')
                                if fielder:
                                    self.profiles[fielder]['Player_Name'] = fielder
                                    self.profiles[fielder]['Total_Drops'] += 1
            except Exception as e:
                print(f"  -> Skipping {os.path.basename(file_path)}: {e}")

    def process_cricsheet_stats(self, csv_filename="ipl_ball_by_ball.csv"):
        csv_path = os.path.join(BASE_DIR, csv_filename)
        if not os.path.exists(csv_path):
            print(f"⚠️ Warning: {csv_filename} not found.")
            return

        print(f"📈 Crunching metrics from {csv_filename}...")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Standardizing naming
        rename_map = {'batter': 'striker', 'batter_runs': 'runs_off_bat', 'wicket_player_out': 'player_dismissed', 'wicket_kind': 'wicket_type'}
        df.rename(columns=rename_map, inplace=True)
        
        # Wicket Logic
        df['batter_out'] = df['player_dismissed'] == df['striker']
        df['bowler_wicket'] = df['player_dismissed'].notna() & (~df['wicket_type'].isin(['run out', 'retired hurt', 'obstructing the field']))
        df['runs_conceded'] = df['total_runs'] - df.get('legbyes', 0) - df.get('byes', 0)

        bat_stats = df.groupby('striker').agg(runs=('runs_off_bat', 'sum'), balls=('ball_number', 'count')).reset_index()
        bowl_stats = df.groupby('bowler').agg(wickets=('bowler_wicket', 'sum'), runs_conc=('runs_conceded', 'sum'), balls=('ball_number', 'count')).reset_index()

        for _, row in bat_stats.iterrows():
            p = row['striker']
            self.profiles[p]['Player_Name'] = p
            self.profiles[p]['Runs'] = row['runs']
            self.profiles[p]['Balls_Faced'] = row['balls']

        for _, row in bowl_stats.iterrows():
            p = row['bowler']
            self.profiles[p]['Player_Name'] = p
            self.profiles[p]['Wickets'] = row['wickets']
            self.profiles[p]['Balls_Bowled'] = row['balls']
            self.profiles[p]['Runs_Conceded'] = row['runs_conc']

        # Role determination
        for p, data in self.profiles.items():
            if data['Balls_Faced'] > 100 and data['Balls_Bowled'] > 120: data['Role'] = 'All-Rounder'
            elif data['Balls_Bowled'] > 120: data['Role'] = 'Bowler'
            elif data['Balls_Faced'] > 50: data['Role'] = 'Batsman'

        # Death overs
        death_df = df[df['is_death_overs'] == 1]
        death_bat = death_df.groupby('striker').agg(runs=('runs_off_bat', 'sum'), balls=('ball_number', 'count'))
        death_bowl = death_df.groupby('bowler').agg(runs_conc=('runs_conceded', 'sum'), balls=('ball_number', 'count'))

        for p, data in death_bat.iterrows():
            if data['balls'] > 15: self.profiles[p]['Pressure_Bat_SR'] = round((data['runs'] / data['balls']) * 100, 1)

        for p, data in death_bowl.iterrows():
            overs = data['balls'] / 6
            if overs > 3: self.profiles[p]['Pressure_Bowl_Econ'] = round(data['runs_conc'] / overs, 2)

        # Favorable Pitches
        if 'venue' in df.columns:
            venue_runs = df.groupby(['striker', 'venue'])['runs_off_bat'].sum().reset_index()
            best_venues = venue_runs.loc[venue_runs.groupby('striker')['runs_off_bat'].idxmax()]
            for _, row in best_venues.iterrows():
                if row['runs_off_bat'] > 100: self.profiles[row['striker']]['Favorable_Pitch'] = row['venue']

        # Matchups
        matchups = df.groupby(['striker', 'bowler']).agg(runs=('runs_off_bat', 'sum'), balls=('ball_number', 'count'), outs=('batter_out', 'sum')).reset_index()
        valid_matchups = matchups[matchups['balls'] >= 12].copy()
        valid_matchups['sr'] = (valid_matchups['runs'] / valid_matchups['balls']) * 100

        for batter in valid_matchups['striker'].unique():
            b_data = valid_matchups[valid_matchups['striker'] == batter]
            self.profiles[batter]['Top_3_Target_Bowlers'] = b_data.sort_values(by='sr', ascending=False).head(3)['bowler'].tolist()
            self.profiles[batter]['Top_3_Dangerous_Bowlers'] = b_data.sort_values(by=['outs', 'sr'], ascending=[False, True]).head(3)['bowler'].tolist()

    def export_to_csv(self, output_filename="players.csv"):
        print(f"\n💾 Exporting Unified Database to {output_filename}...")
        export_data = []
        for player, stats in self.profiles.items():
            if not stats['Player_Name']: continue 
            
            flaws = " | ".join([f for f in stats['Aggregated_Flaws'] if f])
            tactics = " | ".join([t for t in stats['Aggregated_Tactics'] if t])
            targets = " | ".join(stats['Top_3_Target_Bowlers'])
            threats = " | ".join(stats['Top_3_Dangerous_Bowlers'])
            
            sr = round((stats['Runs'] / stats['Balls_Faced']) * 100, 1) if stats['Balls_Faced'] > 0 else 0
            econ = round(stats['Runs_Conceded'] / (stats['Balls_Bowled'] / 6), 2) if stats['Balls_Bowled'] > 0 else 0

            export_data.append({
                'Player_Name': stats['Player_Name'],
                'Role': stats['Role'],
                'Matches_Scraped_Flaws': flaws if flaws else 'No qualitative data',
                'Recommended_Tactics': tactics if tactics else 'Rely on standard metrics',
                'Total_Dropped_Catches': stats['Total_Drops'],
                'Wickets': stats['Wickets'],
                'Overall_Bat_SR': sr,
                'Pressure_Bat_SR_Death': stats['Pressure_Bat_SR'],
                'Overall_Bowl_Econ': econ,
                'Pressure_Bowl_Econ_Death': stats['Pressure_Bowl_Econ'],
                'Favorable_Pitch': stats['Favorable_Pitch'],
                'H2H_Target_Bowlers': targets,
                'H2H_Dangerous_Bowlers': threats
            })

        df = pd.DataFrame(export_data)
        df = df.sort_values(by=['Overall_Bat_SR', 'Wickets'], ascending=False)
        df.to_csv(os.path.join(BASE_DIR, output_filename), index=False)
        print(f"✅ SUCCESS! Created ultimate {output_filename} with {len(df)} players.")

if __name__ == "__main__":
    builder = PlayerProfileAggregator()
    builder.parse_tactical_jsons()
    builder.process_cricsheet_stats("ipl_ball_by_ball.csv")
    builder.export_to_csv("players.csv")