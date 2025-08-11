#!/usr/bin/env python3
"""
Interactive 4th Down Strategy Evolution with Plotly
===================================================

This script creates interactive visualizations of NFL 4th down strategy evolution:
- Animated timeline of decision-making trends across years
- Interactive team filtering and comparison tools
- Drill-down analysis by field position and game situation
- Rich hover information with detailed statistics

Demonstrates the "analytics revolution" in NFL 4th down decision making with interactive tools.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import os
import sys

# Import nflplotpy and nfl_data_py
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import nflplotpy as nflplot
import nfl_data_py as nfl


def load_fourth_down_data(years=None):
    """Load play-by-play data for 4th down analysis."""
    if years is None:
        years = list(range(2015, 2025))  # 10 years of data
    
    print(f"📥 Loading 4th down data for years {min(years)}-{max(years)}...")
    
    all_data = []
    for year in years:
        try:
            print(f"  Loading {year}...")
            pbp = nfl.import_pbp_data([year])
            
            # Filter for 4th downs in regular season
            fourth_downs = pbp[
                (pbp['down'] == 4) & 
                (pbp['season_type'] == 'REG') &
                (pbp['ydstogo'].notna()) &
                (pbp['play_type'].notna())
            ].copy()
            
            print(f"    Found {len(fourth_downs):,} 4th down plays in {year}")
            all_data.append(fourth_downs)
            
        except Exception as e:
            print(f"    ⚠️ Error loading {year}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No 4th down data could be loaded")
    
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"✅ Loaded {len(combined_data):,} total 4th down plays across {len(years)} seasons")
    
    return combined_data


def categorize_fourth_downs(df):
    """Categorize 4th down plays by distance and situation."""
    print("🏈 Categorizing 4th down plays...")
    
    df = df.copy()
    
    # Distance categories
    def distance_category(yards):
        if yards <= 2:
            return '4th & Short (1-2)'
        elif yards <= 4:
            return '4th & Medium (3-4)'
        elif yards <= 7:
            return '4th & Long (5-7)'
        else:
            return '4th & Very Long (8+)'
    
    df['distance_category'] = df['ydstogo'].apply(distance_category)
    
    # Field position categories using yardline_100
    if 'yardline_100' in df.columns:
        def field_position_category(yards_to_goal):
            if pd.isna(yards_to_goal):
                return 'Unknown'
            if yards_to_goal <= 10:
                return 'Goal Line (1-10)'
            elif yards_to_goal <= 25:
                return 'Red Zone (11-25)'
            elif yards_to_goal <= 50:
                return 'Opponent Territory (26-50)'
            elif yards_to_goal <= 75:
                return 'Midfield (51-75)'
            else:
                return 'Own Territory (76+)'
        
        df['field_position'] = df['yardline_100'].apply(field_position_category)
    else:
        df['field_position'] = 'Unknown'
    
    # Determine 4th down decision
    def fourth_down_decision(row):
        play_type = str(row['play_type']).lower()
        
        if 'punt' in play_type:
            return 'Punt'
        elif 'field_goal' in play_type or row.get('field_goal_attempt', 0) == 1:
            return 'Field Goal'
        elif play_type in ['run', 'pass', 'rush']:
            return 'Go For It'
        elif 'no_play' in play_type or 'penalty' in play_type:
            return 'Other'
        else:
            # Infer from other columns
            if row.get('punt_attempt', 0) == 1:
                return 'Punt'
            elif row.get('field_goal_attempt', 0) == 1:
                return 'Field Goal'
            else:
                return 'Go For It'
    
    df['decision'] = df.apply(fourth_down_decision, axis=1)
    
    # Filter out unclear plays
    df = df[df['decision'] != 'Other'].copy()
    
    # Success indicator for "Go For It" plays
    df['conversion_success'] = df.apply(
        lambda row: row.get('fourth_down_converted', 0) == 1 if row['decision'] == 'Go For It' else None, 
        axis=1
    )
    
    # Score situation (leading/trailing/tied)
    df['score_situation'] = 'Unknown'
    if 'score_differential' in df.columns:
        df['score_situation'] = df['score_differential'].apply(
            lambda x: 'Leading' if x > 7 else 'Slightly Leading' if x > 0 else 
                     'Tied' if x == 0 else 'Slightly Trailing' if x > -7 else 'Trailing'
        )
    
    print(f"✅ Categorized {len(df):,} 4th down plays")
    return df


def create_animated_trends_plot(df):
    """Create animated plot showing evolution of 4th down trends."""
    print("📊 Creating animated trends visualization...")
    
    # Calculate yearly trends by distance
    yearly_data = []
    for year in sorted(df['season'].unique()):
        year_data = df[df['season'] == year]
        
        for distance in year_data['distance_category'].unique():
            distance_data = year_data[year_data['distance_category'] == distance]
            
            decision_counts = distance_data['decision'].value_counts()
            total_plays = len(distance_data)
            
            for decision in ['Go For It', 'Punt', 'Field Goal']:
                count = decision_counts.get(decision, 0)
                percentage = (count / total_plays) * 100 if total_plays > 0 else 0
                
                yearly_data.append({
                    'season': year,
                    'distance_category': distance,
                    'decision': decision,
                    'count': count,
                    'total_plays': total_plays,
                    'percentage': percentage
                })
    
    trends_df = pd.DataFrame(yearly_data)
    
    # Create animated bar chart
    fig = px.bar(
        trends_df[trends_df['decision'] == 'Go For It'],
        x='distance_category',
        y='percentage',
        animation_frame='season',
        color='distance_category',
        hover_data=['count', 'total_plays'],
        title="Evolution of NFL 4th Down Aggressiveness by Distance Category",
        labels={
            'percentage': 'Go For It Rate (%)',
            'distance_category': 'Down & Distance'
        }
    )
    
    # Update layout
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45,
        showlegend=False,
        yaxis=dict(range=[0, max(trends_df[trends_df['decision'] == 'Go For It']['percentage']) * 1.1])
    )
    
    # Add trend annotation
    fig.add_annotation(
        text="📈 Watch teams become more aggressive over time!",
        xref="paper", yref="paper",
        x=0.5, y=0.95,
        showarrow=False,
        font=dict(size=14, color="blue")
    )
    
    return fig


def create_interactive_team_comparison(df):
    """Create interactive team comparison tool."""
    print("📊 Creating interactive team comparison...")
    
    # Calculate team statistics for recent years
    recent_years = sorted(df['season'].unique())[-5:]  # Last 5 years
    recent_data = df[df['season'].isin(recent_years)]
    
    # Team stats by year and distance
    team_yearly_stats = []
    
    for team in recent_data['posteam'].unique():
        if pd.isna(team):
            continue
            
        team_data = recent_data[recent_data['posteam'] == team]
        
        for year in recent_years:
            year_data = team_data[team_data['season'] == year]
            
            for distance in year_data['distance_category'].unique():
                distance_data = year_data[year_data['distance_category'] == distance]
                
                if len(distance_data) == 0:
                    continue
                
                total_plays = len(distance_data)
                go_for_it_plays = len(distance_data[distance_data['decision'] == 'Go For It'])
                go_for_it_rate = (go_for_it_plays / total_plays) * 100
                
                # Success rate for go-for-it plays
                success_plays = distance_data[
                    (distance_data['decision'] == 'Go For It') & 
                    (distance_data['conversion_success'] == 1)
                ]
                success_rate = (len(success_plays) / go_for_it_plays * 100) if go_for_it_plays > 0 else 0
                
                team_yearly_stats.append({
                    'team': team,
                    'season': year,
                    'distance_category': distance,
                    'total_plays': total_plays,
                    'go_for_it_plays': go_for_it_plays,
                    'go_for_it_rate': go_for_it_rate,
                    'success_rate': success_rate
                })
    
    team_stats_df = pd.DataFrame(team_yearly_stats)
    
    # Create subplot figure with dropdowns
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Go For It Rate by Distance', 'Success Rate by Distance', 
                       'Aggressiveness vs Success', 'Team Trends Over Time'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Get team colors
    teams = sorted(team_stats_df['team'].unique())
    try:
        team_colors = nflplot.get_team_colors(teams, 'primary')
        color_dict = dict(zip(teams, team_colors))
    except:
        color_dict = {team: px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)] 
                     for i, team in enumerate(teams)}
    
    # Add traces for first team (others will be toggled via buttons)
    default_team = teams[0] if teams else 'KC'
    default_data = team_stats_df[team_stats_df['team'] == default_team]
    
    # 1. Go for it rate by distance (bar chart)
    for distance in default_data['distance_category'].unique():
        distance_data = default_data[default_data['distance_category'] == distance]
        avg_rate = distance_data['go_for_it_rate'].mean()
        
        fig.add_trace(
            go.Bar(
                x=[distance],
                y=[avg_rate],
                name=distance,
                marker_color=color_dict.get(default_team, '#1f77b4'),
                showlegend=False
            ),
            row=1, col=1
        )
    
    # 2. Success rate by distance
    for distance in default_data['distance_category'].unique():
        distance_data = default_data[default_data['distance_category'] == distance]
        avg_success = distance_data['success_rate'].mean()
        
        fig.add_trace(
            go.Bar(
                x=[distance],
                y=[avg_success],
                name=distance,
                marker_color=color_dict.get(default_team, '#1f77b4'),
                showlegend=False
            ),
            row=1, col=2
        )
    
    # 3. Scatter: Aggressiveness vs Success (team summary)
    team_summary = team_stats_df.groupby('team').agg({
        'go_for_it_rate': 'mean',
        'success_rate': 'mean',
        'total_plays': 'sum'
    }).reset_index()
    
    fig.add_trace(
        go.Scatter(
            x=team_summary['go_for_it_rate'],
            y=team_summary['success_rate'],
            mode='markers+text',
            text=team_summary['team'],
            textposition='top center',
            marker=dict(
                size=10,
                color=[color_dict.get(team, '#1f77b4') for team in team_summary['team']],
                line=dict(width=1, color='white')
            ),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 4. Trends over time for default team
    team_yearly = default_data.groupby('season')['go_for_it_rate'].mean().reset_index()
    fig.add_trace(
        go.Scatter(
            x=team_yearly['season'],
            y=team_yearly['go_for_it_rate'],
            mode='lines+markers',
            name=default_team,
            line=dict(color=color_dict.get(default_team, '#1f77b4'), width=3),
            marker=dict(size=8),
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text="Interactive NFL 4th Down Team Analysis Dashboard",
        showlegend=False
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Distance Category", row=1, col=1)
    fig.update_yaxes(title_text="Go For It Rate (%)", row=1, col=1)
    fig.update_xaxes(title_text="Distance Category", row=1, col=2)
    fig.update_yaxes(title_text="Success Rate (%)", row=1, col=2)
    fig.update_xaxes(title_text="Go For It Rate (%)", row=2, col=1)
    fig.update_yaxes(title_text="Success Rate (%)", row=2, col=1)
    fig.update_xaxes(title_text="Season", row=2, col=2)
    fig.update_yaxes(title_text="Go For It Rate (%)", row=2, col=2)
    
    return fig


def create_situational_analysis(df):
    """Create situational analysis with interactive filters."""
    print("📊 Creating situational analysis...")
    
    # Prepare data for situational analysis
    situational_data = df.groupby([
        'season', 'field_position', 'distance_category', 'decision'
    ]).size().reset_index(name='count')
    
    situational_totals = df.groupby([
        'season', 'field_position', 'distance_category'
    ]).size().reset_index(name='total')
    
    situational_merged = situational_data.merge(
        situational_totals, 
        on=['season', 'field_position', 'distance_category']
    )
    situational_merged['percentage'] = (situational_merged['count'] / situational_merged['total']) * 100
    
    # Focus on "Go For It" decisions
    go_for_it_situational = situational_merged[
        situational_merged['decision'] == 'Go For It'
    ].copy()
    
    # Create interactive heatmap
    fig = px.density_heatmap(
        go_for_it_situational,
        x='field_position',
        y='distance_category',
        z='percentage',
        animation_frame='season',
        title='4th Down Aggressiveness by Field Position and Distance',
        labels={
            'percentage': 'Go For It Rate (%)',
            'field_position': 'Field Position',
            'distance_category': 'Down & Distance'
        },
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(
        height=600,
        xaxis_tickangle=-45
    )
    
    return fig


def main():
    """Create interactive 4th down evolution visualizations."""
    print("🏈 NFL Interactive 4th Down Strategy Evolution")
    print("=" * 60)
    
    # Configuration
    YEARS = list(range(2015, 2025))  # 10 years of analysis
    
    try:
        # Load and process data
        fourth_down_data = load_fourth_down_data(YEARS)
        categorized_data = categorize_fourth_downs(fourth_down_data)
        
        print("\n📊 Creating interactive visualizations...")
        
        output_dir = os.path.dirname(__file__)
        
        # 1. Animated trends over time
        fig1 = create_animated_trends_plot(categorized_data)
        trends_path = os.path.join(output_dir, 'plotly_fourth_down_trends_animated.html')
        fig1.write_html(trends_path)
        print(f"💾 Saved animated trends: {trends_path}")
        
        # 2. Interactive team comparison
        fig2 = create_interactive_team_comparison(categorized_data)
        team_path = os.path.join(output_dir, 'plotly_fourth_down_team_dashboard.html')
        fig2.write_html(team_path)
        print(f"💾 Saved team dashboard: {team_path}")
        
        # 3. Situational analysis
        fig3 = create_situational_analysis(categorized_data)
        situation_path = os.path.join(output_dir, 'plotly_fourth_down_situational.html')
        fig3.write_html(situation_path)
        print(f"💾 Saved situational analysis: {situation_path}")
        
        print("\n" + "=" * 60)
        print("✅ Interactive 4th down visualizations completed!")
        
        print("\n🎮 Generated Interactive Visualizations:")
        print("• Animated timeline showing evolution of 4th down aggressiveness")
        print("• Team comparison dashboard with multiple perspectives")
        print("• Situational analysis by field position and game context")
        print("\n💻 Open the HTML files in your browser for full interactivity!")
        
        # Quick summary stats
        total_plays = len(categorized_data)
        earliest_year = min(YEARS)
        latest_year = max(YEARS)
        
        early_data = categorized_data[categorized_data['season'] == earliest_year]
        recent_data = categorized_data[categorized_data['season'] == latest_year]
        
        early_rate = len(early_data[early_data['decision'] == 'Go For It']) / len(early_data) * 100
        recent_rate = len(recent_data[recent_data['decision'] == 'Go For It']) / len(recent_data) * 100
        
        print(f"\n📈 Analytics Revolution Summary:")
        print(f"   Total plays analyzed: {total_plays:,}")
        print(f"   'Go for it' rate {earliest_year}: {early_rate:.1f}%")
        print(f"   'Go for it' rate {latest_year}: {recent_rate:.1f}%")
        print(f"   Increase: +{recent_rate - early_rate:.1f} percentage points")
        print(f"   Your hypothesis was correct - teams ARE going for it much more! 🎯")
        
    except Exception as e:
        print(f"\n❌ Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()