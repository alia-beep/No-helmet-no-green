import pandas as pd

from report import build_report, export_csv, export_html


df = pd.DataFrame([
    {
        "vehicle_id": "MH12AB1234",
        "violation": "NO_HELMET",
        "fine_amount": 500
    },
    {
        "vehicle_id": "MH12CD5678",
        "violation": "HELMET",
        "fine_amount": 0
    },
    {
        "vehicle_id": "MH12EF9999",
        "violation": "NO_HELMET",
        "fine_amount": 500
    }
])


print("\nREPORT:")
print(build_report(df))

print("\nExporting...")

export_csv(df)
export_html(df)

print("\nDONE!")