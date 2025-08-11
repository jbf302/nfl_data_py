#!/usr/bin/env python3
"""
Interactive Team Schedule Visualization with Plotly
===================================================

This script creates interactive team schedule visualizations showing:
- Game results vs betting spreads with hover details
- Interactive team selection and filtering
- Animated timeline view of season progression
- Rich hover information with scores, spreads, and game details

Demonstrates nflplotpy integration with plotly for interactive NFL analytics.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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


def prepare_all_teams_data(schedule_df):
    """Prepare schedule data for all teams."""
    print("🏈 Preparing schedule data for all teams...")
    
    all_teams = sorted(set(schedule_df['home_team'].unique()) | set(schedule_df['away_team'].unique()))
    all_team_data = []
    
    for team in all_teams:
        # Get games where team played (home or away)
        team_games = schedule_df[
            (schedule_df['home_team'] == team) | (schedule_df['away_team'] == team)
        ].copy()
        
        if len(team_games) == 0:
            continue
        
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
        team_games['team_spread'] = np.where(
            team_games['is_home'],
            team_games['spread_line'],   # If home, team gets the spread_line directly
            -team_games['spread_line']   # If away, team gets opposite of spread_line
        )
        
        # Calculate spread performance
        team_games['spread_diff'] = team_games['score_diff'] - team_games['team_spread']
        team_games['beat_spread'] = team_games['spread_diff'] > 0
        
        # Create game information
        team_games['location'] = np.where(team_games['is_home'], 'vs', '@')
        team_games['game_info'] = team_games['location'] + ' ' + team_games['opponent']
        team_games['result_text'] = np.where(team_games['win'], 'W', 'L')
        
        # Add team identifier
        team_games['team'] = team
        
        # Sort by week
        team_games = team_games.sort_values('week')
        
        all_team_data.append(team_games)
    
    # Combine all teams
    combined_data = pd.concat(all_team_data, ignore_index=True)
    print(f"✅ Processed data for {len(all_teams)} teams")
    
    return combined_data


def create_interactive_team_schedule(all_teams_data, default_team='KC'):
    """Create interactive plotly visualization for team schedule."""
    print(f"📊 Creating interactive schedule visualization...")
    
    # Get team colors
    teams = sorted(all_teams_data['team'].unique())
    team_colors = {}
    for team in teams:
        try:
            colors = nflplot.get_team_colors([team], 'primary')
            if colors and len(colors) > 0 and colors[0] and len(colors[0]) > 1:
                team_colors[team] = colors[0]
            else:
                team_colors[team] = '#1f77b4'
        except Exception as e:
            print(f"⚠️ Could not get color for {team}: {e}")
            team_colors[team] = '#1f77b4'
    
    # Create the figure
    fig = go.Figure()
    
    # Add traces for each team (initially hidden except default)
    for team in teams:
        team_data = all_teams_data[all_teams_data['team'] == team].copy()
        if len(team_data) == 0:
            continue
            
        # Create hover text with rich information
        hover_text = []
        for _, row in team_data.iterrows():
            # Interpret team_spread correctly: negative = favored, positive = underdog
            if row['team_spread'] < 0:
                spread_text = f"Favored by {abs(row['team_spread']):.1f}"
            elif row['team_spread'] > 0:
                spread_text = f"Underdog by {row['team_spread']:.1f}"
            else:
                spread_text = "Pick'em"
            
            spread_result = "✅ Beat spread" if row['beat_spread'] else "❌ Lost to spread"
            
            hover_info = (
                f"<b>Week {row['week']}: {row['result_text']} {row['game_info']}</b><br>"
                f"Final Score: {row['team_score']:.0f} - {row['opponent_score']:.0f}<br>"
                f"Score Differential: {row['score_diff']:+.0f}<br>"
                f"<br>"
                f"Pre-game: {spread_text}<br>"
                f"Spread Performance: {row['spread_diff']:+.1f}<br>"
                f"{spread_result}<br>"
                f"<br>"
                f"Date: {row['gameday']}<br>"
                f"Location: {'Home' if row['is_home'] else 'Away'}"
            )
            hover_text.append(hover_info)
        
        # Score differential bars
        fig.add_trace(go.Bar(
            name=f'{team} Score Diff',
            x=team_data['week'],
            y=team_data['score_diff'],
            text=[f"{diff:+.0f}" for diff in team_data['score_diff']],
            textposition='outside',
            marker_color=team_colors[team],
            opacity=0.8,
            visible=True if team == default_team else False,
            legendgroup=team,
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_text,
            showlegend=False
        ))
        
        # Add spread reference line
        fig.add_trace(go.Scatter(
            name=f'{team} Spread',
            x=team_data['week'],
            y=team_data['team_spread'],
            mode='markers+lines',
            line=dict(color='gray', width=2, dash='dash'),
            marker=dict(size=6, color='gray'),
            visible=True if team == default_team else False,
            legendgroup=team,
            hovertemplate='Week %{x}: Pre-game spread %{y:+.1f}<extra></extra>',
            showlegend=False
        ))
    
    # Add horizontal line at 0
    fig.add_hline(y=0, line_dash="solid", line_color="black", opacity=0.3)
    
    # Create dropdown menu for team selection
    dropdown_buttons = []
    for i, team in enumerate(teams):
        visibility = [False] * (len(teams) * 2)  # 2 traces per team
        visibility[i * 2] = True      # Score diff bars
        visibility[i * 2 + 1] = True  # Spread line
        
        dropdown_buttons.append(
            dict(
                label=team,
                method="update",
                args=[{"visible": visibility},
                      {"title": f"{team} 2024 Season Schedule Analysis<br><sub>Score Differential vs Pre-Game Spread</sub>"}]
            )
        )
    
    # Layout
    fig.update_layout(
        title=f"{default_team} 2024 Season Schedule Analysis<br><sub>Score Differential vs Pre-Game Spread</sub>",
        xaxis_title="Week",
        yaxis_title="Points",
        hovermode='closest',
        height=600,
        showlegend=False,
        
        # Add dropdown
        updatemenus=[
            dict(
                buttons=dropdown_buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.02,
                xanchor="left",
                y=1.05,
                yanchor="top",
            ),
        ],
        
        # Annotations
        annotations=[
            dict(text="Select Team:", x=0.01, xref="paper", y=1.08, yref="paper", 
                 align="left", showarrow=False, font=dict(size=14, color="black"))
        ]
    )
    
    # Update axes
    fig.update_xaxes(
        tickmode='linear',
        tick0=1,
        dtick=1,
        range=[0.5, 18.5],
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=0.5
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=0.5,
        zeroline=True,
        zerolinecolor='black',
        zerolinewidth=2
    )
    
    return fig


def create_spread_performance_heatmap(all_teams_data):
    """Create heatmap showing spread performance by team and week."""
    print("📊 Creating spread performance heatmap...")
    
    # Create pivot table
    pivot_data = all_teams_data.pivot_table(
        values='spread_diff',
        index='team',
        columns='week',
        aggfunc='first'
    )
    
    # Create custom colorscale (red = lost to spread, green = beat spread)
    colorscale = [
        [0.0, '#d62728'],    # Red for negative (lost to spread)
        [0.5, '#ffffff'],    # White for neutral
        [1.0, '#2ca02c']     # Green for positive (beat spread)
    ]
    
    # Create hover text
    hover_text = []
    for team in pivot_data.index:
        team_hover_row = []
        for week in pivot_data.columns:
            value = pivot_data.loc[team, week]
            if pd.isna(value):
                team_hover_row.append(f"Week {week}: No game")
            else:
                result = "Beat spread" if value > 0 else "Lost to spread" if value < 0 else "Push"
                team_hover_row.append(f"Week {week}: {result}<br>Margin: {value:+.1f} pts")
        hover_text.append(team_hover_row)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=[f"Week {w}" for w in pivot_data.columns],
        y=pivot_data.index,
        colorscale=colorscale,
        zmid=0,
        hovertemplate='%{text}<extra></extra>',
        text=hover_text,
        colorbar=dict(
            title="Spread Performance",
            titleside="right",
            tickmode="linear",
            tick0=-20,
            dtick=10,
            ticksuffix=" pts"
        )
    ))
    
    fig.update_layout(
        title="2024 NFL Spread Performance by Team and Week<br><sub>Green = Beat Spread, Red = Lost to Spread</sub>",
        xaxis_title="Week",
        yaxis_title="Team",
        height=800,
        font=dict(size=12)
    )
    
    return fig


def create_season_progression_animation(all_teams_data):
    """Create animated view of season progression."""
    print("📊 Creating animated season progression...")
    
    # Calculate cumulative stats by week
    animation_data = []
    teams = sorted(all_teams_data['team'].unique())
    
    for team in teams:
        team_data = all_teams_data[all_teams_data['team'] == team].sort_values('week')
        
        cumulative_wins = 0
        cumulative_spread_wins = 0
        
        for i, (_, row) in enumerate(team_data.iterrows()):
            if row['win']:
                cumulative_wins += 1
            if row['beat_spread']:
                cumulative_spread_wins += 1
                
            animation_data.append({
                'team': team,
                'week': row['week'],
                'cumulative_wins': cumulative_wins,
                'cumulative_losses': i + 1 - cumulative_wins,
                'cumulative_spread_wins': cumulative_spread_wins,
                'cumulative_spread_losses': i + 1 - cumulative_spread_wins,
                'win_pct': cumulative_wins / (i + 1),
                'spread_pct': cumulative_spread_wins / (i + 1)
            })
    
    anim_df = pd.DataFrame(animation_data)
    
    # Create animated scatter plot
    fig = px.scatter(
        anim_df,
        x='win_pct',
        y='spread_pct',
        animation_frame='week',
        animation_group='team',
        color='team',
        size_max=15,
        hover_name='team',
        hover_data={
            'cumulative_wins': True,
            'cumulative_losses': True,
            'cumulative_spread_wins': True,
            'cumulative_spread_losses': True,
            'win_pct': ':.1%',
            'spread_pct': ':.1%'
        },
        title="NFL Season Progression: Win Rate vs Spread Performance",
        labels={
            'win_pct': 'Win Percentage',
            'spread_pct': 'Spread Win Percentage',
            'team': 'Team'
        }
    )
    
    # Add quadrant lines
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=0.5, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Update layout
    fig.update_layout(
        xaxis=dict(range=[0, 1], tickformat='.0%'),
        yaxis=dict(range=[0, 1], tickformat='.0%'),
        height=600,
        showlegend=False
    )
    
    # Add quadrant labels
    fig.add_annotation(x=0.25, y=0.75, text="Good vs Spread<br>Bad Record", showarrow=False, font_size=12)
    fig.add_annotation(x=0.75, y=0.75, text="Good Record<br>Good vs Spread", showarrow=False, font_size=12)
    fig.add_annotation(x=0.25, y=0.25, text="Bad Record<br>Bad vs Spread", showarrow=False, font_size=12)
    fig.add_annotation(x=0.75, y=0.25, text="Good Record<br>Bad vs Spread", showarrow=False, font_size=12)
    
    return fig


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create interactive NFL team schedule analysis with plotly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plotly_team_schedule.py                     # Interactive dashboard for 2024
  python plotly_team_schedule.py --year 2023         # 2023 season data
  python plotly_team_schedule.py --default-team BUF  # Start with Buffalo Bills selected
  python plotly_team_schedule.py --skip-animation    # Skip creating the animation (faster)

Available teams: KC, BUF, BAL, CIN, CLE, PIT, HOU, IND, JAX, TEN, DEN, LV, LAC,
                 DAL, NYG, PHI, WAS, CHI, DET, GB, MIN, ATL, CAR, NO, TB,
                 ARI, LA, SEA, SF, MIA, NE, NYJ
        """
    )
    
    parser.add_argument(
        '--year', '-y',
        type=int,
        default=2024,
        help='Season year to analyze (default: 2024)'
    )
    
    parser.add_argument(
        '--default-team', '-t',
        default='KC',
        help='Default team shown when dashboard loads (default: KC)'
    )
    
    parser.add_argument(
        '--skip-heatmap',
        action='store_true',
        help='Skip creating the spread performance heatmap'
    )
    
    parser.add_argument(
        '--skip-animation',
        action='store_true',
        help='Skip creating the season progression animation (faster execution)'
    )
    
    return parser.parse_args()


