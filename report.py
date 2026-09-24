from pathlib import Path
from datetime import datetime
import pandas as pd


def build_report(df):
    generated_at = datetime.now().isoformat(timespec="seconds")

    if df.empty:
        return {
            "generated_at": generated_at,
            "total": 0,
            "helmet": 0,
            "no_helmet": 0,
            "compliance_rate": 0.0,
            "total_fine": 0.0
        }

    # Make sure required columns exist
    required_columns = ["violation", "fine_amount"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(
                f"Missing column '{col}'. "
                f"Available columns: {list(df.columns)}"
            )

    no_helmet = int(
        df["violation"]
        .astype(str)
        .str.upper()
        .eq("NO_HELMET")
        .sum()
    )

    total = len(df)
    helmet = max(total - no_helmet, 0)

    fine = float(
        pd.to_numeric(
            df["fine_amount"],
            errors="coerce"
        )
        .fillna(0)
        .sum()
    )

    return {
        "generated_at": generated_at,
        "total": total,
        "helmet": helmet,
        "no_helmet": no_helmet,
        "compliance_rate": round(100 * helmet / total, 2),
        "total_fine": fine,
    }


def export_csv(df, output="reports/challans_export.csv"):
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(p, index=False)

    print(f"CSV created: {p}")

    return p


def export_html(df, output="reports/traffic_summary.html"):
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)

    s = build_report(df)

    table = (
        df.to_html(index=False)
        if not df.empty
        else "<p>No records.</p>"
    )

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">

<title>Traffic Safety Report</title>

<style>
body {{
    font-family: Arial;
    margin: 30px;
}}

.card {{
    display: inline-block;
    padding: 15px;
    margin: 5px;
    border: 1px solid #ddd;
}}

table {{
    border-collapse: collapse;
    width: 100%;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 8px;
}}

th {{
    background: #f2f2f2;
}}
</style>

</head>

<body>

<h1>AI Traffic Safety Report</h1>

<div class="card">
Total: {s["total"]}
</div>

<div class="card">
No Helmet: {s["no_helmet"]}
</div>

<div class="card">
Helmet: {s["helmet"]}
</div>

<div class="card">
Compliance: {s["compliance_rate"]}%
</div>

<div class="card">
Fine: Rs.{s["total_fine"]:.2f}
</div>

<h2>Records</h2>

{table}

</body>
</html>
"""

    p.write_text(html, encoding="utf-8")

    print(f"HTML report created: {p}")

    return p