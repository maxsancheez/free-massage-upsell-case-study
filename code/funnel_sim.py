#!/usr/bin/env python3
"""
Free-session + mid-session "pause and continue?" upsell: a funnel model with
the psychology made explicit.

Every psychological effect is a named multiplier, so you can switch each one
off and see how much of the result it carries. All numbers are ASSUMPTIONS
chosen to be plausible and loosely anchored to the studies cited in the
README; they are not measured for any real business. Change them.

Two presets:
  massage      free 30-min massage, paused halfway with a paid upgrade (the reel)
  dog-daycare  free half-day trial, midday photo + "make it a full day?" text

Standard library only.  Run:
  python3 funnel_sim.py
  python3 funnel_sim.py --preset dog-daycare
"""

import random
import sys

PRESETS = {
    "massage": {
        "unit": "hands-on h",
        "full_price": 120.0,        # one full 60-minute massage
        "consumables": 8.0,         # oil, linen, laundry per session
        "intro_slots": 40,          # intro sessions you are willing to give away
        "visits_per_month": 1,      # a regular comes about monthly
        # "deal" = came mainly for the price; "value" = wanted it anyway
        "client_types": {
            "deal":  {"rebook": 0.10, "retain": 0.55},
            "value": {"rebook": 0.40, "retain": 0.80},
        },
        # chance of paying to continue when asked at the pause
        "extend_base": {"deal": 0.20, "value": 0.40},
        "psych": {
            # adverse selection: share of deal-seekers by intro price tier
            "deal_share": {"free": 0.65, "discount": 0.45, "full": 0.25},
            # reciprocity: a gift raises the odds of a first paid rebook
            "reciprocity": {"free": 1.25, "discount": 1.10, "full": 1.00},
            # hot state + endowment + interruption at the pause
            "hot_state_extend": 1.50,
            # persuasion knowledge / reactance on later rebooking
            "reactance_decliners": 0.60,
            "reactance_accepters": 0.90,
            # zero-price anchor: free makes full price feel steep later
            "zero_anchor_retain": {"free": 0.92, "discount": 0.97, "full": 1.00},
        },
        # name: (price tier, share of a full unit given as intro, intro price, pitch?)
        "strategies": {
            "A. Free 30 + pause pitch (reel)": ("free", 0.5, 0.0, True),
            "B. Free 30, offer after":         ("free", 0.5, 0.0, False),
            "C. $49 intro 60 min":             ("discount", 1.0, 49.0, False),
            "D. Full price + guarantee":       ("full", 1.0, 120.0, False),
        },
        "units_per_session": 1.0,   # hours per full session
    },
    "dog-daycare": {
        "unit": "dog-days",
        "full_price": 55.0,         # one full day of daycare
        "consumables": 6.0,         # treats, cleaning, extra staff time
        "intro_slots": 40,
        "visits_per_month": 6,      # regulars average ~1.5 days a week
        "client_types": {
            # dogs build routines and friendships, so retention is higher
            "deal":  {"rebook": 0.12, "retain": 0.65},
            "value": {"rebook": 0.45, "retain": 0.85},
        },
        "extend_base": {"deal": 0.20, "value": 0.45},
        "psych": {
            "deal_share": {"free": 0.60, "discount": 0.40, "full": 0.25},
            "reciprocity": {"free": 1.20, "discount": 1.10, "full": 1.00},
            # the "hot state" is a photo of a happy dog sent to the owner
            "hot_state_extend": 1.40,
            # a text to an owner at work is easy to ignore, so milder backlash
            "reactance_decliners": 0.85,
            "reactance_accepters": 0.97,
            "zero_anchor_retain": {"free": 0.94, "discount": 0.98, "full": 1.00},
        },
        "strategies": {
            "A. Free half-day + photo upsell": ("free", 0.5, 0.0, True),
            "B. Free half-day, offer pickup":  ("free", 0.5, 0.0, False),
            "C. $25 assessment day (credit)":  ("discount", 1.0, 25.0, False),
            "D. Full price first day":         ("full", 1.0, 55.0, False),
        },
        "units_per_session": 1.0,   # one day per visit
    },
}

MONTHS = 12


def expected_cohort(cfg, tier, intro_share, price, pitch, psych=None):
    """Expected 12-month outcome for one intro cohort."""
    psych = psych or cfg["psych"]
    full, slots, visits = cfg["full_price"], cfg["intro_slots"], cfg["visits_per_month"]
    unit = cfg["units_per_session"]
    deal_share = psych["deal_share"][tier]
    out = {"revenue": 0.0, "units": 0.0, "free_units": 0.0,
           "regulars_m6": 0.0, "costs": 0.0, "extended": 0.0}

    for ctype, share in (("deal", deal_share), ("value", 1 - deal_share)):
        n = slots * share
        p = cfg["client_types"][ctype]

        # intro session
        out["revenue"] += n * price
        out["units"] += n * intro_share * unit
        if price == 0:
            out["free_units"] += n * intro_share * unit
        out["costs"] += n * cfg["consumables"]

        rebook = p["rebook"] * psych["reciprocity"][tier]
        retain = min(p["retain"] * psych["zero_anchor_retain"][tier], 0.99)

        if pitch:
            p_ext = min(cfg["extend_base"][ctype] * psych["hot_state_extend"], 0.95)
            rest = 1 - intro_share
            out["extended"] += n * p_ext
            out["revenue"] += n * p_ext * rest * full
            out["units"] += n * p_ext * rest * unit
            rebook_eff = (p_ext * rebook * psych["reactance_accepters"]
                          + (1 - p_ext) * rebook * psych["reactance_decliners"])
        else:
            rebook_eff = rebook

        # paying regulars: rebook once, then monthly visits with retention
        active = n * min(rebook_eff, 0.99)
        for month in range(1, MONTHS):
            out["revenue"] += active * visits * full
            out["units"] += active * visits * unit
            out["costs"] += active * visits * cfg["consumables"]
            if month == 6:
                out["regulars_m6"] += active
            active *= retain

    out["profit"] = out["revenue"] - out["costs"]
    out["rev_per_unit"] = out["revenue"] / out["units"]
    return out


