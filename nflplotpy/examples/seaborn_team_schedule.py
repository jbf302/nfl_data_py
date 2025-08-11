#!/usr/bin/env python3
"""
Team Schedule Visualization with Seaborn
========================================

This script creates a team's season schedule visualization showing:
- Game results vs betting spreads as horizontal bar chart
- Win/loss coloring based on actual performance vs spread
- Opponent team information and logos
- Interactive team selection

Demonstrates nflplotpy integration with seaborn for publication-quality charts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import sys
import argparse
from datetime import datetime

# Import nflplotpy and nfl_data_py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import nflplotpy as nflplot
import nfl_data_py as nfl


def load_schedule_with_spreads(year=2024):
    """Load NFL schedule data with betting lines."""
    print(f"📥 Loading {year} NFL schedule and betting data...")
    schedule = nfl.import_schedules([year])
    
    # Filter for regular season games with completed scores
    reg_season = schedule[
        (schedule['game_type'] == 'REG') & 
        (schedule['away_score'].notna()) &
        (schedule['home_score'].notna())
    ].copy()
    
    print(f"✅ Loaded {len(reg_season)} completed regular season games")
    return reg_season


def prepare_team_schedule_data(schedule_df, team='KC'):
    """Prepare schedule data for a specific team."""
    print(f"🏈 Preparing schedule data for {team}...")
    
    # Get games where team played (home or away)
    team_games = schedule_df[
        (schedule_df['home_team'] == team) | (schedule_df['away_team'] == team)
    ].copy()
    
    if len(team_games) == 0:
        raise ValueError(f"No games found for team '{team}' in the data")
    
    # Create standardized columns from team's perspective
    team_games['is_home'] = team_games['home_team'] == team
    team_games['team_score'] = np.where(
        team_games['is_home'], 
        team_games['home_score'], 
        team_games['away_score']
    )
    team_games['opponent_score'] = np.where(
        team_games['is_home'], 
        team_games['away_score'], 
        team_games['home_score']
    )
    team_games['opponent'] = np.where(
        team_games['is_home'], 
        team_games['away_team'], 
        team_games['home_team']
    )
    
    # Calculate score differential (positive = team won)
    team_games['score_diff'] = team_games['team_score'] - team_games['opponent_score']
    team_games['win'] = team_games['score_diff'] > 0
    
    # Handle spread from team's perspective 
    # spread_line is for the HOME team: negative = home favored, positive = home underdog
    # We need to calculate what spread our team was getting/giving
    team_games['team_spread'] = np.where(
        team_games['is_home'],
        team_games['spread_line'],   # If home, team gets the spread_line directly
        -team_games['spread_line']   # If away, team gets opposite of spread_line
    )
    
    # Calculate spread performance (did team beat the spread?)
    # Team beats spread if: (team_score - opponent_score) > team_spread
    team_games['spread_diff'] = team_games['score_diff'] - team_games['team_spread'] 
    team_games['beat_spread'] = team_games['spread_diff'] > 0
    
    # Create game labels
    team_games['game_label'] = team_games.apply(
        lambda row: f"W {row['week']: >2} vs {row['opponent']}" if row['is_home'] 
                   else f"W {row['week']: >2} @ {row['opponent']}", axis=1
    )
    team_games['game_label'] = team_games['game_label'].str.replace('W', 'Week')
    
    # Sort by week
    team_games = team_games.sort_values('week')
    
    print(f"✅ Processed {len(team_games)} games for {team}")
    print(f"   Record: {team_games['win'].sum()}-{(~team_games['win']).sum()}")
    print(f"   vs Spread: {team_games['beat_spread'].sum()}-{(~team_games['beat_spread']).sum()}")
    
    return team_games


def create_team_schedule_plot(team_games, team='KC', season=2024):
    """Create seaborn-based team schedule visualization."""
    print(f"📊 Creating schedule visualization for {team}...")
    
    # Set up the plot
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(14, max(10, len(team_games) * 0.6)))
    
    # Define colors
    win_color = '#2E8B57'    # Sea green for wins
    loss_color = '#DC143C'   # Crimson for losses
    spread_color = '#4682B4' # Steel blue for spread bars
    
    # Create base bars for score differential
    y_positions = range(len(team_games))
    score_diffs = team_games['score_diff'].values
    spread_values = team_games['team_spread'].values
    
    # Color bars based on win/loss
    bar_colors = [win_color if win else loss_color for win in team_games['win']]
    
    # Main bars - actual score differential
    bars = ax.barh(y_positions, score_diffs, height=0.6, 
                   color=bar_colors, alpha=0.8, label='Actual Score Differential')
    
    # Spread reference bars - thinner, behind main bars
    spread_bars = ax.barh(y_positions, spread_values, height=0.3, 
                          color=spread_color, alpha=0.6, label='Pre-game Spread')
    
    # Add vertical line at 0
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.3, linewidth=1)
    
    # Customize y-axis with game labels
    ax.set_yticks(y_positions)
    ax.set_yticklabels(team_games['game_label'].tolist())
    ax.invert_yaxis()  # Latest games at top
    
    # Labels and title
    ax.set_xlabel('Points Differential', fontsize=12, fontweight='bold')
    ax.set_title(f'{team} {season} Season Schedule Analysis\n'
                 f'Actual Results vs Pre-Game Spreads', 
                 fontsize=16, fontweight='bold', pad=20)
    
    # Add legend
    ax.legend(loc='lower right', framealpha=0.9)
    
    # Add text annotations for key stats
    wins = team_games['win'].sum()
    losses = len(team_games) - wins
    spread_wins = team_games['beat_spread'].sum()
    spread_losses = len(team_games) - spread_wins
    
    stats_text = f'Record: {wins}-{losses}\nAgainst Spread: {spread_wins}-{spread_losses}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Apply seaborn styling
    sns.despine(left=False, bottom=False)
    
    # Add subtle grid
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Improve layout
    plt.tight_layout()
    
    # Add explanatory footnote
    fig.text(0.5, 0.02, 
             f'Green bars = wins, Red bars = losses • Blue bars = pre-game spread • '
             f'Positive values = outperformed expectations',
             ha='center', fontsize=10, style='italic', alpha=0.7)
    
    return fig


def create_multiple_teams_comparison(schedule_df, teams=['KC', 'BUF', 'BAL', 'CIN'], season=2024):
    """Create a comparison plot of multiple teams' spread performance."""
    print(f"📊 Creating multi-team spread performance comparison...")
    
    # Prepare data for all teams
    all_teams_data = []
    for team in teams:
        try:
            team_data = prepare_team_schedule_data(schedule_df, team)
            team_summary = {
                'team': team,
                'wins': team_data['win'].sum(),
                'losses': len(team_data) - team_data['win'].sum(),
                'spread_wins': team_data['beat_spread'].sum(),
                'spread_losses': len(team_data) - team_data['beat_spread'].sum(),
                'avg_score_diff': team_data['score_diff'].mean(),
                'avg_spread_diff': team_data['spread_diff'].mean()
            }
            all_teams_data.append(team_summary)
        except ValueError as e:
            print(f"⚠️ Skipping {team}: {e}")
    
    if not all_teams_data:
        raise ValueError("No valid teams found in the data")
    
    df = pd.DataFrame(all_teams_data)
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Win-Loss Record
    wins_losses = df[['team', 'wins', 'losses']].melt(id_vars='team', var_name='result', value_name='games')
    sns.barplot(data=wins_losses, x='team', y='games', hue='result', ax=ax1, palette=['green', 'red'])
    ax1.set_title('Win-Loss Records', fontweight='bold')
    ax1.set_ylabel('Games')
    
    # 2. Against Spread Record
    spread_record = df[['team', 'spread_wins', 'spread_losses']].melt(id_vars='team', var_name='result', value_name='games')
    spread_record['result'] = spread_record['result'].map({'spread_wins': 'Beat Spread', 'spread_losses': 'Lost to Spread'})
    sns.barplot(data=spread_record, x='team', y='games', hue='result', ax=ax2, palette=['blue', 'orange'])
    ax2.set_title('Performance vs Spread', fontweight='bold')
    ax2.set_ylabel('Games')
    
    # 3. Average Score Differential
    sns.barplot(data=df, x='team', y='avg_score_diff', hue='team', ax=ax3, palette='viridis', legend=False)
    ax3.set_title('Average Score Differential', fontweight='bold')
    ax3.set_ylabel('Points per Game')
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # 4. Average Spread Performance
    sns.barplot(data=df, x='team', y='avg_spread_diff', hue='team', ax=ax4, palette='plasma', legend=False)
    ax4.set_title('Average Spread Performance', fontweight='bold')
    ax4.set_ylabel('Points vs Spread')
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.suptitle(f'{season} NFL Season - Team Performance Analysis', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    return fig


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create NFL team schedule analysis with seaborn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seaborn_team_schedule.py                    # Analyze KC for 2024
  python seaborn_team_schedule.py --team BUF         # Analyze Buffalo Bills
  python seaborn_team_schedule.py --team SF --year 2023  # 49ers 2023 season
  python seaborn_team_schedule.py --comparison-teams KC,BUF,BAL,CIN  # Custom comparison

Available teams: KC, BUF, BAL, CIN, CLE, PIT, HOU, IND, JAX, TEN, DEN, LV, LAC,
                 DAL, NYG, PHI, WAS, CHI, DET, GB, MIN, ATL, CAR, NO, TB,
                 ARI, LA, SEA, SF, MIA, NE, NYJ
        """
    )
    
    parser.add_argument(
        '--team', '-t',
        default='KC',
        help='Team to analyze (default: KC). Use 3-letter team abbreviation.'
    )
    
    parser.add_argument(
        '--year', '-y',
        type=int,
        default=2024,
        help='Season year to analyze (default: 2024)'
    )
    
    parser.add_argument(
        '--comparison-teams', '-c',
        default='KC,BUF,BAL,CIN',
        help='Comma-separated list of teams for comparison plot (default: KC,BUF,BAL,CIN)'
    )
    
    parser.add_argument(
        '--no-comparison',
        action='store_true',
        help='Skip creating the multi-team comparison plot'
    )
    
    return parser.parse_args()


def main():
    """Create team schedule visualizations."""
    # Parse command line arguments
    args = parse_arguments()
    
    print("🏈 NFL Team Schedule Analysis with Seaborn")
    print("=" * 50)
    
    # Configuration from arguments
    SEASON = args.year
    PRIMARY_TEAM = args.team.upper()
    COMPARISON_TEAMS = [team.strip().upper() for team in args.comparison_teams.split(',')]
    
    try:
        # Load schedule data
        schedule_data = load_schedule_with_spreads(SEASON)
        
        # Check what teams are available
        available_teams = set(schedule_data['home_team'].unique()) | set(schedule_data['away_team'].unique())
        print(f"\n📋 Available teams: {sorted(available_teams)}")
        
        # Create individual team analysis
        print(f"\n🎯 Creating detailed schedule for {PRIMARY_TEAM}...")
        team_schedule = prepare_team_schedule_data(schedule_data, PRIMARY_TEAM)
        
        fig1 = create_team_schedule_plot(team_schedule, PRIMARY_TEAM, SEASON)
        
        # Save individual team plot
        output_dir = os.path.dirname(__file__)
        individual_path = os.path.join(output_dir, f'seaborn_{PRIMARY_TEAM.lower()}_{SEASON}_schedule.png')
        fig1.savefig(individual_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"💾 Saved individual team analysis: {individual_path}")
        plt.close(fig1)
        
        # Create team comparison (unless disabled)
        if not args.no_comparison:
            print(f"\n📊 Creating team comparison analysis...")
            valid_teams = [team for team in COMPARISON_TEAMS if team in available_teams]
            if len(valid_teams) > 1:
                fig2 = create_multiple_teams_comparison(schedule_data, valid_teams, SEASON)
                
                comparison_path = os.path.join(output_dir, f'seaborn_teams_comparison_{SEASON}.png')
                fig2.savefig(comparison_path, dpi=300, bbox_inches='tight', facecolor='white')
                print(f"💾 Saved team comparison: {comparison_path}")
                plt.close(fig2)
            else:
                print(f"⚠️ Not enough valid teams for comparison")
        else:
            print(f"\n📊 Skipping team comparison (--no-comparison flag used)")
        
        print("\n" + "=" * 50)
        print("✅ Seaborn visualizations completed successfully!")
        print("\n🎨 Generated visualizations:")
        print("• Individual team schedule with spread analysis")
        print("• Multi-team performance comparison")
        print("• Publication-quality styling with seaborn")
        
        print(f"\n🏈 Analysis Summary for {PRIMARY_TEAM}:")
        print(f"   Games analyzed: {len(team_schedule)}")
        print(f"   Record: {team_schedule['win'].sum()}-{(~team_schedule['win']).sum()}")
        print(f"   Against spread: {team_schedule['beat_spread'].sum()}-{(~team_schedule['beat_spread']).sum()}")
        print(f"   Avg score diff: {team_schedule['score_diff'].mean():+.1f} points")
        print(f"   Avg spread performance: {team_schedule['spread_diff'].mean():+.1f} points")
        
    except Exception as e:
        print(f"\n❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()