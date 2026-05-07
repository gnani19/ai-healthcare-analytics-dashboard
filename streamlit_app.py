import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="AI Healthcare Analytics Dashboard", layout="wide")

st.title("AI-Powered Healthcare Analytics Dashboard")
st.write(
    "Analyze healthcare claims, denials, prior authorizations, provider performance, "
    "operational KPIs, and high-value claim anomalies."
)

DATA_PATH = Path("data/healthcare_claims_sample.csv")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["service_date"] = pd.to_datetime(df["service_date"])
    df["submitted_date"] = pd.to_datetime(df["submitted_date"])
    return df

def build_kpi_summary(df):
    total_claims = len(df)
    denied_claims = int((df["claim_status"] == "Denied").sum())
    approved_claims = int((df["claim_status"] == "Approved").sum())
    pending_claims = int((df["claim_status"] == "Pending").sum())

    denial_rate = round((denied_claims / total_claims) * 100, 2) if total_claims else 0
    total_claim_value = round(df["claim_amount"].sum(), 2)
    avg_claim_value = round(df["claim_amount"].mean(), 2) if total_claims else 0

    auth_df = df[df["prior_auth_required"] == "Yes"]
    avg_auth_days = round(auth_df["days_to_authorization"].mean(), 2) if len(auth_df) else 0

    return {
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "denied_claims": denied_claims,
        "pending_claims": pending_claims,
        "denial_rate_percent": denial_rate,
        "total_claim_value": total_claim_value,
        "average_claim_value": avg_claim_value,
        "average_authorization_days": avg_auth_days,
    }

def denial_trends(df):
    denied = df[df["claim_status"] == "Denied"]
    if denied.empty:
        return pd.DataFrame(columns=["denial_reason", "claim_count", "total_value"])

    return (
        denied.groupby("denial_reason")
        .agg(
            claim_count=("claim_id", "count"),
            total_value=("claim_amount", "sum"),
        )
        .reset_index()
        .sort_values("claim_count", ascending=False)
    )

def provider_performance(df):
    provider = (
        df.groupby("provider_name")
        .agg(
            total_claims=("claim_id", "count"),
            denied_claims=("claim_status", lambda x: (x == "Denied").sum()),
            avg_claim_amount=("claim_amount", "mean"),
            avg_auth_days=("days_to_authorization", "mean"),
        )
        .reset_index()
    )

    provider["denial_rate_percent"] = round(
        (provider["denied_claims"] / provider["total_claims"]) * 100, 2
    )
    provider["avg_claim_amount"] = round(provider["avg_claim_amount"], 2)
    provider["avg_auth_days"] = round(provider["avg_auth_days"], 2)

    return provider.sort_values("denial_rate_percent", ascending=False)

def detect_anomalies(df):
    if df.empty:
        return pd.DataFrame()

    threshold = df["claim_amount"].mean() + (2 * df["claim_amount"].std())
    anomalies = df[df["claim_amount"] > threshold].copy()
    anomalies["anomaly_reason"] = "Claim amount significantly higher than normal pattern"

    return anomalies[
        [
            "claim_id",
            "provider_name",
            "department",
            "payer_type",
            "claim_amount",
            "claim_status",
            "anomaly_reason",
        ]
    ]

def monthly_claim_summary(df):
    monthly = df.copy()
    monthly["month"] = monthly["service_date"].dt.to_period("M").astype(str)

    return (
        monthly.groupby("month")
        .agg(
            total_claims=("claim_id", "count"),
            denied_claims=("claim_status", lambda x: (x == "Denied").sum()),
        )
        .reset_index()
    )

def generate_ai_insights(kpis, top_denials, provider_summary):
    top_denial = (
        top_denials.iloc[0]["denial_reason"]
        if len(top_denials)
        else "No major denial reason"
    )

    top_provider = (
        provider_summary.iloc[0]["provider_name"]
        if len(provider_summary)
        else "N/A"
    )

    return f"""
The dashboard analyzed **{kpis['total_claims']:,} healthcare claims** with an overall denial rate of **{kpis['denial_rate_percent']}%**.

The most frequent denial reason is **{top_denial}**, which indicates an opportunity to improve documentation, coding, or prior authorization checks.

The provider with the highest denial risk is **{top_provider}**, based on provider-level denial rate comparison.

Average authorization turnaround time is **{kpis['average_authorization_days']} days**.

Recommended actions include strengthening pre-submission validation, reviewing denial trends weekly, and monitoring authorization delays by department.
"""

try:
    df = load_data()
except Exception:
    st.error("Dataset not found. Please make sure data/healthcare_claims_sample.csv exists in your GitHub repo.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    department = st.multiselect("Department", sorted(df["department"].unique()))
    payer = st.multiselect("Payer Type", sorted(df["payer_type"].unique()))
    status = st.multiselect("Claim Status", sorted(df["claim_status"].unique()))

filtered = df.copy()

if department:
    filtered = filtered[filtered["department"].isin(department)]

if payer:
    filtered = filtered[filtered["payer_type"].isin(payer)]

if status:
    filtered = filtered[filtered["claim_status"].isin(status)]

kpis = build_kpi_summary(filtered)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Claims", f"{kpis['total_claims']:,}")
col2.metric("Denied Claims", f"{kpis['denied_claims']:,}")
col3.metric("Denial Rate", f"{kpis['denial_rate_percent']}%")
col4.metric("Avg Auth Days", f"{kpis['average_authorization_days']}")

denials = denial_trends(filtered)
providers = provider_performance(filtered)
monthly = monthly_claim_summary(filtered)
anomalies = detect_anomalies(filtered)

st.subheader("AI-Generated Operational Summary")
st.info(generate_ai_insights(kpis, denials, providers))

st.subheader("Denial Reason Trends")
if len(denials):
    fig = px.bar(
        denials,
        x="denial_reason",
        y="claim_count",
        title="Denied Claims by Reason",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No denial records available for selected filters.")

st.subheader("Monthly Claim Volume")
fig2 = px.line(
    monthly,
    x="month",
    y=["total_claims", "denied_claims"],
    markers=True,
    title="Monthly Claims and Denials",
)
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Provider Performance")
st.dataframe(providers, use_container_width=True)

st.subheader("High-Value Claim Anomalies")
st.dataframe(anomalies, use_container_width=True)

st.subheader("Raw Claims Data")
st.dataframe(filtered.head(200), use_container_width=True)