def main():
    """Create interactive plotly visualizations."""
    # Parse command line arguments
    args = parse_arguments()
    
    print("🏈 NFL Interactive Schedule Analysis with Plotly")
    print("=" * 50)
    
    # Configuration from arguments
    SEASON = args.year
    DEFAULT_TEAM = args.default_team.upper()
    
    try:
        # Load schedule data
        schedule_data = load_schedule_with_spreads(SEASON)
        
        # Prepare all teams data
        all_teams_data = prepare_all_teams_data(schedule_data)
        
        # Create visualizations
        print("\n📊 Creating interactive visualizations...")
        
        # 1. Interactive team schedule
        fig1 = create_interactive_team_schedule(all_teams_data, DEFAULT_TEAM)
        output_dir = os.path.dirname(__file__)
        schedule_path = os.path.join(output_dir, f'plotly_team_schedule_{SEASON}.html')
        fig1.write_html(schedule_path)
        print(f"💾 Saved interactive team schedule: {schedule_path}")
        
        # 2. Spread performance heatmap (optional)
        if not args.skip_heatmap:
            fig2 = create_spread_performance_heatmap(all_teams_data)
            heatmap_path = os.path.join(output_dir, f'plotly_spread_heatmap_{SEASON}.html')
            fig2.write_html(heatmap_path)
            print(f"💾 Saved spread heatmap: {heatmap_path}")
        else:
            print("📊 Skipping spread heatmap (--skip-heatmap flag used)")
        
        # 3. Season progression animation (optional)
        if not args.skip_animation:
            fig3 = create_season_progression_animation(all_teams_data)
            animation_path = os.path.join(output_dir, f'plotly_season_animation_{SEASON}.html')
            fig3.write_html(animation_path)
            print(f"💾 Saved season animation: {animation_path}")
        else:
            print("📊 Skipping season animation (--skip-animation flag used)")
        
        print("\n" + "=" * 50)
        print("✅ Plotly visualizations completed successfully!")
        print("\n🎨 Generated interactive visualizations:")
        print("• Team schedule selector with detailed hover information")
        print("• Spread performance heatmap by team and week")
        print("• Animated season progression showing win vs spread trends")
        print("\n💻 Open the HTML files in your browser to interact with them!")
        
        # Summary stats
        total_teams = len(all_teams_data['team'].unique())
        total_games = len(all_teams_data)
        print(f"\n📊 Data Summary:")
        print(f"   Teams: {total_teams}")
        print(f"   Total games analyzed: {total_games}")
        print(f"   Season: {SEASON}")
        
    except Exception as e:
        print(f"\n❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()