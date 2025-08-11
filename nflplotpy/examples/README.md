# nflplotpy Examples 🏈

Welcome to the nflplotpy examples directory! This collection of scripts demonstrates the full capabilities of nflplotpy, the Python equivalent of R's nflplotR package for NFL data visualization.

## 📋 Quick Start

1. **Install Requirements**
   ```bash
   pip install -e .  # Install nfl_data_py with nflplotpy
   ```

2. **Run Examples**
   ```bash
   # Comprehensive feature demo
   python nflplotpy_demo.py

   # Matplotlib examples
   python matplotlib/nfl_examples.py                  # Basic logo/epa demo

   # Quick functionality test
   python quick_test.py

   # Seaborn examples
   python seaborn/seaborn_team_schedule.py                    # KC 2024 schedule analysis
   python seaborn/seaborn_team_schedule.py --team BUF         # Buffalo Bills analysis
   python seaborn/seaborn_team_schedule.py --team SF --year 2023  # 49ers 2023 season
   python seaborn/seaborn_fourth_down_evolution.py            # 4th down trends analysis
   python seaborn/seaborn_week_net_success.py -y 2024 -w 10   # League weekly net SR
   python seaborn/seaborn_week_net_success.py -y 2024 -t KC   # Team season net SR

   # Plotly examples (interactive)
   python plotly/plotly_team_schedule.py                      # Interactive schedule
   python plotly/plotly_team_schedule.py --default-team BUF   # Start with Bills selected
   python plotly/plotly_fourth_down_evolution.py              # Interactive 4th down dashboard
   ```

## 📊 Available Examples

### 1. `nflplotpy_demo.py` - Complete Feature Showcase

**What it demonstrates:**
- 🎨 **Team Colors**: Official NFL color palettes
- 🏟️ **Team Organization**: Conference/division groupings  
- 💾 **Asset Management**: Logo caching system
- 📊 **Matplotlib Integration**: Dots vs logos comparison
- 🚀 **High-Level Functions**: One-line plotting with `plot_team_stats()`
- 🎯 **Color Palettes**: Advanced color management
- 📈 **Real Data Integration**: Using nfl_data_py for authentic data

**Key Features:**
- Side-by-side comparison of traditional dots vs modern team logos
- Proper User-Agent handling for logo downloads
- Professional NFL styling and themes
- Reference lines for statistical context

**Output Files:**
- `matplotlib_integration_demo.png`
- `high_level_team_plot.png`
- `real_data_demo.png` (if internet available)

### 2. `real_data_examples.py` - Authentic NFL Analytics

**What it demonstrates:**
- 📊 **Real 2024 NFL Data**: Live play-by-play analysis
- 🏈 **Team Logos**: All plots use actual team logos instead of dots
- 📈 **EPA Analysis**: Expected Points Added per play metrics
- 🏆 **Multiple Views**: All teams, divisions, conferences
- 🎯 **Statistical Context**: Reference lines and quadrant analysis

**Key Metrics:**
- Offensive EPA per play
- Defensive EPA per play allowed  
- Team performance quadrants
- Division and conference comparisons

**Output Files:**
- `2024_real_all_teams_epa.png` - All 32 teams overview
- `2024_real_divisions_epa.png` - 8 division breakdown
- `2024_real_conferences_epa.png` - AFC vs NFC comparison

### 3. `quick_test.py` - Fast Functionality Check

**What it demonstrates:**
- ⚡ **Quick Setup Test**: Verify installation
- 🎨 **Basic Colors**: Simple color retrieval
- 🏈 **Logo Loading**: Test logo download system
- ✅ **System Check**: Validate all components work

## 🔑 Key Features Explained

### Team Logos vs Dots

**Traditional Approach (Dots):**
```python
# Old way - colored dots with team labels
colors = nflplot.get_team_colors(teams, 'primary')
ax.scatter(x, y, c=colors, s=200)
```

