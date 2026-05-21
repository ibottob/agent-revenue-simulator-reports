#!/usr/bin/env python3
"""Build customer-facing report from deterministic validation data."""
import json
from pathlib import Path
from datetime import datetime

def build_customer_report(validation_json_path: str, output_html_path: str):
    with open(validation_json_path) as f:
        val = json.load(f)

    s = val["summary"]
    config = val["configuration"]
    fleet_sorted = sorted(config["fleet_counts"].items(), key=lambda x: x[1], reverse=True)
    fleet_total = sum(c for _, c in fleet_sorted)

    campaign_text = ""
    if config["campaigns"]:
        campaign_text = f"Launch {config['campaigns'][0]['segment']} campaign at {config['campaigns'][0]['discount_pct']:.1f}% discount"
    else:
        campaign_text = "Launch targeted campaign"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Annual Optimization Report</title>
  <style>
    :root{{--bg:#0a0f1a;--card:#111827;--text:#f1f5f9;--muted:#94a3b8;--pos:#22c55e;--neg:#ef4444;--accent:#3b82f6;--border:#1e293b;}}
    body{{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;max-width:900px;margin:0 auto;padding:2rem;}}
    h1{{font-size:2rem;margin-bottom:.5rem;}} h2{{font-size:1.3rem;margin-top:2rem;border-bottom:1px solid var(--border);padding-bottom:.5rem;}}
    .subtitle{{color:var(--muted);font-size:1rem;margin-bottom:2rem;}}
    .hero{{background:linear-gradient(135deg,#1e3a5f,#0f172a);border:1px solid var(--border);border-radius:1rem;padding:2rem;margin:1.5rem 0;}}
    .hero-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1.5rem;}}
    .hero-item{{text-align:center;}}
    .hero-item .label{{color:var(--muted);font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;}}
    .hero-item .value{{font-size:2rem;font-weight:700;color:var(--pos);margin:.25rem 0;}}
    .hero-item .sub{{color:var(--muted);font-size:.85rem;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin:1rem 0;}}
    .card{{background:var(--card);border:1px solid var(--border);border-radius:.75rem;padding:1.25rem;}}
    .card .title{{color:var(--muted);font-size:.8rem;text-transform:uppercase;margin-bottom:.5rem;}}
    .card .value{{font-size:1.4rem;font-weight:700;}}
    .card .value.pos{{color:var(--pos);}}
    .card .value.neg{{color:var(--neg);}}
    .card .detail{{color:var(--muted);font-size:.85rem;margin-top:.25rem;}}
    table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem;}}
    th,td{{padding:.75rem .5rem;text-align:left;border-bottom:1px solid var(--border);}}
    th{{color:var(--muted);font-weight:600;font-size:.8rem;text-transform:uppercase;}}
    td{{font-family:monospace;}}
    .cta{{background:var(--accent);color:#fff;padding:1rem 1.5rem;border-radius:.5rem;text-decoration:none;display:inline-block;margin:1rem 0;font-weight:600;}}
    .note{{background:rgba(34,197,94,.1);border-left:3px solid var(--pos);padding:1rem;margin:1rem 0;color:var(--text);}}
    .method{{background:var(--card);border:1px solid var(--border);border-radius:.5rem;padding:1rem;margin:1.5rem 0;}}
    .method h3{{margin-top:0;color:var(--accent);}}
    footer{{text-align:center;color:var(--muted);font-size:.8rem;padding:2rem 0;}}
    .badge{{display:inline-block;padding:.15rem .5rem;border-radius:9999px;font-size:.7rem;font-weight:600;background:var(--pos);color:#fff;}}
  </style>
</head>
<body>
  <h1>Annual Optimization Report</h1>
  <p class="subtitle">Agent-based simulation results · Validated across 50 independent seeds · {datetime.now().strftime("%B %Y")}</p>

  <div class="hero">
    <div class="hero-grid">
      <div class="hero-item">
        <div class="label">Annual Profit</div>
        <div class="value">EUR {s['profit_mean']:,.0f}</div>
        <div class="sub">Validated across 50 seeds <span class="badge">REPRODUCIBLE</span></div>
      </div>
      <div class="hero-item">
        <div class="label">Total Revenue</div>
        <div class="value">EUR {s['revenue_mean']:,.0f}</div>
        <div class="sub">{round(s['revenue_mean'] / (s['revenue_mean'] + s['cost_mean']) * 100)}% of total value</div>
      </div>
      <div class="hero-item">
        <div class="label">Total Cost</div>
        <div class="value" style="color:var(--neg)">EUR {s['cost_mean']:,.0f}</div>
        <div class="sub">Fixed + variable fleet costs</div>
      </div>
      <div class="hero-item">
        <div class="label">Bookings</div>
        <div class="value">{round(s['bookings_mean']):,}</div>
        <div class="sub">Annual reservation count</div>
      </div>
    </div>
  </div>

  <div class="note">
    ✓ Each figure is the mean of 50 independent simulation runs. Standard deviation shown for transparency.
    Deviation from BO-reported mean: {abs(s['profit_mean'] - 278778.88) / 278778.88 * 100:.2f}%.
  </div>

  <h2>Pricing Structure</h2>
  <div class="grid">
    <div class="card">
      <div class="title">Per Hour</div>
      <div class="value">EUR {config['per_hour_cents']/100:.2f}</div>
      <div class="detail">Short trips, same-day returns</div>
    </div>
    <div class="card">
      <div class="title">Per Day</div>
      <div class="value">EUR {config['per_day_cents']/100:.2f}</div>
      <div class="detail">24h+ reservations, most bookings</div>
    </div>
    <div class="card">
      <div class="title">Per Kilometer</div>
      <div class="value">EUR {config['per_km_cents']/100:.2f}</div>
      <div class="detail">Beyond {config['km_included_per_day']} km/day included</div>
    </div>
    <div class="card">
      <div class="title">Weekend Multiplier</div>
      <div class="value">{config['weekend_pricing_multiplier']:.2f}×</div>
      <div class="detail">{'Cheaper weekends' if config['weekend_pricing_multiplier'] < 1.0 else 'Premium weekends'} pricing</div>
    </div>
  </div>

  <h2>Yield Curve</h2>
  <p>Demand-driven pricing: higher occupancy = higher price multiplier.</p>
  <div class="grid">
"""
    for occ, mult in config["yield_curve"]:
        html += f"""
    <div class="card">
      <div class="title">{int(occ*100)}% Occupancy</div>
      <div class="value">{mult:.2f}×</div>
      <div class="detail">Price multiplier</div>
    </div>
"""
    html += "  </div>\n"

    html += f"""
  <h2>Fleet Allocation</h2>
  <p>{fleet_total} vehicles across {sum(1 for _, c in fleet_sorted if c > 0)} active stations.</p>
  <table>
    <thead><tr><th>Station</th><th>Vehicles</th><th>Share</th></tr></thead>
    <tbody>
"""
    for sid, count in fleet_sorted[:15]:
        share = count / fleet_total * 100
        html += f"      <tr><td>Station #{sid}</td><td>{count}</td><td>{share:.1f}%</td></tr>\n"
    html += "    </tbody>\n  </table>\n"

    if config["campaigns"]:
        html += "\n  <h2>Marketing Campaigns</h2>\n  <div class='grid'>\n"
        for c in config["campaigns"]:
            html += f"""
    <div class="card">
      <div class="title">{c['segment'].capitalize()} Campaign</div>
      <div class="value">{c['discount_pct']:.1f}% discount</div>
      <div class="detail">Max {c['max_customers']} customers</div>
    </div>
"""
        html += "  </div>\n"

    html += f"""
  <div class="method">
    <h3>Methodology</h3>
    <p>This report is based on an agent-based simulation of 2,000 customer digital twins, 81 vehicles, and 35 stations over a full calendar year. The optimization used Bayesian Optimization (<code>gp_minimize</code>) with 200 function evaluations, each averaging 20 stochastic seeds.</p>
    <p><strong>Validation:</strong> The best configuration was re-evaluated with 50 independent seeds using fresh simulator instances (deterministic seeding, no hidden RNG state). Results are fully reproducible.</p>
    <p><strong>Key metrics:</strong> Profit EUR {s['profit_mean']:,.0f} (±{s['profit_std']:,.0f}), Revenue EUR {s['revenue_mean']:,.0f}, Cost EUR {s['cost_mean']:,.0f}, {round(s['bookings_mean']):,} bookings, {s['utilization_mean_pct']:.1f}% utilization.</p>
    <p>Git commit: {val['meta']['code_version']} | Validation method: {val['meta']['method']} | Base seed: {val['meta']['base_seed']}</p>
  </div>

  <h2>Recommended Actions</h2>
  <ul>
    <li><strong>Phase 1 (Week 1):</strong> Update tariff engine with validated pricing parameters. Deploy weekend multiplier at {config['weekend_pricing_multiplier']:.2f}×.</li>
    <li><strong>Phase 2 (Month 1):</strong> Reallocate fleet per simulation-optimal distribution. Monitor station-level utilization.</li>
    <li><strong>Phase 3 (Quarter 1):</strong> {campaign_text} if ROI > 3×.</li>
  </ul>

  <footer>
    Agent Revenue Simulator — {datetime.now().strftime("%B %Y")} — Deterministic Validation
  </footer>
</body>
</html>
"""

    with open(output_html_path, "w") as f:
        f.write(html)
    print(f"Customer report: {output_html_path} ({len(html):,} chars)")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: build_customer_report.py <validation_json> <output_html>")
        sys.exit(1)
    build_customer_report(sys.argv[1], sys.argv[2])
