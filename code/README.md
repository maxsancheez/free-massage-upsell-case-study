# funnel_sim.py

A model of a massage or facial practice comparing four ways to get new clients:

| | Strategy |
|---|---|
| A | Free 30-minute session, paused mid-way with "want me to continue? it's $X" (the reel's tactic) |
| B | Free 30-minute session, booking offer made afterwards, clothed, no pressure |
| C | $49 intro for a full 60 minutes |
| D | Full price with a money-back guarantee |

Each psychological effect (adverse selection, reciprocity, hot state, reactance, zero-price anchoring) is a named multiplier in `PSYCH`. Setting one to 1 switches it off. All numbers are assumptions, loosely anchored to the studies in the main README. Edit them to match your own practice.

## Run

Standard library only, Python 3.8+.

```bash
python3 funnel_sim.py
```

## What it prints

1. Expected 12-month revenue, hands-on hours, free hours, revenue per hour, and regulars at month 6 for a 40-client cohort
2. How many intro clients each strategy needs to match strategy D's regulars
3. P10, median and P90 revenue across 1,000 simulated cohorts (seed 7, so results repeat)
4. Which psychology lever carries strategy A, found by switching each lever off
5. The break-even: how mild the backlash against the on-table pitch has to be for A to beat B
