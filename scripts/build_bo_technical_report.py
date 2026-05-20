#!/usr/bin/env python3
"""Build technical report from BO results JSON."""
import json
from pathlib import Path
from datetime import datetime

def build_bo_technical_report(bo_json_path: str, out_html_path: str):
    with open(bo_json_path) as f:
        data = json.load(f)

    meta = data["meta"]
    results = data["results"]

    profits = [r["profit_mean"] for r in results if r["profit_mean"] is not None]
    best = meta["best_profit"]
    worst = min(profits)
    mean_p = sum(profits)/len(profits)
    median_p = sorted(profits)[len(profits)//2]
    std_p = (sum((p-mean_p)**2 for p in profits)/len(profits))**0.5
    profitable = sum(1 for p in profits if p > 0)

    best_entry = max(results, key=lambda r: r["profit_mean"])
    best_params = best_entry["params"]
    fleet_counts = best_params.get("fleet_counts", {})
    campaigns = best_params.get("campaigns", [])
    yield_curve = best_params.get("yield_curve", [])

    def eur(x): return f"€{x:,.0f}".replace(",", ".")
    def eur2(x): return f"€{x:,.2f}".replace(",", ".")

    top10 = sorted(results, key=lambda r: r["profit_mean"], reverse=True)[:10]
    top10_rows = []
    for i, r in enumerate(top10, 1):
        p = r["params"]
        fleet_total = sum(p.get("fleet_counts", {}).values())
        camp_count = len(p.get("campaigns", []))
        top10_rows.append(
            f"<tr><td>{i}</td><td class='n'>{eur2(r['profit_mean'])}</td>"
            f"<td class='n'>{p.get('weekend_pricing_multiplier', 1.0):.2f}x</td>"
            f"<td class='n'>{p.get('per_hour_cents', 0)}c</td>"
            f"<td class='n'>{p.get('per_km_cents', 0)}c</td>"
            f"<td class='n'>{p.get('km_included_per_day', 0)}</td>"
            f"<td class='n'>{fleet_total}</td>"
            f"<td class='n'>{camp_count}</td></tr>"
        )

    all_rows = []
    for r in results:
        p = r["params"]
        all_rows.append(
            f"<tr><td>{r['config_idx']}</td>"
            f"<td class='n'>{eur2(r['profit_mean'])}</td>"
            f"<td class='n'>{p.get('weekend_pricing_multiplier', 1.0):.3f}x</td>"
            f"<td class='n'>{p.get('per_hour_cents', 0)}</td>"
            f"<td class='n'>{p.get('per_day_cents', 0)}</td>"
            f"<td class='n'>{p.get('per_km_cents', 0)}</td></tr>"
        )

    fleet_rows = []
    if fleet_counts:
        sorted_fleet = sorted(fleet_counts.items(), key=lambda x: int(x[1]), reverse=True)
        total_vehicles = sum(int(v) for v in fleet_counts.values())
        for sid, cnt in sorted_fleet[:15]:
            pct_share = (int(cnt) / total_vehicles * 100) if total_vehicles else 0
            bar_width = min(100, int(pct_share * 3))
            fleet_rows.append(
                f"<tr><td>Station {sid}</td>"
                f"<td class='n'>{cnt}</td>"
                f"<td class='n'>{pct_share:.1f}%</td>"
                f"<td><div style='background:#059669;height:12px;border-radius:4px;width:{bar_width}%'></div></td></tr>"
            )

    camp_rows = []
    for c in campaigns:
        camp_rows.append(
            f"<tr><td>{c.get('segment', 'all').title()}</td>"
            f"<td class='n'>{c.get('discount_pct', 0):.1f}%</td>"
            f"<td class='n'>{c.get('max_customers', 0)}</td></tr>"
        )

    yield_rows = []
    for occ, mult in yield_curve:
        yield_rows.append(
            f"<tr><td class='n'>{occ*100:.0f}% occupancy</td>"
            f"<td class='n'>{mult:.2f}x</td></tr>"
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    elapsed = meta.get("elapsed_sec", 0)
    elapsed_str = f"{int(elapsed//60)} min {int(elapsed%60)} sec"
    
    # Distribution chart bars
    sorted_profits = sorted(profits)
    chart_bars = []
    for i, p in enumerate(sorted_profits):
        color = "#059669" if p > 0 else "#dc2626"
        height = max(2, (p - worst) / (best - worst) * 100)
        chart_bars.append(
            f"<div style='flex:1;min-width:2px;background:{color};"
            f"height:{height}%;border-radius:1px 1px 0 0;' "
            f"title='Config {i+1}: {eur2(p)}'></div>"
        )
    chart_bars = ''.join(chart_bars)

    report = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agent Revenue Simulator - Technical Optimization Report</title>
<style>
:root{{--bg:#f7f9fb;--card:#fff;--text:#1a202c;--muted:#4a5568;--accent:#2563eb;--suc:#059669;--dgr:#dc2626;--brd:#e2e8f0;--r:12px;--sh:0 4px 6px -1px rgba(0,0,0,0.07)}}
*{{box-sizing:border-box}}body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);margin:0;padding:0;line-height:1.6}}
.c{{max-width:1100px;margin:0 auto;padding:32px 16px}}
header{{text-align:center;margin-bottom:32px;padding-bottom:24px;border-bottom:2px solid var(--brd)}}
header h1{{font-size:1.75rem;font-weight:700;margin:0 0 8px}}.sub{{font-size:.95rem;color:var(--muted)}}.meta{{font-size:.8rem;color:#94a3b8;margin-top:12px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}}
.card{{background:var(--card);border-radius:var(--r);padding:20px;box-shadow:var(--sh);border:1px solid var(--brd)}}
.card .l{{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:6px}}.card .v{{font-size:1.5rem;font-weight:700}}.pos{{color:var(--suc)}}.neg{{color:var(--dgr)}}
section{{background:var(--card);border-radius:var(--r);padding:24px;margin-bottom:24px;box-shadow:var(--sh);border:1px solid var(--brd)}}
section h2{{margin:0 0 16px;font-size:1.2rem;font-weight:600}} section h3{{margin:20px 0 10px;font-size:1rem;font-weight:600}}section p{{margin:0 0 12px;color:var(--muted)}}
table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:.9rem}}
th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid var(--brd)}}
th{{background:var(--bg);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
tr:hover td{{background:#f0f4f8}}
.hb{{background:#dbeafe;border-left:4px solid var(--accent);padding:16px;border-radius:0 var(--r) var(--r) 0;margin:16px 0}}
.hb.g{{background:#d1fae5;border-left-color:var(--suc)}}
.hb.r{{background:#fee2e2;border-left-color:var(--dgr)}}
footer{{text-align:center;font-size:.75rem;color:#94a3b8;padding:32px 16px}}
@media(max-width:640px){{.cards{{grid-template-columns:1fr}}}}
</style>
</head>
<body><div class="c">
<header>
  <h1>Technical Optimization Report</h1>
  <p class="sub">Bayesian Optimization over JointState configuration space</p>
  <div class="meta">Algorithm: Bayesian Optimization (scikit-optimize gp_minimize) - {meta["n_calls"]} calls x {meta["seeds_per_eval"]} seeds - Generated {now}</div>
</header>

<div class="cards">
  <div class="card"><div class="l">Best Profit</div><div class="v pos">{eur2(best)}</div></div>
  <div class="card"><div class="l">Worst Profit</div><div class="v neg">{eur2(worst)}</div></div>
  <div class="card"><div class="l">Mean Profit</div><div class="v">{eur2(mean_p)}</div></div>
  <div class="card"><div class="l">Median Profit</div><div class="v">{eur2(median_p)}</div></div>
  <div class="card"><div class="l">Std Deviation</div><div class="v">{eur2(std_p)}</div></div>
  <div class="card"><div class="l">Profitable Configs</div><div class="v pos">{profitable}/{len(profits)} ({profitable/len(profits)*100:.0f}%)</div></div>
  <div class="card"><div class="l">Best Config Index</div><div class="v">#{meta["best_config_idx"]}</div></div>
  <div class="card"><div class="l">Total Simulations</div><div class="v">{meta["total_simulations"]:,}</div></div>
</div>

<section>
  <h2>Run Configuration</h2>
  <table>
    <tr><th>Parameter</th><th class="n">Value</th></tr>
    <tr><td>Algorithm</td><td class="n">Bayesian Optimization (gp_minimize)</td></tr>
    <tr><td>Total calls</td><td class="n">{meta["n_calls"]}</td></tr>
    <tr><td>Random initialization points</td><td class="n">{meta["n_random_starts"]}</td></tr>
    <tr><td>Seeds per evaluation</td><td class="n">{meta["seeds_per_eval"]}</td></tr>
    <tr><td>Total simulations</td><td class="n">{meta["total_simulations"]:,}</td></tr>
    <tr><td>Wall-clock duration</td><td class="n">{elapsed_str}</td></tr>
    <tr><td>Acquisition function</td><td class="n">Expected Improvement (EI)</td></tr>
    <tr><td>Noise model</td><td class="n">Gaussian</td></tr>
    <tr><td>Base seed</td><td class="n">173567</td></tr>
  </table>
</section>

<section>
  <h2>Best Configuration (Config #{meta["best_config_idx"]})</h2>
  <div class="hb g"><strong>Profit:</strong> {eur2(best)}</div>
  <h3>Pricing Parameters</h3>
  <table>
    <tr><th>Parameter</th><th class="n">Value</th></tr>
    <tr><td>Weekend pricing multiplier</td><td class="n">{best_params.get('weekend_pricing_multiplier', 1.0):.3f}x</td></tr>
    <tr><td>Per-hour rate</td><td class="n">{best_params.get('per_hour_cents', 0)}c</td></tr>
    <tr><td>Per-day rate</td><td class="n">{best_params.get('per_day_cents', 0)}c</td></tr>
    <tr><td>Per-km rate</td><td class="n">{best_params.get('per_km_cents', 0)}c</td></tr>
    <tr><td>Km included per day</td><td class="n">{best_params.get('km_included_per_day', 0)}</td></tr>
  </table>

  <h3>Yield Curve</h3>
  <p>Occupancy-based price multipliers:</p>
  <table>
    <tr><th>Occupancy</th><th class="n">Multiplier</th></tr>
    {''.join(yield_rows)}
  </table>

  <h3>Fleet Allocation</h3>
  <p>Vehicle distribution across stations ({sum(int(v) for v in fleet_counts.values())} total):</p>
  <table>
    <tr><th>Station</th><th class="n">Vehicles</th><th class="n">Share</th><th>Visual</th></tr>
    {''.join(fleet_rows)}
  </table>

  <h3>Marketing Campaign</h3>
  <table>
    <tr><th>Target Segment</th><th class="n">Discount</th><th class="n">Max Customers</th></tr>
    {''.join(camp_rows) if camp_rows else "<tr><td colspan='3' style='text-align:center;color:var(--muted)'>No active campaigns</td></tr>"}
  </table>
</section>

<section>
  <h2>Top 10 Configurations</h2>
  <p>Highest-performing parameter combinations discovered by the optimizer:</p>
  <table>
    <tr><th>Rank</th><th class="n">Profit</th><th class="n">Weekend</th><th class="n">Per-hr</th><th class="n">Per-km</th><th class="n">Km inc.</th><th class="n">Fleet</th><th class="n">Campaigns</th></tr>
    {''.join(top10_rows)}
  </table>
</section>

<section>
  <h2>Profit Distribution</h2>
  <p>All {len(profits)} evaluated configurations, sorted by profit:</p>
  <div style="display:flex;flex-wrap:wrap;gap:2px;align-items:flex-end;height:120px;margin:16px 0;padding:8px;background:#fafbfc;border-radius:8px;">
    {chart_bars}
  </div>
  <p style="font-size:.8rem;color:var(--muted)">
    Green = profitable, Red = loss. X-axis: configs sorted by profit. Y-axis: relative profit scale.
    Best: {eur2(best)} - Worst: {eur2(worst)} - Median: {eur2(median_p)}
  </p>
</section>

<section>
  <h2>Complete Results (All Configurations)</h2>
  <table>
    <tr><th>Config</th><th class="n">Profit</th><th class="n">Weekend</th><th class="n">Per-hr</th><th class="n">Per-day</th><th class="n">Per-km</th></tr>
    {''.join(all_rows)}
  </table>
</section>

<section>
  <h2>Methodology</h2>
  <p>Bayesian Optimization uses a Gaussian Process surrogate model to efficiently explore a 10-dimensional continuous/integer parameter space. Each "call" evaluates a candidate configuration by running {meta["seeds_per_eval"]} independent full-year simulations (365 days, ~2,000 customer twins, 81 vehicles, 35 stations) and averaging the net profit.</p>
  <p>The objective function is negated mean profit (gp_minimize minimizes). The Expected Improvement acquisition function balances exploration (uncertain regions) and exploitation (regions near the current best).</p>
  <p>{meta["n_random_starts"]} random initialization points seed the surrogate before model-guided acquisition begins. This ensures global coverage before local refinement.</p>
  <div class="hb"><strong>Determinism note:</strong> Auxiliary parameters (DOW multipliers, hourly multipliers, segment multipliers, station overrides) are derived deterministically from a hash of the core parameter vector. This ensures the same vector always produces the exact same JointState, removing stochastic noise from the BO objective.</div>
</section>

<footer>
  <p>Agent Revenue Simulator v1.0 - Proprietary - Generated {now}</p>
  <p>Technical report for simulation developer. Contains configuration details and optimization diagnostics.</p>
</footer>
</div></body></html>"""

    Path(out_html_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_html_path, "w") as f:
        f.write(report)
    print(f"Report written: {out_html_path}")
    print(f"Size: {len(report)} chars ({len(report)/1024:.0f} KB)")

if __name__ == "__main__":
    import sys
    build_bo_technical_report(
        sys.argv[1] if len(sys.argv) > 1 else "/opt/data/agent-revenue-simulator-reports/data/bo_results.json",
        sys.argv[2] if len(sys.argv) > 2 else "/opt/data/agent-revenue-simulator-reports/reports/technical_bo_run_report.html",
    )