**Modern Approach (Logos):**
```python  
# New way - actual team logos
ax.scatter(x, y, c='white', s=1, alpha=0.01)  # Invisible positioning
add_nfl_logos(ax, teams, x, y, width=0.15)    # Add logos
```

### High-Level Function

The easiest way to create NFL plots:

```python
fig = nflplot.plot_team_stats(
    data,
    x='offensive_epa', 
    y='defensive_epa',
    show_logos=True,  # 🔑 Enable team logos
    add_reference_lines=True,
    title='Team Performance Analysis'
)
```

### Logo System Features

- ✅ **35+ working team logos** from official nflverse data
- 💾 **Automatic caching** for fast subsequent use
- 🔄 **Fallback system** gracefully handles failed downloads
- 📏 **Adjustable sizing** with `width` parameter
- 🎯 **Professional quality** suitable for presentations

## 🛠️ Customization

### Logo Sizes
```python
width=0.08   # Small logos
width=0.12   # Medium logos (default)
width=0.18   # Large logos
```

### Reference Lines
```python
add_reference_lines=True,
reference_type='median'  # or 'mean' or 'both'
```

### NFL Themes
```python
nflplot.apply_nfl_theme(ax, style='default')  # or 'minimal'
```

## 📋 Common Use Cases

1. **Team Performance Analysis**
   - EPA efficiency plots
   - Win rate comparisons
   - Offensive vs defensive metrics

2. **Division/Conference Breakdowns**
   - Comparing teams within divisions
   - AFC vs NFC analysis
   - Playoff race visualizations

3. **Season Tracking**
   - Week-by-week progression
   - Trend analysis
   - Performance correlation studies

## 🔍 Troubleshooting

### Logo Issues
If logos aren't loading:
1. Check internet connection
2. Verify User-Agent headers are working
3. Look for fallback to colored dots
4. Check cache directory permissions

### Data Issues  
If real data examples fail:
1. Ensure `nfl_data_py` is installed
2. Check internet connection for data download
3. Verify year parameter (2024 data availability)

### Import Issues
```python
# Make sure path is set correctly
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
```

## 🎨 NEW: Seaborn & Plotly Examples

### 4. `seaborn_team_schedule.py` - Team Schedule Analysis with Seaborn

**What it demonstrates:**
- 🏈 **Individual Team Focus**: Analyze single team's complete season
- 📊 **Game Results vs Spreads**: Compare actual performance to betting lines  
- 🎯 **Seaborn Integration**: Publication-quality statistical visualizations
- 📈 **Spread Performance**: Track how teams perform against expectations
- 🏆 **Multi-Team Comparison**: Compare multiple teams' spread performance

**Key Features:**
- Horizontal bar charts showing score differential vs pre-game spread
- Color coding for wins/losses and spread performance
- Statistical summaries and team comparisons
- Professional seaborn styling for publications
- **Command line arguments**: `--team`, `--year`, `--comparison-teams`, `--no-comparison`

**Output Files:**
- `seaborn_[team]_[year]_schedule.png` - Individual team detailed analysis
- `seaborn_teams_comparison_[year].png` - Multi-team comparison charts

### 5. `plotly_team_schedule.py` - Interactive Team Schedule Dashboard

**What it demonstrates:**
- 🎮 **Interactive Team Selection**: Dropdown menu to switch between all teams
- 🔍 **Rich Hover Information**: Detailed game stats, scores, spreads on hover
- 📊 **Multiple Views**: Team schedule, spread heatmap, animated progression
- 📱 **Web-Based**: Output as HTML files for sharing and presenting

**Key Features:**
- Interactive team selector with all 32 teams
- Animated season progression showing win rate vs spread performance
- Heatmap visualization of spread performance by team and week
- Detailed hover tooltips with game context and results
- **Command line arguments**: `--year`, `--default-team`, `--skip-heatmap`, `--skip-animation`

**Output Files:**
- `plotly_team_schedule_[year].html` - Interactive team schedule selector
- `plotly_spread_heatmap_[year].html` - League-wide spread performance heatmap
- `plotly_season_animation_[year].html` - Animated season progression

