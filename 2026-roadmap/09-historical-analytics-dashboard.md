# Historical Analytics & Insights Dashboard

**Category:** New Feature | DX Improvement
**Quarter:** Q3-Q4
**T-shirt Size:** L

## Why This Matters

Spotify Wrapped exists for a reason—people love understanding their listening patterns. But Wrapped is once a year, controlled by Spotify, and limited in scope. Users want to explore their listening history on their own terms: custom date ranges, deeper analysis, exportable reports.

A historical analytics dashboard turns collected listening data into actionable insights and beautiful visualizations. This is the payoff for all the data collection work—the feature that makes users say "wow, I had no idea I listened to that much jazz in April."

## Current State

- **Historical data:** None stored (each query is independent)
- **Analytics:** None (raw API responses only)
- **Visualization:** None (JSON output only)
- **Custom date ranges:** Limited (`--before`, `--after` on recently-played)
- **Aggregations:** None (no summaries, counts, or statistics)

Current capability is point-in-time only:
```bash
esporifai get-recently-played  # Last 50 tracks, no history
```

## Proposed Future State

A comprehensive analytics system with terminal and web dashboards:

**Time-Series Analytics:**
- Listening time by hour/day/week/month/year
- Artist/track/genre trends over time
- Listening session analysis (duration, frequency)
- Discovery rate tracking (new vs. familiar)
- Skipped track analysis (if available)

**Comparative Analysis:**
- This week vs. last week
- This month vs. same month last year
- Weekday vs. weekend patterns
- Morning vs. evening listening

**Personal Insights:**
- Listening personality classification
- Genre diversity score over time
- "Deepest cuts" (most obscure tracks)
- Loyalty metrics (most consistent artists)
- Mood trajectory analysis

**Visualizations:**
- Terminal dashboard using Rich/Textual
- ASCII art charts for trends
- Calendar heatmaps
- Genre sunburst diagrams
- Artist network graphs

**Web Dashboard (Optional):**
- Local web server with interactive charts
- Exportable HTML reports
- Shareable static reports

**Reports:**
- Weekly/monthly listening summaries
- Custom date range reports
- "Your Year in Music" generator
- PDF export with charts

## Key Deliverables

- [ ] Create listening history aggregation engine
- [ ] Implement time-series rollups (hourly → daily → monthly)
- [ ] Build terminal dashboard using Rich or Textual
- [ ] Create `esporifai stats` command for quick summaries
- [ ] Implement `esporifai stats --period week/month/year`
- [ ] Add `esporifai stats --from DATE --to DATE`
- [ ] Create ASCII chart library for terminal visualization
- [ ] Implement calendar heatmap visualization
- [ ] Build comparative analysis ("vs last week")
- [ ] Create listening personality classifier
- [ ] Implement genre diversity scoring
- [ ] Add "deepest cuts" finder (obscure tracks)
- [ ] Create artist loyalty rankings
- [ ] Build local web dashboard using Flask/FastAPI
- [ ] Implement interactive charts with Plotly
- [ ] Create PDF report generator
- [ ] Add shareable HTML export
- [ ] Implement "Year in Music" generator
- [ ] Create scheduled report generation

## Prerequisites

- Initiative 05 (Real-Time Analytics) provides the historical data
- Initiative 07 (AI Engine) enables personality/mood analysis
- Initiative 04 (Data Export) for report generation

## Risks & Open Questions

- How much historical data before analytics are meaningful? (Minimum 30 days?)
- Terminal dashboard framework: Rich's Live display vs. Textual's full TUI?
- Web dashboard: worth the added complexity? Start terminal-only?
- How to handle missing data gaps in historical collection?
- Performance of aggregations on large datasets (years of history)?
- How to make terminal visualizations accessible?

## Notes

Analytics aggregation strategy:
- Raw data: individual play events
- Hourly rollups: plays per hour
- Daily summaries: unique artists, tracks, genres, total time
- Weekly/monthly: aggregated summaries with trends

Terminal visualization options:
- **Rich:** Already a dependency, good for dashboards
- **Textual:** Full TUI framework, by same author as Rich
- **asciichartpy:** Simple ASCII line charts
- **termgraph:** Terminal bar charts

Web dashboard stack (if pursued):
- **FastAPI** + **uvicorn** for local server
- **Jinja2** for templates
- **Plotly** for interactive charts
- **Chart.js** as lightweight alternative

New files:
```
esporifai/
├── analytics/
│   ├── aggregations.py   # Rollup calculations
│   ├── comparisons.py    # Period comparisons
│   ├── insights.py       # Derived insights
│   └── personality.py    # Listener classification
├── visualization/
│   ├── terminal.py       # Rich/Textual dashboards
│   ├── charts.py         # ASCII charts
│   └── calendar.py       # Heatmap
└── reports/
    ├── generator.py      # Report building
    ├── templates/        # HTML/PDF templates
    └── year_in_review.py # Special annual report
```

Example terminal dashboard output:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 esporifai · Weekly Summary · Dec 23-29, 2025             │
├─────────────────────────────────────────────────────────────┤
│ Total Listening: 14h 32m (↑12% from last week)              │
│ Unique Tracks: 187   Unique Artists: 54   New Discoveries: 8│
├─────────────────────────────────────────────────────────────┤
│ Top Artists          │ Listening by Hour                    │
│ 1. The Beatles (2h)  │ ▁▁▂▃▅▇█▆▄▃▂▂▃▄▅▆▇█▇▅▄▃▂▁         │
│ 2. Queen (1.5h)      │ 12am        12pm        12am         │
│ 3. Pink Floyd (1h)   │                                      │
├─────────────────────────────────────────────────────────────┤
│ Mood: Upbeat (72% high-valence tracks)                      │
│ Genre Diversity: 7.3/10                                     │
└─────────────────────────────────────────────────────────────┘
```
