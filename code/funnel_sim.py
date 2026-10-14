#!/usr/bin/env python3
"""
Free-session + mid-session "pause and continue?" upsell: a funnel model with
the psychology made explicit.

Every psychological effect is a named multiplier, so you can switch each one
off and see how much of the result it carries. All numbers are ASSUMPTIONS
chosen to be plausible and loosely anchored to the studies cited in the
README; they are not measured for any real business. Change them.

Standard library only.  Run:  python3 funnel_sim.py
"""

import random
import statistics

# ---------------------------------------------------------------- business
RATE_PER_HOUR = 120.0        # full price, 60-minute massage
CONSUMABLES_PER_SESSION = 8.0  # oil, linen, laundry
INTRO_SLOTS = 40             # intro sessions you are willing to give away
MONTHS = 12

# ------------------------------------------------------- two kinds of client
# "deal" = shows up mainly for the price; "value" = wanted a massage anyway.
CLIENT_TYPES = {
    #           first full-price rebook | monthly retention after that
    "deal":  {"rebook": 0.10, "retain": 0.55},
    "value": {"rebook": 0.40, "retain": 0.80},
}

# Chance of agreeing to pay for the rest of the session when paused mid-way.
EXTEND_BASE = {"deal": 0.20, "value": 0.40}

# ------------------------------------------------------- psychology levers
# 1 = effect off.  See README "Deep dive" for the evidence behind each.
PSYCH = {
    # Adverse selection: share of the intro cohort who are deal-seekers,
    # by price of the intro offer (free attracts the most).
    "deal_share": {"free": 0.65, "discount": 0.45, "full": 0.25},
    # Reciprocity: a gift raises the odds of a first paid rebook.
    "reciprocity": {"free": 1.25, "discount": 1.10, "full": 1.00},
    # Hot state + endowment + interruption: being relaxed, undressed and
    # mid-experience makes "continue?" much easier to say yes to.
    "hot_state_extend": 1.50,
    # Persuasion knowledge / reactance: a pitch on the table can feel like a
    # tactic. Multiplier on later rebooking for people who said no...
    "reactance_decliners": 0.60,
    # ...and a smaller hit for people who said yes but felt pushed.
    "reactance_accepters": 0.90,
    # Zero-price anchor: a free first session makes $120 feel steep later.
    "zero_anchor_retain": {"free": 0.92, "discount": 0.97, "full": 1.00},
}

STRATEGIES = {
    # name: (intro price tier, intro minutes, intro price $, mid-session pitch?)
    "A. Free 30 + pause pitch (reel)": ("free", 30, 0.0, True),
    "B. Free 30, offer after":         ("free", 30, 0.0, False),
    "C. $49 intro 60 min":             ("discount", 60, 49.0, False),
    "D. Full price + guarantee":       ("full", 60, 120.0, False),
}


def expected_cohort(tier, minutes, price, pitch, psych=PSYCH):
    """Expected 12-month outcome for INTRO_SLOTS intro clients."""
    deal_share = psych["deal_share"][tier]
    out = {"revenue": 0.0, "hours": 0.0, "free_hours": 0.0,
           "regulars_m6": 0.0, "costs": 0.0, "extended": 0.0}

    for ctype, share in (("deal", deal_share), ("value", 1 - deal_share)):
        n = INTRO_SLOTS * share
        p = CLIENT_TYPES[ctype]

        # intro session
        out["revenue"] += n * price
        out["hours"] += n * minutes / 60
        if price == 0:
            out["free_hours"] += n * minutes / 60
        out["costs"] += n * CONSUMABLES_PER_SESSION

        rebook = p["rebook"] * psych["reciprocity"][tier]
        retain = min(p["retain"] * psych["zero_anchor_retain"][tier], 0.99)

        if pitch:
            p_ext = min(EXTEND_BASE[ctype] * psych["hot_state_extend"], 0.95)
            ext_hours = (60 - minutes) / 60
            out["extended"] += n * p_ext
            out["revenue"] += n * p_ext * ext_hours * RATE_PER_HOUR
            out["hours"] += n * p_ext * ext_hours
            rebook_eff = (p_ext * rebook * psych["reactance_accepters"]
                          + (1 - p_ext) * rebook * psych["reactance_decliners"])
        else:
            rebook_eff = rebook

        # paying regulars: rebook once, then monthly visits with retention
        active = n * min(rebook_eff, 0.99)
        for month in range(1, MONTHS):
            out["revenue"] += active * RATE_PER_HOUR
            out["hours"] += active
            out["costs"] += active * CONSUMABLES_PER_SESSION
            if month == 6:
                out["regulars_m6"] += active
            active *= retain

    out["profit"] = out["revenue"] - out["costs"]
    out["rev_per_hour"] = out["revenue"] / out["hours"]
    return out


