#!/usr/bin/env python3
"""
Weekly Net Success Rate Visualization (Seaborn/Matplotlib)
=========================================================

This example creates a per-week bar chart of game-level net success rates,
placing the team with the higher success rate at the end of the bar and the
opponent team logo at the origin. Positive bars indicate the HOME team had the
higher success rate; negative bars indicate the AWAY team did.

Net Success Rate definition:
  success_rate(team) - success_rate(opponent), where success is defined by
  down-and-distance heuristics:
    - 1st down: gain >= 40% of yards to go
    - 2nd down: gain >= 60% of yards to go
    - 3rd/4th down: gain >= 100% of yards to go

The chart is inspired by commonly shared “Did We Really Get Beat That Bad?”
visuals and is designed for quick, weekly league context.
"""

from __future__ import annotations

import os
import sys
import argparse
from typing import List, Tuple

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Make local package importable when run from examples/
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import nfl_data_py as nfl
import nflplotpy as nflplot
from nflplotpy.matplotlib.artists import add_nfl_logo


def _load_week_pbp(season: int, week: int) -> pd.DataFrame:
    print(f"📥 Loading play-by-play data for {season} Week {week}...")
    pbp = nfl.import_pbp_data([season])

    # Keep regular season, target week only
    pbp = pbp[(pbp.get('season_type') == 'REG') & (pbp.get('week') == week)].copy()

    # Filter to offensive plays only (pass or rush attempts), exclude spikes/kneels
    offensive_mask = (
        (pbp.get('pass_attempt', 0) == 1) | (pbp.get('rush_attempt', 0) == 1)
    )
    pbp = pbp[offensive_mask].copy()

    # Exclude spikes/kneels if present
    if 'qb_spike' in pbp.columns:
        pbp = pbp[pbp['qb_spike'] != 1]
    if 'qb_kneel' in pbp.columns:
        pbp = pbp[pbp['qb_kneel'] != 1]

    # Keep essential columns
    keep_cols = [
        'game_id', 'posteam', 'defteam', 'home_team', 'away_team', 'week', 'down',
        'ydstogo', 'yards_gained'
    ]
    keep_cols = [c for c in keep_cols if c in pbp.columns]
    pbp = pbp[keep_cols].copy()

    # Drop rows without offense team or down info
    pbp = pbp[pbp['posteam'].notna() & pbp['down'].notna() & pbp['ydstogo'].notna()]

    print(f"✅ Loaded {len(pbp):,} offensive snaps for Week {week}")
    return pbp


def _is_success(down: int, yards_gained: float, ydstogo: float) -> bool:
    if pd.isna(yards_gained) or pd.isna(ydstogo):
        return False
    if down == 1:
        return yards_gained >= 0.4 * ydstogo
    if down == 2:
        return yards_gained >= 0.6 * ydstogo
    # 3rd or 4th down
    return yards_gained >= ydstogo


def compute_game_net_success(pbp: pd.DataFrame) -> pd.DataFrame:
    """Compute success rate by team for each game and derive net success rate.

    Returns a DataFrame with one row per game containing:
      - game_id, week, home_team, away_team
      - home_sr, away_sr (success rates as proportions 0-1)
      - net_sr (home_sr - away_sr)
    """
    df = pbp.copy()

    # Success flag
    df['success'] = df.apply(
        lambda r: _is_success(int(r['down']), float(r['yards_gained']), float(r['ydstogo'])),
        axis=1,
    )

    # Offensive success rate by game and posteam
    team_sr = (
        df.groupby(['game_id', 'posteam'])['success']
        .mean()
        .reset_index()
        .rename(columns={'posteam': 'team', 'success': 'success_rate'})
    )

    # Game metadata (home/away/week)
    game_meta = (
        df.groupby('game_id')[['home_team', 'away_team', 'week']]
        .agg('first')
        .reset_index()
    )

    # Pivot to lookups by game
    sr_lookup = team_sr.pivot(index='game_id', columns='team', values='success_rate')

    rows: List[Tuple] = []
    for _, gm in game_meta.iterrows():
        gid = gm['game_id']
        home = gm['home_team']
        away = gm['away_team']

        # Some edge cases: if a team's SR is missing (very rare), skip the game
        try:
            home_sr = float(sr_lookup.loc[gid, home])
            away_sr = float(sr_lookup.loc[gid, away])
        except Exception:
            continue

        rows.append((gid, int(gm['week']), home, away, home_sr, away_sr, home_sr - away_sr))

    result = pd.DataFrame(
        rows,
        columns=['game_id', 'week', 'home_team', 'away_team', 'home_sr', 'away_sr', 'net_sr'],
    )
    return result


