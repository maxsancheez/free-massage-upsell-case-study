# funnel_sim.py

A model comparing four ways to get new clients, with each piece of the psychology as a dial you can turn. It has two presets.

**`massage` (default): the reel's tactic**

| | Strategy |
|---|---|
| A | Free 30-minute session, paused at halfway with a paid upgrade (price explained up front) |
| B | Free 30-minute session, booking offer made afterwards |
| C | $49 intro for a full 60 minutes |
| D | Full price with a money-back guarantee |

**`dog-daycare`: the same idea for a dog business**

| | Strategy |
|---|---|
| A | Free half-day trial, midday photo and "make it a full day?" text |
| B | Free half-day trial, offer made at pickup |
| C | $25 assessment day, credited toward the first month |
| D | Full price first day |

Each psychological effect (adverse selection, reciprocity, hot state, reactance, zero-price anchoring) is a named multiplier in the preset's `psych` block. Setting one to 1 switches it off. All numbers are assumptions; the main README's Assumptions table shows what each is anchored to. To model your own business, copy a preset in `PRESETS` and edit it.

## Run

Standard library only, Python 3.8+.

```bash
python3 funnel_sim.py
```

```bash
python3 funnel_sim.py --preset dog-daycare
```

## What it prints

1. Expected 12-month revenue, units delivered (hours or dog-days), free units, revenue per unit, regulars at month 6, and upsells accepted, for a 40-client cohort
2. How many intro clients each strategy needs to match strategy D's regulars
3. P10, median and P90 revenue across 1,000 simulated cohorts (seed 7, so results repeat)
4. Which psychology lever carries strategy A, found by switching each lever off
5. The break-even: how mild the backlash against the upsell must be for A to beat B