def simulate_once(tier, minutes, price, pitch, rng, psych=PSYCH):
    """One random draw of the same funnel (for spread, not just the mean)."""
    revenue = 0.0
    for _ in range(INTRO_SLOTS):
        ctype = "deal" if rng.random() < psych["deal_share"][tier] else "value"
        p = CLIENT_TYPES[ctype]
        revenue += price
        rebook = p["rebook"] * psych["reciprocity"][tier]
        retain = min(p["retain"] * psych["zero_anchor_retain"][tier], 0.99)
        if pitch:
            p_ext = min(EXTEND_BASE[ctype] * psych["hot_state_extend"], 0.95)
            if rng.random() < p_ext:
                revenue += (60 - minutes) / 60 * RATE_PER_HOUR
                rebook *= psych["reactance_accepters"]
            else:
                rebook *= psych["reactance_decliners"]
        if rng.random() < rebook:
            for _month in range(1, MONTHS):
                revenue += RATE_PER_HOUR
                if rng.random() > retain:
                    break
    return revenue


def with_lever_off(name):
    """Copy of PSYCH with one lever neutralised (set to 1 / no effect)."""
    psych = {k: (dict(v) if isinstance(v, dict) else v) for k, v in PSYCH.items()}
    if name == "deal_share":
        psych[name] = {t: PSYCH[name]["full"] for t in PSYCH[name]}
    elif isinstance(psych[name], dict):
        psych[name] = {t: 1.0 for t in psych[name]}
    else:
        psych[name] = 1.0
    return psych


def main():
    print(f"Cohort: {INTRO_SLOTS} intro clients, {MONTHS}-month horizon, "
          f"${RATE_PER_HOUR:.0f}/hr full price\n")
    hdr = (f"{'strategy':34}{'12-mo rev':>10}{'profit*':>9}{'hands-on h':>11}"
           f"{'free h':>8}{'$/hour':>8}{'regulars@m6':>12}{'extended':>9}")
    print(hdr)
    print("-" * len(hdr))
    results = {}
    for name, args in STRATEGIES.items():
        r = expected_cohort(*args)
        results[name] = r
        print(f"{name:34}{r['revenue']:>10,.0f}{r['profit']:>9,.0f}"
              f"{r['hours']:>11.0f}{r['free_hours']:>8.0f}{r['rev_per_hour']:>8.0f}"
              f"{r['regulars_m6']:>12.1f}{r['extended']:>9.1f}")
    print("* profit = revenue minus consumables; therapist time not costed.\n")

    # Same cohort size is unfair to "free": free fills slots far more easily.
    # So: how many intro clients would each strategy need to match D's
    # regulars at month 6?
    target = results["D. Full price + guarantee"]["regulars_m6"]
    print(f"Intro clients needed to end month 6 with {target:.1f} regulars "
          f"(D's result):")
    for name, r in results.items():
        need = INTRO_SLOTS * target / r["regulars_m6"]
        print(f"  {name:34} {need:>5.0f}")
    print()

    print("Spread for 1,000 simulated cohorts (12-month revenue, seed 7):")
    rng = random.Random(7)
    for name, args in STRATEGIES.items():
        draws = sorted(simulate_once(*args, rng) for _ in range(1000))
        p10, p50, p90 = draws[100], draws[500], draws[900]
        print(f"  {name:34} P10 {p10:>7,.0f}   median {p50:>7,.0f}   P90 {p90:>7,.0f}")

    print("\nWhich psychology carries strategy A? (revenue if one lever is off)")
    base = results["A. Free 30 + pause pitch (reel)"]["revenue"]
    args = STRATEGIES["A. Free 30 + pause pitch (reel)"]
    rows = []
    for lever in PSYCH:
        r = expected_cohort(*args, psych=with_lever_off(lever))["revenue"]
        rows.append((r - base, lever, r))
    for delta, lever, r in sorted(rows, key=lambda x: -abs(x[0])):
        print(f"  {lever:22} off -> {r:>7,.0f}  ({delta:+,.0f})")

    print("\nBreak-even: how mild must reactance be for A to beat B?")
    b_rev = results["B. Free 30, offer after"]["revenue"]
    for dec in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        psych = dict(PSYCH)
        psych["reactance_decliners"] = dec
        a = expected_cohort(*args, psych=psych)["revenue"]
        flag = "A wins" if a > b_rev else "B wins"
        print(f"  decliners keep {dec:.0%} of rebook intent -> A {a:>7,.0f} "
              f"vs B {b_rev:>7,.0f}  {flag}")


if __name__ == "__main__":
    main()