def simulate_once(cfg, tier, intro_share, price, pitch, rng):
    """One random draw of the same funnel (for spread, not just the mean)."""
    psych, full = cfg["psych"], cfg["full_price"]
    revenue = 0.0
    for _ in range(cfg["intro_slots"]):
        ctype = "deal" if rng.random() < psych["deal_share"][tier] else "value"
        p = cfg["client_types"][ctype]
        revenue += price
        rebook = p["rebook"] * psych["reciprocity"][tier]
        retain = min(p["retain"] * psych["zero_anchor_retain"][tier], 0.99)
        if pitch:
            p_ext = min(cfg["extend_base"][ctype] * psych["hot_state_extend"], 0.95)
            if rng.random() < p_ext:
                revenue += (1 - intro_share) * full
                rebook *= psych["reactance_accepters"]
            else:
                rebook *= psych["reactance_decliners"]
        if rng.random() < rebook:
            for _month in range(1, MONTHS):
                revenue += cfg["visits_per_month"] * full
                if rng.random() > retain:
                    break
    return revenue


def with_lever_off(psych, name):
    """Copy of psych with one lever neutralised (set to 1 / no effect)."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in psych.items()}
    if name == "deal_share":
        out[name] = {t: psych[name]["full"] for t in psych[name]}
    elif isinstance(out[name], dict):
        out[name] = {t: 1.0 for t in out[name]}
    else:
        out[name] = 1.0
    return out


def main():
    preset = "massage"
    if "--preset" in sys.argv:
        preset = sys.argv[sys.argv.index("--preset") + 1]
    if preset not in PRESETS:
        sys.exit(f"unknown preset {preset!r}; choose from {', '.join(PRESETS)}")
    cfg = PRESETS[preset]
    strategies = cfg["strategies"]
    names = list(strategies)

    print(f"Preset: {preset}. Cohort: {cfg['intro_slots']} intro clients, {MONTHS}-month "
          f"horizon, ${cfg['full_price']:.0f} full price\n")
    unit = cfg["unit"]
    hdr = (f"{'strategy':34}{'12-mo rev':>10}{'profit*':>9}{unit:>11}"
           f"{'free':>8}{'$/unit':>8}{'regulars@m6':>12}{'extended':>9}")
    print(hdr)
    print("-" * len(hdr))
    results = {}
    for name, args in strategies.items():
        r = expected_cohort(cfg, *args)
        results[name] = r
        print(f"{name:34}{r['revenue']:>10,.0f}{r['profit']:>9,.0f}"
              f"{r['units']:>11.0f}{r['free_units']:>8.0f}{r['rev_per_unit']:>8.0f}"
              f"{r['regulars_m6']:>12.1f}{r['extended']:>9.1f}")
    print("* profit = revenue minus consumables; staff time not costed.\n")

    # Same cohort size is unfair to "free": free fills slots far more easily.
    target = results[names[3]]["regulars_m6"]
    print(f"Intro clients needed to end month 6 with {target:.1f} regulars "
          f"(D's result):")
    for name, r in results.items():
        need = cfg["intro_slots"] * target / r["regulars_m6"]
        print(f"  {name:34} {need:>5.0f}")
    print()

    print("Spread for 1,000 simulated cohorts (12-month revenue, seed 7):")
    rng = random.Random(7)
    for name, args in strategies.items():
        draws = sorted(simulate_once(cfg, *args, rng) for _ in range(1000))
        p10, p50, p90 = draws[100], draws[500], draws[900]
        print(f"  {name:34} P10 {p10:>7,.0f}   median {p50:>7,.0f}   P90 {p90:>7,.0f}")

    a_name, b_name = names[0], names[1]
    print(f"\nWhich psychology carries strategy A? (revenue if one lever is off)")
    base = results[a_name]["revenue"]
    rows = []
    for lever in cfg["psych"]:
        r = expected_cohort(cfg, *strategies[a_name],
                            psych=with_lever_off(cfg["psych"], lever))["revenue"]
        rows.append((r - base, lever, r))
    for delta, lever, r in sorted(rows, key=lambda x: -abs(x[0])):
        print(f"  {lever:22} off -> {r:>7,.0f}  ({delta:+,.0f})")

    print("\nBreak-even: how mild must reactance be for A to beat B?")
    b_rev = results[b_name]["revenue"]
    for dec in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        psych = dict(cfg["psych"])
        psych["reactance_decliners"] = dec
        a = expected_cohort(cfg, *strategies[a_name], psych=psych)["revenue"]
        flag = "A wins" if a > b_rev else "B wins"
        print(f"  decliners keep {dec:.0%} of rebook intent -> A {a:>7,.0f} "
              f"vs B {b_rev:>7,.0f}  {flag}")


if __name__ == "__main__":
    main()
