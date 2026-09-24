import streamlit as st
import pandas as pd
import plotly.express as px
from db import fetch_all, fetch_one
from report import export_csv, export_html

st.set_page_config(page_title="AI Traffic E-Challan", page_icon="🚦", layout="wide")
st.title("🚦 No Helmet — No Green Light")
st.subheader("AI Traffic Enforcement Dashboard")
try:
    s = fetch_one("SELECT COUNT(*) total_challans, COALESCE(SUM(fine_amount),0) total_fine, COUNT(*) FILTER(WHERE signal_status='RED') red_violations FROM challans")
    df = pd.DataFrame(fetch_all("SELECT id,challan_no,created_at,video_name,vehicle_number,violation,fine_amount,signal_status,confidence,message_status,payment_status FROM challans ORDER BY created_at DESC LIMIT 5000") or [])
    if df.empty:
        st.info("No challans found yet.")
        st.stop()
    no_helmet = df["violation"].astype(str).str.upper().eq("NO_HELMET").sum()
    total = len(df)
    compliance = max(0.0, 100 * (1 - no_helmet / total)) if total else 0.0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Challans", int(s["total_challans"]))
    c2.metric("Total Fine", f"₹{float(s['total_fine']):,.0f}")
    c3.metric("RED Violations", int(s["red_violations"]))
    c4.metric("Compliance Rate", f"{compliance:.1f}%")
    st.header("📋 E-Challan Records")
    st.dataframe(df, use_container_width=True, hide_index=True)
    a,b = st.columns(2)
    with a:
        vc=df.groupby("video_name").size().reset_index(name="challans")
        st.plotly_chart(px.bar(vc,x="video_name",y="challans",title="Challans per Video"),use_container_width=True)
    with b:
        df["created_at"]=pd.to_datetime(df["created_at"])
        daily=df.assign(date=df["created_at"].dt.date).groupby("date").agg(fine=("fine_amount","sum"),challans=("id","count")).reset_index()
        st.plotly_chart(px.line(daily,x="date",y="fine",markers=True,title="Fine Trend"),use_container_width=True)
    st.header("📈 Compliance Over Time")
    cd=df.assign(date=df["created_at"].dt.date).groupby("date").agg(total=("id","count"),no_helmet=("violation",lambda x:x.astype(str).str.upper().eq("NO_HELMET").sum())).reset_index()
    cd["compliance_rate"]=100*(1-cd["no_helmet"]/cd["total"])
    st.plotly_chart(px.line(cd,x="date",y="compliance_rate",markers=True,title="Daily Compliance Rate (%)"),use_container_width=True)
    st.header("🔎 Vehicle Search")
    q=st.text_input("Vehicle number")
    if q:
        r=df[df["vehicle_number"].fillna("").str.contains(q,case=False,regex=False)]
        if r.empty: st.warning("No record found.")
        else: st.dataframe(r,use_container_width=True,hide_index=True)
    st.header("📨 Message Status")
    mc=df.groupby("message_status").size().reset_index(name="count")
    st.plotly_chart(px.pie(mc,names="message_status",values="count",title="SMS Status"),use_container_width=True)
    st.header("📤 Reports & Export")
    if st.button("Generate CSV report"): st.success(f"Saved: {export_csv(df)}")
    if st.button("Generate HTML report"): st.success(f"Saved: {export_html(df)}")
except Exception as e:
    st.error("Database connection error")
    st.code(str(e))