def create_week_net_success_plot(games_df: pd.DataFrame, season: int, week: int) -> plt.Figure:
    """Create vertical bar chart of net success rates with logos at bar end and origin."""
    if games_df.empty:
        raise ValueError("No game-level success data to plot")

    # Sort by net success (ascending like the example)
    plot_df = games_df.sort_values('net_sr').reset_index(drop=True).copy()

    # X positions and labels
    plot_df['x'] = np.arange(len(plot_df))
    plot_df['label'] = plot_df.apply(lambda r: f"{r['away_team']} @ {r['home_team']}", axis=1)

    # Colors keyed to the leading team in each game
    lead_teams = np.where(plot_df['net_sr'] >= 0, plot_df['home_team'], plot_df['away_team'])
    colors = []
    for t in lead_teams:
        try:
            colors.append(nflplot.get_team_colors(t, 'primary'))
        except Exception:
            colors.append('#1f77b4')

    # Plot
    plt.style.use('default')
    sns.set_palette('deep')
    fig, ax = plt.subplots(figsize=(18, 8))

    bars = ax.bar(plot_df['x'], plot_df['net_sr'], color=colors, alpha=0.85, edgecolor='white', linewidth=0.6)

    # Zero line
    ax.axhline(0, color='black', linewidth=1.2, alpha=0.4)

    # Logos: leader at bar end, opponent at origin (y=0)
    y_pad = 0.01  # small padding so logos clear the bar end / axis
    for i, row in plot_df.iterrows():
        net = float(row['net_sr'])
        home = row['home_team']
        away = row['away_team']
        x = row['x']

        if net >= 0:
            lead, trail = home, away
        else:
            lead, trail = away, home

        # Place lead logo at the end/tip of the bar
        end_y = net + (y_pad if net >= 0 else -y_pad)
        add_nfl_logo(ax, lead, x=x, y=end_y, target_width_pixels=26, zorder=10)

        # Place trailing logo at origin
        origin_y = 0 + (y_pad if net < 0 else -y_pad)  # nudge away from the axis
        add_nfl_logo(ax, trail, x=x, y=origin_y, target_width_pixels=24, zorder=10)

        # Optional value label
        ax.text(
            x,
            end_y + (0.008 if net >= 0 else -0.008),
            f"{net:+.3f}",
            ha='center', va='bottom' if net >= 0 else 'top', fontsize=8, alpha=0.8,
        )

    # Axis formatting
    ax.set_xticks(plot_df['x'])
    ax.set_xticklabels(plot_df['label'], rotation=60, ha='right')
    ax.set_ylabel('Net Success Rate (Home - Away)')
    ax.set_title(
        f"Did We Really Get Beat that Bad?\nNet Success Rates in Week {week} ({season})",
        fontsize=20, fontweight='bold', pad=16,
    )

    # Subtle grid
    ax.grid(axis='y', linestyle='--', alpha=0.25)
    ax.set_axisbelow(True)

    # Tight layout
    plt.tight_layout()
    return fig


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a weekly Net Success Rate chart with team logos",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python seaborn_week_net_success.py               # Default: 2024 Week 10
  python seaborn_week_net_success.py -y 2023 -w 1  # 2023 Week 1
        """,
    )
    parser.add_argument('--year', '-y', type=int, default=2024, help='Season year (default: 2024)')
    parser.add_argument('--week', '-w', type=int, default=10, help='Week number (default: 10)')
    return parser.parse_args()


def main():
    args = parse_arguments()
    season = args.year
    week = args.week

    try:
        pbp_week = _load_week_pbp(season, week)
        games = compute_game_net_success(pbp_week)

        if games.empty:
            raise ValueError("No games found after processing play-by-play.")

        fig = create_week_net_success_plot(games, season, week)
        out_dir = os.path.dirname(__file__)
        out_path = os.path.join(out_dir, f'seaborn_week_{season}_w{week}_net_success.png')
        fig.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        print(f"💾 Saved weekly net success chart: {out_path}")

    except Exception as e:
        print(f"\n❌ Error creating weekly net success chart: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()


