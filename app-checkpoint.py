"""
Complaint Sentiment & Urgency Triage System - Streamlit App
--------------------------------------------------------------
1. Get complaint narratives from a local CSV file (e.g., your Kaggle CFPB
   complaints dataset) - fast and reliable, no network call needed.
2. Send each narrative to Azure AI Language (free F0 tier) for
   sentiment and key phrases.
3. Apply simple keyword-based rules to assign a category and an
   urgency flag (no model training involved).

Run with:  streamlit run app.py

SETUP: put your Kaggle "complaints.csv" file in this same folder. If your
file has a different name, change CSV_FILE below to match it.
"""

import requests
import pandas as pd
import streamlit as st
import os

CSV_FILE = r"C:\Users\miran\Azure Project\docs\complaints.csv"

URGENT_WORDS = ["fraud", "unauthorized", "stolen", "scam", "identity theft"]

CATEGORY_KEYWORDS = [
    ("Fraud", ["fraud", "unauthorized", "stolen", "scam", "identity theft"]),
    ("Credit Reporting", ["credit report", "credit score", "credit bureau"]),
    ("Customer Service", ["rude", "no response", "hung up", "on hold"]),
    ("Billing", ["charge", "fee", "billing", "payment"]),
]

PRODUCT_COL_CANDIDATES = ["Product", "product"]
NARRATIVE_COL_CANDIDATES = [
    "Consumer complaint narrative",
    "consumer_complaint_narrative",
    "Consumer_complaint_narrative",
]


def detect_columns(csv_file):
    header = pd.read_csv(csv_file, nrows=0).columns.tolist()
    product_col = next((c for c in PRODUCT_COL_CANDIDATES if c in header), None)
    narrative_col = next((c for c in NARRATIVE_COL_CANDIDATES if c in header), None)
    if product_col is None or narrative_col is None:
        raise ValueError(
            f"Could not find product/narrative columns in {csv_file}. "
            f"Columns found: {header}. Update PRODUCT_COL_CANDIDATES / "
            f"NARRATIVE_COL_CANDIDATES at the top of app.py to match."
        )
    return product_col, narrative_col


@st.cache_data(show_spinner=False)
def get_available_products(csv_file):
    product_col, _ = detect_columns(csv_file)
    products = pd.read_csv(csv_file, usecols=[product_col])[product_col].dropna().unique()
    return sorted(products.tolist())


@st.cache_data(show_spinner=False)
def fetch_complaints(product, size):
    product_col, narrative_col = detect_columns(CSV_FILE)
    narratives = []
    for chunk in pd.read_csv(CSV_FILE, usecols=[product_col, narrative_col],
                              chunksize=20_000, low_memory=False):
        matches = chunk[(chunk[product_col] == product) & (chunk[narrative_col].notna())]
        narratives.extend(matches[narrative_col].tolist())
        if len(narratives) >= size:
            break
    return narratives[:size]


def analyze_sentiment(narrative, endpoint, key, mock_mode):
    if mock_mode:
        return "mock-sentiment", {"mock": 0.0}
    url = f"{endpoint}/language/:analyze-text?api-version=2023-04-01"
    headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}
    body = {"kind": "SentimentAnalysis", "analysisInput": {"documents": [{"id": "1", "text": narrative}]}}
    result = requests.post(url, headers=headers, json=body).json()
    doc = result["results"]["documents"][0]
    return doc["sentiment"], doc["confidenceScores"]


def extract_key_phrases(narrative, endpoint, key, mock_mode):
    if mock_mode:
        return ["mock-mode - no real analysis"]
    url = f"{endpoint}/language/:analyze-text?api-version=2023-04-01"
    headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/json"}
    body = {"kind": "KeyPhraseExtraction", "analysisInput": {"documents": [{"id": "1", "text": narrative}]}}
    result = requests.post(url, headers=headers, json=body).json()
    return result["results"]["documents"][0]["keyPhrases"]


def assign_category(narrative):
    text = narrative.lower()
    for category, keywords in CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return category
    return "Other"


def is_urgent(narrative, sentiment):
    text = narrative.lower()
    urgent_word_hits = sum(1 for word in URGENT_WORDS if word in text)
    return sentiment == "negative" and urgent_word_hits >= 2


st.set_page_config(page_title="Complaint Sentiment & Urgency Triage", layout="wide")
st.title("Complaint Sentiment & Urgency Triage System")
st.caption("Local CFPB dataset (CSV) + Azure AI Language (F0 free tier) + simple rule-based routing")

if not os.path.exists(CSV_FILE):
    st.error(f"Couldn't find '{CSV_FILE}' in this folder. Put your downloaded "
             f"CFPB complaints CSV here (or update CSV_FILE at the top of app.py "
             f"to match its actual filename), then reload the page.")
    st.stop()

with st.sidebar:
    st.header("Settings")
    try:
        products = get_available_products(CSV_FILE)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    product = st.selectbox("CFPB product", products)
    sample_size = st.slider("Number of complaints to pull", 5, 100, 20)
    st.caption(f"Reading from local file: {CSV_FILE}")

    st.divider()
    mock_mode = st.checkbox("Mock mode (no Azure key needed)", value=True)
    if not mock_mode:
        endpoint = st.text_input("Azure AI Language endpoint")
        key = st.text_input("Azure AI Language key", type="password")
    else:
        endpoint, key = None, None
        st.info("Mock mode is on: sentiment and key phrases will be fake placeholders, "
                "used only to test the fetch and routing logic.")

    run_button = st.button("Run analysis", type="primary")

if run_button:
    with st.spinner(f"Reading {sample_size} complaints for '{product}' from {CSV_FILE}..."):
        narratives = fetch_complaints(product, sample_size)

    if not narratives:
        st.warning("No complaints with narratives were found for that product. Try another one.")
        st.stop()

    rows = []
    progress = st.progress(0, text="Analyzing complaints...")
    for i, narrative in enumerate(narratives):
        sentiment, scores = analyze_sentiment(narrative, endpoint, key, mock_mode)
        key_phrases = extract_key_phrases(narrative, endpoint, key, mock_mode)
        category = assign_category(narrative)
        urgent = is_urgent(narrative, sentiment)
        rows.append({
            "narrative": narrative[:200],
            "sentiment": sentiment,
            "confidence": max(scores.values()) if scores else 0.0,
            "key_phrases": ", ".join(key_phrases),
            "category": category,
            "urgent": urgent,
        })
        progress.progress((i + 1) / len(narratives), text=f"Analyzing complaints... ({i + 1}/{len(narratives)})")

    progress.empty()
    results = pd.DataFrame(rows)

    col1, col2, col3 = st.columns(3)
    col1.metric("Complaints analyzed", len(results))
    col2.metric("Flagged urgent", int(results["urgent"].sum()))
    col3.metric("Categories found", results["category"].nunique())

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("By category")
        st.bar_chart(results["category"].value_counts())
    with chart_col2:
        st.subheader("By sentiment")
        st.bar_chart(results["sentiment"].value_counts())

    st.subheader("Complaint details")
    st.dataframe(results, use_container_width=True)

    csv = results.to_csv(index=False).encode("utf-8")
    st.download_button("Download results as CSV", csv, "complaint_triage_results.csv", "text/csv")
else:
    st.info("Set your options in the sidebar and click **Run analysis** to get started.")