### 6. `seaborn_fourth_down_evolution.py` - 4th Down Strategy Analytics

**What it demonstrates:**
- 📈 **Multi-Year Trend Analysis**: Track 4th down strategy evolution (2015-2024)
- 🎯 **Distance Categories**: Break down by 4th & short, medium, long, very long
- 📊 **Team Aggressiveness**: Compare team 4th down philosophies
- 🏈 **Success Rate Analysis**: Track conversion rates and strategy effectiveness
- 📉 **Seaborn Statistical Plots**: Heatmaps, trend lines, and correlation analysis

**Key Insights:**
- Validates the "analytics revolution" in NFL decision-making
- Shows dramatic increase in "going for it" rates since 2015
- Reveals which teams are most/least aggressive on 4th down
- Analyzes success rates by distance and situation

**Output Files:**
- `seaborn_fourth_down_evolution.png` - Comprehensive trends analysis
- `seaborn_team_fourth_down_aggressiveness.png` - Team comparison charts

### 7. `plotly_fourth_down_evolution.py` - Interactive 4th Down Dashboard

**What it demonstrates:**
- 🎬 **Animated Timeline**: Watch 4th down strategy evolve year by year
- 🎮 **Interactive Filtering**: Filter by team, distance, field position
- 📊 **Multi-Perspective Dashboard**: Multiple views in single interface
- 🎯 **Situational Analysis**: Drill down by field position and game context
- 📱 **Rich Interactivity**: Hover, zoom, filter, and explore data dynamically

**Key Features:**
- Animated bar chart showing evolution of aggressiveness by distance
- Interactive team comparison dashboard with multiple metrics
- Situational heatmap analysis by field position and distance
- Animated scatter plot showing team performance over time

**Output Files:**
- `plotly_fourth_down_trends_animated.html` - Animated trends timeline
- `plotly_fourth_down_team_dashboard.html` - Interactive team comparison
- `plotly_fourth_down_situational.html` - Situational analysis tool

## 🆕 What's New in Seaborn & Plotly Examples

### **Advanced Data Integration**
- **Betting Lines**: Direct integration with `import_schedules()` for spread analysis
- **Multi-Year Analysis**: Comprehensive trends across 10 seasons (2015-2024)  
- **Rich Statistics**: Success rates, team comparisons, situational breakdowns

### **Professional Visualizations**
- **Seaborn**: Publication-quality statistical plots with NFL team colors
- **Plotly**: Interactive web-based dashboards with animation and filtering
- **Team Branding**: Consistent use of official NFL team colors throughout

### **Real Analytics Questions**
- **Schedule Performance**: How do teams perform vs betting expectations?
- **Strategy Evolution**: How much more aggressive are teams on 4th down now?
- **Team Philosophy**: Which teams are most/least aggressive in key situations?

## 🎯 Next Steps

1. **Modify Examples**: Edit the scripts to use your own data
2. **Create Custom Plots**: Use `plot_team_stats()` with your metrics
3. **Explore Colors**: Try different team color combinations
4. **Add Reference Lines**: Use median/mean lines for context
5. **Export High-DPI**: Save plots with `dpi=300` for presentations
6. **🆕 Try Interactive**: Run the plotly examples and open HTML outputs in browser
7. **🆕 Analyze Trends**: Use the 4th down scripts to validate your own hypotheses

## 📚 Documentation

- **Package Documentation**: See parent directory README files
- **Function Documentation**: All functions have detailed docstrings
- **nfl_data_py Integration**: Check nfl_data_py documentation for data options
- **Matplotlib Integration**: Standard matplotlib customization applies
- **🆕 Seaborn Integration**: Statistical plotting with NFL data and team branding
- **🆕 Plotly Integration**: Interactive web-based NFL analytics dashboards

---

**Happy plotting! 🏈📊**

*Questions? Check the test files in `nflplotpy/tests/` for more code examples.*