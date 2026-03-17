#loading data
import pandas as pd

# Adding low_memory=False fixes the DtypeWarning!
df = pd.read_csv('IPL.csv', low_memory=False)

print("Data loaded successfully without memory warnings!")



# 1. SPLIT & APPLY: Group by the batter and calculate their totals
batter_stats = df.groupby('batter').agg(
    Total_Runs=('runs_batter', 'sum'),   # Uses your exact column name!
    Balls_Faced=('runs_batter', 'count') # Counts how many balls they faced
).reset_index()

# 2. FILTER: Remove players who have faced fewer than 100 balls in their career
batter_stats = batter_stats[batter_stats['Balls_Faced'] >= 100]

# 3. CALCULATE: Create the Strike Rate column
batter_stats['Strike_Rate'] = ((batter_stats['Total_Runs'] / batter_stats['Balls_Faced']) * 100).round(2)

# 4. SORT & DISPLAY: Bring the highest strike rates to the top
batter_stats = batter_stats.sort_values(by='Strike_Rate', ascending=False)

print("Top 10 IPL Batters by Strike Rate:")
display(batter_stats.head(10))




# 1. SPLIT & APPLY: Group by the bowler and calculate their totals
# Notice how we use 'runs_bowler' to get the runs they conceded, and 'bowler_wicket' to count wickets!
bowler_stats = df.groupby('bowler').agg(
    Runs_Conceded=('runs_bowler', 'sum'),
    Total_Balls_Bowled=('ball', 'count'),
    Total_Wickets=('bowler_wicket', 'sum')
).reset_index()

# 2. FILTER: Remove part-timers by only looking at players who bowled at least 120 balls (20 overs)
bowler_stats = bowler_stats[bowler_stats['Total_Balls_Bowled'] >= 120]

# 3. CALCULATE: Figure out the exact Economy Rate
bowler_stats['Overs_Bowled'] = bowler_stats['Total_Balls_Bowled'] / 6
bowler_stats['Economy_Rate'] = (bowler_stats['Runs_Conceded'] / bowler_stats['Overs_Bowled']).round(2)

# 4. SORT & DISPLAY: Bring the lowest (best) economy rates to the top
bowler_stats = bowler_stats.sort_values(by='Economy_Rate', ascending=True)

print("Top 10 IPL Bowlers by Economy Rate:")
display(bowler_stats.head(10))