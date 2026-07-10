import pandas as pd
import numpy as np

import sys
import os
# This tells Python: "Look in the parent folder (IPL_Brain) to find 'data_pipeline'"
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_pipelines.cricsheet import CricsheetProcessor
# Adjust the import path based on your exact folder structure
# (e.g., from data_pipelines.cricsheet_processor import CricsheetProcessor)
#from data_pipelines.cricsheet import cricsheet

class TacticalSimulatorEngine:
    """
    The core recommendation engine for the Django Coach Simulator.
    Takes a User's locked 25-man squad and an Opponent's 15-man squad,
    analyzes them against the historical Cricsheet dataset, and generates tactics.
    """

    def __init__(self, user_squad_25, opponent_squad_15, pitch_condition='Neutral'):
        self.my_squad = user_squad_25
        self.opp_squad = opponent_squad_15
        self.pitch_condition = pitch_condition
        
        # Load the real data using our rock-solid processor!
        processor = CricsheetProcessor("ipl_ball_by_ball.csv")
        self.df = processor.load_and_clean_data()
        
        # Flatten the 25-man squad for easy querying
        self.all_my_players = self.my_squad.get('BAT', []) + self.my_squad.get('BOWL', []) + self.my_squad.get('AR', [])

    # ==========================================
    # 1. CORE ALGORITHMS: 25 -> 15 -> 11
    # ==========================================

    def suggest_top_15(self):
        """
        Filters the locked 25-man squad down to the 15 most optimal players 
        based on general historical performance.
        """
        top_15 = {'BAT': [], 'BOWL': [], 'AR': []}
        player_scores = []

        for player in self.all_my_players:
            # 1. Calculate base performance from the CSV
            player_data = self.df[(self.df['striker'] == player) | (self.df['bowler'] == player)]
            
            # Simple heuristic score (Runs scored + Wickets taken * 25)
            runs = player_data[player_data['striker'] == player]['runs_off_bat'].sum()
            wickets = player_data[(player_data['bowler'] == player) & (player_data['player_dismissed'].notna())].shape[0]
            base_score = runs + (wickets * 25)

            player_scores.append({'name': player, 'score': base_score})

        # Sort all 25 players by their calculated heuristic score
        sorted_players = sorted(player_scores, key=lambda x: x['score'], reverse=True)

        # Ensure balanced categorization for the 15-man squad (e.g., 6 Batsmen, 5 Bowlers, 4 ARs)
        for p in sorted_players:
            name = p['name']
            if name in self.my_squad.get('BAT', []) and len(top_15['BAT']) < 6:
                top_15['BAT'].append(name)
            elif name in self.my_squad.get('BOWL', []) and len(top_15['BOWL']) < 5:
                top_15['BOWL'].append(name)
            elif name in self.my_squad.get('AR', []) and len(top_15['AR']) < 4:
                top_15['AR'].append(name)

        return top_15

    def suggest_playing_11(self, top_15_squad):
        """
        Filters the top 15 down to the MUST-PLAY 11 by analyzing head-to-head 
        matchups specifically against the locked 15-man Opponent squad.
        """
        matchup_scores = []
        candidates = top_15_squad['BAT'] + top_15_squad['BOWL'] + top_15_squad['AR']

        for player in candidates:
            # Calculate how well this player performs specifically against the opponent's roster
            h2h_data = self.df[
                ((self.df['striker'] == player) & (self.df['bowler'].isin(self.opp_squad))) |
                ((self.df['bowler'] == player) & (self.df['striker'].isin(self.opp_squad)))
            ]
            
            # If they have a great history against these specific opponents, boost them
            h2h_runs = h2h_data[h2h_data['striker'] == player]['runs_off_bat'].sum()
            h2h_wickets = h2h_data[(h2h_data['bowler'] == player) & (h2h_data['player_dismissed'].notna())].shape[0]
            
            matchup_scores.append({
                'name': player, 
                'h2h_impact': h2h_runs + (h2h_wickets * 30) 
            })

        # Sort by best head-to-head impact and pick the top 11
        best_11 = sorted(matchup_scores, key=lambda x: x['h2h_impact'], reverse=True)[:11]
        return [p['name'] for p in best_11]

    # ==========================================
    # 2. TACTICAL MATCHUP ADVICE
    # ==========================================

    def tactic_how_to_get_wicket(self, target_opp_batter):
        """
        Analyzes the CSV to find which bowler from your squad 
        has the highest probability of dismissing a specific opponent batter.
        """
        my_bowlers = self.my_squad.get('BOWL', []) + self.my_squad.get('AR', [])
        best_bowler = None
        lowest_balls_per_dismissal = float('inf')

        for bowler in my_bowlers:
            # Filter CSV for this exact Batter vs Bowler matchup
            matchup = self.df[(self.df['striker'] == target_opp_batter) & (self.df['bowler'] == bowler)]
            
            balls_bowled = matchup.shape[0]
            dismissals = matchup[matchup['player_dismissed'].notna()].shape[0]

            if dismissals > 0:
                bpd = balls_bowled / dismissals
                if bpd < lowest_balls_per_dismissal:
                    lowest_balls_per_dismissal = bpd
                    best_bowler = bowler

        if best_bowler:
            return f"Bring on {best_bowler}. Historically, they take {target_opp_batter}'s wicket every {round(lowest_balls_per_dismissal, 1)} balls."
        return f"Insufficient direct historical data. Recommend using your primary strike bowler against {target_opp_batter}."

    def tactic_best_batter_against(self, target_opp_bowler):
        """
        Finds which batter in your squad has the highest strike rate
        against a specific dangerous opponent bowler.
        """
        my_batters = self.my_squad.get('BAT', []) + self.my_squad.get('AR', [])
        best_batter = None
        highest_strike_rate = 0

        for batter in my_batters:
            matchup = self.df[(self.df['striker'] == batter) & (self.df['bowler'] == target_opp_bowler)]
            balls_faced = matchup.shape[0]
            
            if balls_faced >= 10: # Minimum sample size threshold
                runs = matchup['runs_off_bat'].sum()
                strike_rate = (runs / balls_faced) * 100
                
                if strike_rate > highest_strike_rate:
                    highest_strike_rate = strike_rate
                    best_batter = batter

        if best_batter:
            return f"Deploy {best_batter}. They have a dominant Strike Rate of {round(highest_strike_rate, 1)} against {target_opp_bowler}."
        return f"No batsman in your squad has faced 10+ balls against {target_opp_bowler}. Play defensively to see out their over."

