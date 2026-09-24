from pathlib import Path
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

load_dotenv()

app = FastAPI(title="No Helmet No Green Light")


# =========================================================
# DATABASE CONNECTION
# =========================================================
def get_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL")
    )


# =========================================================
# GET CHALLANS FROM POSTGRESQL
# =========================================================

def get_challans():

    conn = get_connection()

    try:

        query = """
            SELECT
                id,
                challan_no,
                created_at,
                video_name,
                frame_number,
                timestamp_seconds,
                vehicle_number,
                violation,
                fine_amount,
                signal_status,
                confidence,
                message_status,
                payment_status,
                notes
            FROM challans
            ORDER BY created_at DESC
        """

        df = pd.read_sql_query(
            query,
            conn
        )

        return df

    finally:

        conn.close()


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/", response_class=HTMLResponse)
def dashboard():

    try:

        df = get_challans()

    except Exception as e:

        return HTMLResponse(
            f"""
            <h1>Database Connection Error</h1>
            <p>{e}</p>
            <p>
                Check your PostgreSQL credentials
                in the .env file.
            </p>
            """,
            status_code=500
        )

    # =====================================================
    # STATISTICS
    # =====================================================

    total_challans = len(df)

    no_helmet = 0

    if not df.empty:

        no_helmet = int(
            df["violation"]
            .astype(str)
            .str.upper()
            .eq("NO_HELMET")
            .sum()
        )

    total_fine = 0

    if not df.empty:

        total_fine = float(
            pd.to_numeric(
                df["fine_amount"],
                errors="coerce"
            )
            .fillna(0)
            .sum()
        )

    red_count = 0

    if not df.empty:

        red_count = int(
            df["signal_status"]
            .astype(str)
            .str.upper()
            .eq("RED")
            .sum()
        )

    # =====================================================
    # TABLE
    # =====================================================

    if not df.empty:

        display_df = df.copy()

        # Make timestamp readable
        if "created_at" in display_df.columns:

            display_df["created_at"] = (
                display_df["created_at"]
                .astype(str)
            )

        table = display_df.to_html(
            index=False,
            classes="data-table",
            border=0
        )

    else:

        table = """
        <div class="empty">
            No challans generated yet.
        </div>
        """

    # =====================================================
    # HTML PAGE
    # =====================================================

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>No Helmet No Green Light</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    margin: 0;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background: #f4f6f8;

    color: #222;
}}


.header {{

    background: #111827;

    color: white;

    padding: 25px 40px;

}}

.header h1 {{

    margin: 0;

    font-size: 30px;

}}

.header p {{

    margin: 8px 0 0;

    color: #d1d5db;

}}


.container {{

    max-width: 1400px;

    margin: auto;

    padding: 35px;

}}


.cards {{

    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(200px, 1fr)
        );

    gap: 20px;

    margin-bottom: 35px;

}}


.card {{

    background: white;

    padding: 25px;

    border-radius: 12px;

    box-shadow:
        0 2px 8px rgba(
            0,
            0,
            0,
            0.08
        );

}}


.card h3 {{

    margin: 0 0 10px;

    color: #6b7280;

    font-size: 16px;

}}


.card .number {{

    font-size: 32px;

    font-weight: bold;

}}


.download-section {{

    background: white;

    padding: 25px;

    border-radius: 12px;

    margin-bottom: 30px;

    text-align: center;

}}


.download-btn {{

    display: inline-block;

    background: #2563eb;

    color: white;

    padding:
        14px 28px;

    border-radius: 8px;

    text-decoration: none;

    font-size: 17px;

    font-weight: bold;

}}


.download-btn:hover {{

    background: #1d4ed8;

}}


.refresh-btn {{

    display: inline-block;

    margin-left: 10px;

    background: #374151;

    color: white;

    padding:
        14px 28px;

    border-radius: 8px;

    text-decoration: none;

    font-size: 17px;

}}


.table-container {{

    background: white;

    padding: 25px;

    border-radius: 12px;

    overflow-x: auto;

}}


.data-table {{

    width: 100%;

    border-collapse: collapse;

    font-size: 14px;

}}


.data-table th {{

    background: #111827;

    color: white;

    padding: 12px;

    text-align: left;

    white-space: nowrap;

}}


.data-table td {{

    padding: 10px;

    border-bottom:
        1px solid #e5e7eb;

    white-space: nowrap;

}}


.data-table tr:hover {{

    background: #f9fafb;

}}


.empty {{

    text-align: center;

    padding: 40px;

    color: #6b7280;

}}


.footer {{

    text-align: center;

    color: #6b7280;

    padding: 30px;

}}

</style>

</head>


<body>


<div class="header">

    <h1>
        🚦 No Helmet No Green Light
    </h1>

    <p>
        AI Traffic Safety & E-Challan Dashboard
    </p>

</div>


<div class="container">


    <!-- STATISTICS -->

    <div class="cards">


        <div class="card">

            <h3>
                Total Challans
            </h3>

            <div class="number">
                {total_challans}
            </div>

        </div>


        <div class="card">

            <h3>
                No Helmet Violations
            </h3>

            <div class="number">
                {no_helmet}
            </div>

        </div>


        <div class="card">

            <h3>
                Red Signal Events
            </h3>

            <div class="number">
                {red_count}
            </div>

        </div>


        <div class="card">

            <h3>
                Total Fine
            </h3>

            <div class="number">
                ₹{total_fine:.2f}
            </div>

        </div>


    </div>


    <!-- DOWNLOAD -->

    <div class="download-section">

        <h2>
            Traffic Report
        </h2>

        <p>
            Download all challan records
            from PostgreSQL.
        </p>


        <a
            href="/download-report"
            class="download-btn"
        >
            📥 Download Report
        </a>


        <a
            href="/"
            class="refresh-btn"
        >
            🔄 Refresh
        </a>

    </div>


    <!-- CHALLAN TABLE -->

    <div class="table-container">

        <h2>
            Challan Records
        </h2>

        {table}

    </div>


</div>


<div class="footer">

    No Helmet No Green Light
    <br>

    Educational AI Prototype

</div>


</body>

</html>
"""

    return HTMLResponse(
        content=html
    )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@app.get("/download-report")
def download_report():

    try:
        df = get_challans()

        # Excel timezone-aware datetime ko support nahi karta
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.tz_localize(None)

        report_path = Path(
            "reports/challans_report.xlsx"
        )

        report_path.parent.mkdir(
            exist_ok=True
        )

        with pd.ExcelWriter(
            report_path,
            engine="openpyxl"
        ) as writer:

            df.to_excel(
                writer,
                index=False,
                sheet_name="Challans"
            )

        return FileResponse(
            path=report_path,
            filename="challans_report.xlsx",
            media_type=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )
        )

    except Exception as e:

        return {
            "error": str(e)
        }