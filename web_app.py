
from pathlib import Path
import os
import html
import traceback

import pandas as pd
import psycopg2
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

# Load .env from the project directory
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = FastAPI(title="No Helmet No Green Light")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Check your project's .env file."
        )

    return psycopg2.connect(database_url)


# =========================================================
# GET CHALLANS FROM POSTGRESQL
# =========================================================

def get_challans():
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

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [item[0] for item in cur.description]
            rows = cur.fetchall()

        return pd.DataFrame(rows, columns=columns)

    finally:
        conn.close()


# =========================================================
# INTERACTIVE DASHBOARD
# =========================================================

@app.get("/", response_class=HTMLResponse)
def dashboard():
    try:
        df = get_challans()

    except Exception as e:
        traceback.print_exc()

        # Escape database error before showing it in HTML
        error_message = html.escape(str(e))

        return HTMLResponse(
            f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport"
                      content="width=device-width, initial-scale=1">
                <title>Database Connection Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background: #f3f6fb;
                        padding: 30px;
                        color: #172033;
                    }}
                    .error {{
                        max-width: 800px;
                        margin: 40px auto;
                        background: white;
                        padding: 28px;
                        border-radius: 14px;
                        border-left: 5px solid #dc2626;
                        box-shadow: 0 5px 25px #0001;
                    }}
                    pre {{
                        white-space: pre-wrap;
                        overflow-wrap: anywhere;
                        background: #fff1f2;
                        padding: 15px;
                        border-radius: 8px;
                    }}
                    a {{ color: #4f46e5; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>⚠️ Database Connection Error</h2>
                    <p>Check the DATABASE_URL in your .env file,
                    PostgreSQL credentials, and database/table names.</p>
                    <h3>Error details</h3>
                    <pre>{error_message}</pre>
                    <a href="/">Try again</a>
                </div>
            </body>
            </html>
            """,
            status_code=500
        )

    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    total_challans = len(df)
    no_helmet = 0
    red_count = 0
    total_fine = 0.0

    if not df.empty:
        no_helmet = int(
            df["violation"]
            .astype(str)
            .str.upper()
            .eq("NO_HELMET")
            .sum()
        )

        red_count = int(
            df["signal_status"]
            .astype(str)
            .str.upper()
            .eq("RED")
            .sum()
        )

        total_fine = float(
            pd.to_numeric(
                df["fine_amount"], errors="coerce"
            ).fillna(0).sum()
        )

        # Make timestamps readable in the HTML table
        df = df.copy()
        df["created_at"] = df["created_at"].astype(str)

    # Escape database content before inserting it into HTML
    table = (
        df.to_html(
            index=False,
            classes="data-table",
            border=0,
            escape=True,
            table_id="challanTable"
        )
        if not df.empty
        else ""
    )

    # -----------------------------------------------------
    # HTML DASHBOARD
    # -----------------------------------------------------

    page = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>No Helmet No Green Light | Dashboard</title>

<style>
:root {
    --bg: #f3f6fb;
    --panel: #ffffff;
    --text: #172033;
    --muted: #778197;
    --border: #e7ebf2;
    --sidebar: #111827;
    --accent: #6366f1;
    --shadow: 0 8px 28px rgba(25,35,60,.06);
}

body.dark {
    --bg: #0b1120;
    --panel: #151e30;
    --text: #edf2ff;
    --muted: #a0acc2;
    --border: #29354a;
    --sidebar: #080d18;
    --accent: #818cf8;
    --shadow: 0 8px 28px rgba(0,0,0,.15);
}

* { box-sizing: border-box; }

body {
    margin: 0;
    font-family: "Segoe UI", Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    transition: background .25s, color .25s;
}

button, input, select { font: inherit; }

.layout { display: flex; min-height: 100vh; }

.sidebar {
    width: 245px;
    flex-shrink: 0;
    padding: 28px 18px;
    background: var(--sidebar);
    color: white;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 8px 25px;
    border-bottom: 1px solid #30394a;
}

.brand-icon {
    width: 43px;
    height: 43px;
    display: grid;
    place-items: center;
    border-radius: 13px;
    font-size: 23px;
    background: linear-gradient(135deg,#6366f1,#06b6d4);
}

.brand h2 { font-size: 14px; margin: 0; }
.brand p { font-size: 10px; color: #aeb8cb; margin: 5px 0 0; }

.nav-title {
    margin: 28px 10px 12px;
    color: #929db1;
    font-size: 11px;
    letter-spacing: 1.5px;
}

.nav-link {
    display: block;
    padding: 13px 14px;
    margin: 5px 0;
    color: #cbd5e1;
    text-decoration: none;
    border-radius: 10px;
    transition: .2s;
    font-size: 14px;
}

.nav-link:hover, .nav-link.active {
    background: #29334a;
    color: white;
}

.sidebar-note {
    margin-top: 50px;
    padding: 15px;
    background: #1d293d;
    border-radius: 12px;
    color: #cbd5e1;
    font-size: 12px;
    line-height: 1.7;
}

.main {
    flex: 1;
    min-width: 0;
    padding: 30px;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 28px;
}

.eyebrow {
    color: var(--accent);
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1.5px;
}

h1 { margin: 8px 0; font-size: clamp(23px,3vw,31px); }
.subtitle { color: var(--muted); font-size: 14px; }

.actions { display: flex; gap: 9px; flex-wrap: wrap; }

.btn {
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 11px 14px;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    background: var(--panel);
    color: var(--text);
    transition: transform .2s;
    font-size: 13px;
}

.btn:hover { transform: translateY(-2px); }

.btn-primary {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
}

.section-label {
    font-size: 12px;
    font-weight: 700;
    color: var(--muted);
    letter-spacing: 1.2px;
    margin: 26px 0 15px;
}

.cards {
    display: grid;
    grid-template-columns: repeat(4,minmax(0,1fr));
    gap: 17px;
}

.stat-card {
    background: var(--panel);
    padding: 22px;
    border: 1px solid var(--border);
    border-radius: 15px;
    box-shadow: var(--shadow);
    transition: transform .25s,border-color .25s;
    animation: rise .5s ease both;
}

.stat-card:hover {
    transform: translateY(-5px);
    border-color: var(--accent);
}

.stat-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}

.stat-title { color: var(--muted); font-size: 12px; }

.stat-icon {
    width: 42px;
    height: 42px;
    display: grid;
    place-items: center;
    border-radius: 12px;
    font-size: 21px;
}

.purple { background: #eeedff; }
.orange { background: #fff0df; }
.red { background: #ffe6e9; }
.green { background: #ddf8ec; }

.stat-number {
    font-size: clamp(23px,2.4vw,32px);
    font-weight: 750;
    margin-top: 19px;
    overflow-wrap: anywhere;
}

.stat-foot { color: var(--muted); font-size: 11px; margin-top: 8px; }

.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 15px;
    box-shadow: var(--shadow);
    padding: 22px;
    margin-top: 24px;
}

.panel-heading {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.panel-heading h2 { margin: 0; font-size: 18px; }
.panel-heading p { margin: 6px 0 0; font-size: 12px; color: var(--muted); }

.toolbar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 17px;
}

.control {
    background: var(--bg);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 11px 12px;
    outline: none;
    min-width: 150px;
}

.control:focus { border-color: var(--accent); }
.search { flex: 1; min-width: 200px; }

.table-wrap {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 10px;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    white-space: nowrap;
}

.data-table th {
    background: var(--sidebar);
    color: white;
    padding: 15px 13px;
    text-align: left;
    cursor: pointer;
}

.data-table th:hover { background: #303b53; }

.data-table td {
    padding: 13px;
    border-bottom: 1px solid var(--border);
}

.data-table tbody tr:hover { background: var(--bg); }

.empty {
    padding: 38px 12px;
    text-align: center;
    color: var(--muted);
}

.status {
    display: inline-block;
    border-radius: 20px;
    padding: 5px 9px;
    font-size: 11px;
    font-weight: 650;
}

.status-paid { background: #dcfce7; color: #166534; }
.status-unpaid { background: #fee2e2; color: #991b1b; }
.status-other { background: #e0e7ff; color: #3730a3; }

.table-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-top: 17px;
    font-size: 12px;
    color: var(--muted);
}

.pager { display: flex; gap: 8px; align-items: center; }
.pager button:disabled { opacity: .4; cursor: not-allowed; }

.footer {
    text-align: center;
    color: var(--muted);
    font-size: 11px;
    padding: 30px 0 5px;
}

@keyframes rise {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

@media(max-width:1050px) {
    .cards { grid-template-columns: repeat(2,minmax(0,1fr)); }
    .sidebar { width: 205px; }
}

@media(max-width:680px) {
    .layout { display: block; }
    .sidebar { width: 100%; padding: 15px; }
    .brand { padding-bottom: 14px; }
    .nav-title, .sidebar-note { display: none; }
    .nav-link { display: inline-block; padding: 9px 10px; font-size: 12px; }
    .main { padding: 18px 12px; }
    .cards { gap: 10px; }
    .stat-card { padding: 14px; }
    .stat-icon { width: 34px; height: 34px; }
    .panel { padding: 13px; }
    .toolbar { flex-direction: column; }
    .control, .search { width: 100%; min-width: 0; }
}
</style>
</head>

<body>
<div class="layout">

<aside class="sidebar">
    <div class="brand">
        <div class="brand-icon">🚦</div>
        <div>
            <h2>TRAFFIC SAFETY AI</h2>
            <p>NO HELMET NO GREEN LIGHT</p>
        </div>
    </div>

    <div class="nav-title">WORKSPACE</div>
    <a href="#overview" class="nav-link active">▦ &nbsp; Overview</a>
    <a href="#records" class="nav-link">▤ &nbsp; Challan Records</a>
    <a href="/download-report" class="nav-link">⇩ &nbsp; Export Report</a>
    <a href="/" class="nav-link">↻ &nbsp; Refresh Data</a>

    <div class="sidebar-note">
        <div style="font-size:20px">🛡️</div>
        <strong>Road Safety First</strong>
        <br>
        Educational AI prototype for traffic monitoring and simulated e-challans.
    </div>
</aside>

<main class="main" id="overview">
    <div class="topbar">
        <div>
            <div class="eyebrow">TRAFFIC MANAGEMENT SYSTEM</div>
            <h1>Dashboard Overview</h1>
            <div class="subtitle">Monitor violations, challans and fine records.</div>
        </div>

        <div class="actions">
            <button class="btn" id="themeToggle">🌙 Dark Mode</button>
            <a href="/" class="btn">↻ Refresh</a>
            <a href="/download-report" class="btn btn-primary">⬇ Download Excel</a>
        </div>
    </div>

    <div class="section-label">KEY PERFORMANCE INDICATORS</div>

    <div class="cards">
        <div class="stat-card">
            <div class="stat-top">
                <span class="stat-title">TOTAL CHALLANS</span>
                <span class="stat-icon purple">📋</span>
            </div>
            <div class="stat-number">__TOTAL__</div>
            <div class="stat-foot">All recorded challans</div>
        </div>

        <div class="stat-card" style="animation-delay:.08s">
            <div class="stat-top">
                <span class="stat-title">NO HELMET</span>
                <span class="stat-icon orange">🪖</span>
            </div>
            <div class="stat-number">__HELMET__</div>
            <div class="stat-foot">Helmet violation records</div>
        </div>

        <div class="stat-card" style="animation-delay:.16s">
            <div class="stat-top">
                <span class="stat-title">RED SIGNAL EVENTS</span>
                <span class="stat-icon red">🚨</span>
            </div>
            <div class="stat-number">__RED__</div>
            <div class="stat-foot">Records marked RED</div>
        </div>

        <div class="stat-card" style="animation-delay:.24s">
            <div class="stat-top">
                <span class="stat-title">TOTAL FINE</span>
                <span class="stat-icon green">₹</span>
            </div>
            <div class="stat-number">₹__FINE__</div>
            <div class="stat-foot">Total recorded fine amount</div>
        </div>
    </div>

    <section class="panel" id="records">
        <div class="panel-heading">
            <div>
                <h2>Challan Records</h2>
                <p>Search, filter, sort and browse your records.</p>
            </div>
            <span class="status status-other">● Database Records</span>
        </div>

        <div class="toolbar">
            <input id="searchInput" class="control search"
                   placeholder="🔍 Search vehicle, challan, violation..."
                   aria-label="Search challans">

            <select id="violationFilter" class="control" aria-label="Filter violation">
                <option value="">All Violations</option>
            </select>

            <select id="paymentFilter" class="control" aria-label="Filter payment">
                <option value="">All Payment Statuses</option>
            </select>

            <select id="pageSize" class="control" aria-label="Rows per page">
                <option value="10">10 rows</option>
                <option value="25">25 rows</option>
                <option value="50">50 rows</option>
                <option value="100">100 rows</option>
            </select>
        </div>

        <div id="tableArea" class="table-wrap">
            __TABLE__
        </div>

        <div class="table-footer">
            <span id="resultCount">Loading records...</span>
            <div class="pager">
                <button id="prevPage" class="btn">← Previous</button>
                <span id="pageInfo">Page 1</span>
                <button id="nextPage" class="btn">Next →</button>
            </div>
        </div>
    </section>

    <div class="footer">
        No Helmet No Green Light · AI Traffic Safety Dashboard · Educational Prototype
    </div>
</main>
</div>

<script>
const table = document.getElementById("challanTable");
const searchInput = document.getElementById("searchInput");
const violationFilter = document.getElementById("violationFilter");
const paymentFilter = document.getElementById("paymentFilter");
const pageSizeSelect = document.getElementById("pageSize");
const tableArea = document.getElementById("tableArea");

let allRows = [];
let filteredRows = [];
let currentPage = 1;
let sortColumn = -1;
let sortDirection = 1;
let body = null;
let headers = [];

if (table) {
    headers = [...table.querySelectorAll("thead th")];
    body = table.querySelector("tbody");

    allRows = [...body.querySelectorAll("tr")].map(row => ({
        element: row,
        cells: [...row.cells].map(cell => cell.textContent.trim())
    }));

    const violationIndex = headers.findIndex(
        h => h.textContent.trim().toLowerCase() === "violation"
    );

    const paymentIndex = headers.findIndex(
        h => h.textContent.trim().toLowerCase() === "payment_status"
    );

    function populateFilter(select, index) {
        if (index < 0) return;

        const values = [...new Set(
            allRows.map(row => row.cells[index]).filter(Boolean)
        )].sort();

        values.forEach(value => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            select.appendChild(option);
        });
    }

    populateFilter(violationFilter, violationIndex);
    populateFilter(paymentFilter, paymentIndex);

    headers.forEach((header, index) => {
        header.title = "Click to sort";

        header.addEventListener("click", () => {
            if (sortColumn === index) {
                sortDirection *= -1;
            } else {
                sortColumn = index;
                sortDirection = 1;
            }

            headers.forEach(h => {
                h.textContent = h.textContent.replace(/ [▲▼]$/, "");
            });

            header.textContent += sortDirection === 1 ? " ▲" : " ▼";

            currentPage = 1;
            renderTable();
        });
    });

    function renderTable() {
        const query = searchInput.value.trim().toLowerCase();
        const violation = violationFilter.value.toLowerCase();
        const payment = paymentFilter.value.toLowerCase();

        filteredRows = allRows.filter(row => {
            const matchesSearch = row.cells.some(value =>
                value.toLowerCase().includes(query)
            );

            const matchesViolation =
                violationIndex < 0 || !violation ||
                row.cells[violationIndex].toLowerCase() === violation;

            const matchesPayment =
                paymentIndex < 0 || !payment ||
                row.cells[paymentIndex].toLowerCase() === payment;

            return matchesSearch && matchesViolation && matchesPayment;
        });

        if (sortColumn >= 0) {
            filteredRows.sort((a, b) => {
                const x = a.cells[sortColumn];
                const y = b.cells[sortColumn];
                const nx = Number(x);
                const ny = Number(y);

                if (x !== "" && y !== "" &&
                    Number.isFinite(nx) && Number.isFinite(ny)) {
                    return (nx - ny) * sortDirection;
                }

                return x.localeCompare(y, undefined, {
                    numeric: true,
                    sensitivity: "base"
                }) * sortDirection;
            });
        }

        const pageSize = Number(pageSizeSelect.value);
        const totalPages = Math.max(
            1, Math.ceil(filteredRows.length / pageSize)
        );

        currentPage = Math.min(currentPage, totalPages);

        const start = (currentPage - 1) * pageSize;
        const pageRows = filteredRows.slice(start, start + pageSize);

        if (body) {
            pageRows.forEach(row => body.appendChild(row.element));

            allRows.forEach(row => {
                if (!pageRows.includes(row)) row.element.remove();
            });
        }

        let empty = document.getElementById("emptyMessage");

        if (pageRows.length === 0) {
            if (table) table.style.display = "none";

            if (!empty) {
                empty = document.createElement("div");
                empty.id = "emptyMessage";
                empty.className = "empty";
                tableArea.appendChild(empty);
            }

            empty.textContent = allRows.length
                ? "No matching records. Try changing your search or filters."
                : "No challans generated yet.";
        } else {
            if (table) table.style.display = "table";
            if (empty) empty.remove();
        }

        document.getElementById("resultCount").textContent =
            `Showing ${filteredRows.length ? start + 1 : 0}–` +
            `${Math.min(start + pageSize, filteredRows.length)} of ` +
            `${filteredRows.length} matching records`;

        document.getElementById("pageInfo").textContent =
            `Page ${currentPage} of ${totalPages}`;

        document.getElementById("prevPage").disabled = currentPage <= 1;
        document.getElementById("nextPage").disabled =
            currentPage >= totalPages;
    }

    searchInput.addEventListener("input", () => {
        currentPage = 1;
        renderTable();
    });

    violationFilter.addEventListener("change", () => {
        currentPage = 1;
        renderTable();
    });

    paymentFilter.addEventListener("change", () => {
        currentPage = 1;
        renderTable();
    });

    pageSizeSelect.addEventListener("change", () => {
        currentPage = 1;
        renderTable();
    });

    document.getElementById("prevPage").addEventListener("click", () => {
        if (currentPage > 1) currentPage--;
        renderTable();
    });

    document.getElementById("nextPage").addEventListener("click", () => {
        const pages = Math.max(
            1, Math.ceil(filteredRows.length / Number(pageSizeSelect.value))
        );

        if (currentPage < pages) currentPage++;
        renderTable();
    });

    renderTable();
} else {
    tableArea.innerHTML =
        '<div class="empty">No challans generated yet.</div>';

    document.getElementById("resultCount").textContent = "0 records";
    document.getElementById("pageInfo").textContent = "Page 1 of 1";
    document.getElementById("prevPage").disabled = true;
    document.getElementById("nextPage").disabled = true;
}

// Dark/light mode toggle
const themeToggle = document.getElementById("themeToggle");

themeToggle.addEventListener("click", () => {
    document.body.classList.toggle("dark");

    const isDark = document.body.classList.contains("dark");
    themeToggle.textContent = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
    themeToggle.setAttribute("aria-pressed", String(isDark));
});

// Active navigation
document.querySelectorAll(".nav-link[href^='#']").forEach(link => {
    link.addEventListener("click", () => {
        document.querySelectorAll(".nav-link").forEach(item =>
            item.classList.remove("active")
        );
        link.classList.add("active");
    });
});
</script>
</body>
</html>
"""

    replacements = {
        "__TOTAL__": f"{total_challans:,}",
        "__HELMET__": f"{no_helmet:,}",
        "__RED__": f"{red_count:,}",
        "__FINE__": f"{total_fine:,.2f}",
        "__TABLE__": table,
    }

    for key, value in replacements.items():
        page = page.replace(key, value)

    return HTMLResponse(content=page)


# =========================================================
# DOWNLOAD EXCEL REPORT
# =========================================================

@app.get("/download-report")
def download_report():
    try:
        df = get_challans()

        # Excel does not support timezone-aware datetimes.
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                if df[col].dt.tz is not None:
                    df[col] = df[col].dt.tz_localize(None)

        report_path = BASE_DIR / "reports" / "challans_report.xlsx"
        report_path.parent.mkdir(parents=True, exist_ok=True)

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
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

    except Exception:
        traceback.print_exc()

        return HTMLResponse(
            "<h2>Report generation failed.</h2>"
            "<p>Check the terminal for the full error.</p>",
            status_code=500
        )