if __name__ == "__main__":
    # We will test this with real players who exist in your database!
    my_locked_25 = {
        'BAT': ['V Kohli', 'RG Sharma', 'SA Yadav', 'SS Iyer', 'RR Pant'],
        'BOWL': ['JJ Bumrah', 'Mohammed Shami', 'Kuldeep Yadav', 'YS Chahal', 'Mohammed Siraj'],
        'AR': ['HH Pandya', 'RA Jadeja', 'AR Patel', 'Washington Sundar']
    }
    
    opponent_locked_15 = [
        'MS Dhoni', 'AD Russell', 'GJ Maxwell', 'SP Narine', 'RK Singh'
    ]

    print("\n[System] Booting up Tactical Engine and scanning 288,000+ historical deliveries...")
    engine = TacticalSimulatorEngine(my_locked_25, opponent_locked_15)

    print("\n=== SQUAD SELECTION ===")
    top_15 = engine.suggest_top_15()
    print(f"Top 15 Shortlist: {top_15}")
    
    playing_11 = engine.suggest_playing_11(top_15)
    print(f"\nMust-Play 11 (Based on Opponent Matchups): {playing_11}")

    print("\n=== TACTICAL ADVICE ===")
    # Let's ask the engine real historical questions!
    print("Coach: How do we get MS Dhoni out?")
    print("AI: " + engine.tactic_how_to_get_wicket('MS Dhoni'))
    
    print("\nCoach: Andre Russell is bowling, who should face him?")
    print("AI: " + engine.tactic_best_batter_against('AD Russell'))