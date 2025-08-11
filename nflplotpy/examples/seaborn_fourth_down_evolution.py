#!/usr/bin/env python3
"""
4th Down Strategy Evolution Analysis with Seaborn
=================================================

This script analyzes the evolution of NFL 4th down strategy over time, showing:
- Year-over-year trends in "going for it" vs punting/kicking
- Breakdown by distance categories (4th & short, medium, long)
- Team-by-team analysis of aggressive 4th down strategies
- Success rates and strategy effectiveness

Demonstrates how NFL teams have become more aggressive on 4th down in recent years.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import sys
from collections import defaultdict

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
    
    # Field position categories
    def field_position_category(yardline):
        if pd.isna(yardline):
            return 'Unknown'
        if yardline <= 35:
            return 'Own Territory'
        elif yardline <= 50:
            return 'Midfield'
        elif yardline <= 35:  # opponent 35
            return 'Opponent Territory'
        else:
            return 'Red Zone'
    
    # Note: nfl_data_py uses yardline_100 (distance to goal)
    if 'yardline_100' in df.columns:
        df['field_position'] = df['yardline_100'].apply(
            lambda x: 'Red Zone' if x <= 20 else 
                     'Opponent Territory' if x <= 50 else
                     'Midfield' if x <= 65 else 
                     'Own Territory'
        )
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
            return 'Other'  # Will filter these out
        else:
            # Attempt to infer from other columns
            if row.get('punt_attempt', 0) == 1:
                return 'Punt'
            elif row.get('field_goal_attempt', 0) == 1:
                return 'Field Goal'
            else:
                return 'Go For It'  # Assume offensive play
    
    df['decision'] = df.apply(fourth_down_decision, axis=1)
    
    # Filter out unclear plays
    df = df[df['decision'] != 'Other'].copy()
    
    # Success indicator for "Go For It" plays
    df['conversion_success'] = df.apply(
        lambda row: row.get('fourth_down_converted', 0) == 1 if row['decision'] == 'Go For It' else None, 
        axis=1
    )
    
    print(f"✅ Categorized {len(df):,} 4th down plays")
    print(f"   Decisions: {df['decision'].value_counts().to_dict()}")
    print(f"   Distance categories: {df['distance_category'].value_counts().to_dict()}")
    
    return df


def analyze_fourth_down_trends(df):
    """Analyze trends in 4th down decision making over time."""
    print("📊 Analyzing 4th down trends...")
    
    # Calculate yearly trends by distance category
    yearly_trends = df.groupby(['season', 'distance_category', 'decision']).size().reset_index(name='count')
    yearly_totals = df.groupby(['season', 'distance_category']).size().reset_index(name='total')
    
    # Merge to get percentages
    trends = yearly_trends.merge(yearly_totals, on=['season', 'distance_category'])
    trends['percentage'] = (trends['count'] / trends['total']) * 100
    
    # Focus on "Go For It" decisions
    go_for_it_trends = trends[trends['decision'] == 'Go For It'].copy()
    
    # Calculate success rates for "Go For It" plays
    success_data = df[df['decision'] == 'Go For It'].groupby(['season', 'distance_category']).agg({
        'conversion_success': ['count', 'sum']
    }).reset_index()
    
    success_data.columns = ['season', 'distance_category', 'attempts', 'conversions']
    success_data['success_rate'] = (success_data['conversions'] / success_data['attempts']) * 100
    
    print("✅ Trends analysis complete")
    return go_for_it_trends, success_data


def create_fourth_down_trends_plot(go_for_it_trends, success_data):
    """Create comprehensive 4th down trends visualization."""
    print("📊 Creating 4th down trends visualization...")
    
    # Set up the plot style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Trend in "Go For It" rates over time
    go_for_it_pivot = go_for_it_trends.pivot(index='season', columns='distance_category', values='percentage')
    
    for distance in go_for_it_pivot.columns:
        ax1.plot(go_for_it_pivot.index, go_for_it_pivot[distance], 
                marker='o', linewidth=2.5, markersize=6, label=distance)
    
    ax1.set_title('4th Down "Go For It" Rates by Distance\nYear-over-Year Evolution', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Season', fontweight='bold')
    ax1.set_ylabel('Go For It Rate (%)', fontweight='bold')
    ax1.legend(title='Distance Category', framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    
    # 2. Success rates over time
    success_pivot = success_data.pivot(index='season', columns='distance_category', values='success_rate')
    
    for distance in success_pivot.columns:
        ax2.plot(success_pivot.index, success_pivot[distance], 
                marker='s', linewidth=2.5, markersize=6, label=distance, linestyle='--')
    
    ax2.set_title('4th Down Conversion Success Rates\nWhen Going For It', 
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Season', fontweight='bold')
    ax2.set_ylabel('Conversion Rate (%)', fontweight='bold')
    ax2.legend(title='Distance Category', framealpha=0.9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Heatmap of go-for-it rates
    heatmap_data = go_for_it_trends.pivot(index='distance_category', columns='season', values='percentage')
    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax3, cbar_kws={'label': 'Go For It Rate (%)'})
    ax3.set_title('4th Down Aggressiveness Heatmap', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Season', fontweight='bold')
    ax3.set_ylabel('Distance Category', fontweight='bold')
    
    # 4. Overall trend across all distances
    overall_trend = go_for_it_trends.groupby('season').agg({
        'count': 'sum'
    }).reset_index()
    
    overall_total = go_for_it_trends.groupby('season')['total'].sum().reset_index()
    overall_trend = overall_trend.merge(overall_total, on='season')
    overall_trend['overall_percentage'] = (overall_trend['count'] / overall_trend['total']) * 100
    
    # Add trend line
    z = np.polyfit(overall_trend['season'], overall_trend['overall_percentage'], 1)
    p = np.poly1d(z)
    
    ax4.scatter(overall_trend['season'], overall_trend['overall_percentage'], 
               s=100, alpha=0.7, color='navy', label='Actual')
    ax4.plot(overall_trend['season'], p(overall_trend['season']), 
             color='red', linewidth=3, linestyle='-', label=f'Trend (slope: +{z[0]:.2f}%/year)')
    
    ax4.set_title('Overall 4th Down Aggressiveness Trend\nAll Situations Combined', 
                  fontsize=14, fontweight='bold')
    ax4.set_xlabel('Season', fontweight='bold')
    ax4.set_ylabel('Go For It Rate (%)', fontweight='bold')
    ax4.legend(framealpha=0.9)
    ax4.grid(True, alpha=0.3)
    
    # Add annotation with trend info
    trend_text = f"League average increase:\n+{z[0]:.2f}% per year"
    ax4.text(0.05, 0.95, trend_text, transform=ax4.transAxes, 
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
             verticalalignment='top', fontsize=10, fontweight='bold')
    
    plt.suptitle('NFL 4th Down Strategy Evolution (2015-2024)\n'
                 'The Analytics Revolution in Football Decision Making', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    return fig


def create_team_aggressiveness_plot(df, recent_years=3):
    """Create plot showing team-by-team 4th down aggressiveness."""
    print(f"📊 Creating team aggressiveness analysis (last {recent_years} years)...")
    
    # Filter for recent years
    current_year = df['season'].max()
    recent_data = df[df['season'] >= (current_year - recent_years + 1)].copy()
    
    # Calculate team statistics
    team_stats = recent_data.groupby(['posteam', 'decision']).size().reset_index(name='count')
    team_totals = recent_data.groupby('posteam').size().reset_index(name='total')
    
    team_analysis = team_stats.merge(team_totals, left_on='posteam', right_on='posteam')
    team_analysis['percentage'] = (team_analysis['count'] / team_analysis['total']) * 100
    
    # Focus on "Go For It" decisions
    go_for_it_by_team = team_analysis[team_analysis['decision'] == 'Go For It'].copy()
    
    # Calculate success rates
    success_by_team = recent_data[recent_data['decision'] == 'Go For It'].groupby('posteam').agg({
        'conversion_success': ['count', 'sum']
    }).reset_index()
    success_by_team.columns = ['posteam', 'attempts', 'conversions']
    success_by_team['success_rate'] = (success_by_team['conversions'] / success_by_team['attempts']) * 100
    
    # Merge data
    team_combined = go_for_it_by_team.merge(success_by_team, on='posteam', how='left')
    team_combined = team_combined.dropna()
    
    # Get team colors
    teams = team_combined['posteam'].tolist()
    try:
        team_colors = nflplot.get_team_colors(teams, 'primary')
        color_dict = dict(zip(teams, team_colors))
    except:
        color_dict = {team: '#1f77b4' for team in teams}
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    
    # 1. Go-for-it rate by team
    team_sorted = team_combined.sort_values('percentage', ascending=True)
    colors_sorted = [color_dict[team] for team in team_sorted['posteam']]
    
    bars1 = ax1.barh(range(len(team_sorted)), team_sorted['percentage'], 
                     color=colors_sorted, alpha=0.8, edgecolor='white', linewidth=0.5)
    
    ax1.set_yticks(range(len(team_sorted)))
    ax1.set_yticklabels(team_sorted['posteam'])
    ax1.set_xlabel('Go For It Rate (%)', fontweight='bold')
    ax1.set_title(f'Team 4th Down Aggressiveness\n({current_year-recent_years+1}-{current_year})', 
                  fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars1, team_sorted['percentage'])):
        ax1.text(value + 0.5, i, f'{value:.1f}%', va='center', fontsize=9)
    
    # 2. Success rate vs aggressiveness scatter
    scatter = ax2.scatter(team_combined['percentage'], team_combined['success_rate'], 
                         c=[color_dict[team] for team in team_combined['posteam']], 
                         s=120, alpha=0.8, edgecolors='white', linewidth=1)
    
    # Add team labels
    for _, row in team_combined.iterrows():
        ax2.annotate(row['posteam'], (row['percentage'], row['success_rate']), 
                    xytext=(3, 3), textcoords='offset points', fontsize=9, fontweight='bold')
    
    ax2.set_xlabel('Go For It Rate (%)', fontweight='bold')
    ax2.set_ylabel('Conversion Success Rate (%)', fontweight='bold')
    ax2.set_title('Aggressiveness vs Success Rate\n4th Down Efficiency', 
                  fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Add reference lines
    avg_aggression = team_combined['percentage'].mean()
    avg_success = team_combined['success_rate'].mean()
    ax2.axvline(x=avg_aggression, color='gray', linestyle='--', alpha=0.7, label=f'Avg Aggression ({avg_aggression:.1f}%)')
    ax2.axhline(y=avg_success, color='gray', linestyle='--', alpha=0.7, label=f'Avg Success ({avg_success:.1f}%)')
    ax2.legend(loc='upper right', framealpha=0.9)
    
    plt.suptitle(f'NFL Team 4th Down Analysis ({current_year-recent_years+1}-{current_year})', 
                 fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    return fig


def main():
    """Create 4th down evolution analysis."""
    print("🏈 NFL 4th Down Strategy Evolution Analysis")
    print("=" * 60)
    
    # Configuration
    YEARS = list(range(2015, 2025))  # 10 years of analysis
    
    try:
        # Load and process data
        fourth_down_data = load_fourth_down_data(YEARS)
        categorized_data = categorize_fourth_downs(fourth_down_data)
        
        # Analyze trends
        go_for_it_trends, success_data = analyze_fourth_down_trends(categorized_data)
        
        # Create visualizations
        print("\n📊 Creating visualizations...")
        
        # 1. Trends over time
        fig1 = create_fourth_down_trends_plot(go_for_it_trends, success_data)
        output_dir = os.path.dirname(__file__)
        trends_path = os.path.join(output_dir, 'seaborn_fourth_down_evolution.png')
        fig1.savefig(trends_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"💾 Saved trends analysis: {trends_path}")
        plt.close(fig1)
        
        # 2. Team aggressiveness
        fig2 = create_team_aggressiveness_plot(categorized_data)
        team_path = os.path.join(output_dir, 'seaborn_team_fourth_down_aggressiveness.png')
        fig2.savefig(team_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"💾 Saved team analysis: {team_path}")
        plt.close(fig2)
        
        print("\n" + "=" * 60)
        print("✅ 4th Down analysis completed successfully!")
        
        # Summary statistics
        total_plays = len(categorized_data)
        go_for_it_rate_2015 = go_for_it_trends[go_for_it_trends['season'] == 2015]['percentage'].mean()
        go_for_it_rate_recent = go_for_it_trends[go_for_it_trends['season'] == max(YEARS)]['percentage'].mean()
        
        print(f"\n📈 Key Findings:")
        print(f"   Total 4th down plays analyzed: {total_plays:,}")
        print(f"   Years covered: {min(YEARS)}-{max(YEARS)}")
        print(f"   Average 'Go For It' rate in {min(YEARS)}: {go_for_it_rate_2015:.1f}%")
        print(f"   Average 'Go For It' rate in {max(YEARS)}: {go_for_it_rate_recent:.1f}%")
        print(f"   Increase over time: +{go_for_it_rate_recent - go_for_it_rate_2015:.1f} percentage points")
        
        # Distance breakdown
        print(f"\n📊 Most recent season breakdown:")
        recent_data = categorized_data[categorized_data['season'] == max(YEARS)]
        distance_breakdown = recent_data.groupby(['distance_category', 'decision']).size().unstack(fill_value=0)
        distance_breakdown['Go For It %'] = (distance_breakdown.get('Go For It', 0) / distance_breakdown.sum(axis=1) * 100).round(1)
        print(distance_breakdown[['Go For It %']].to_string())
        
    except Exception as e:
        print(f"\n❌ Error creating analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()