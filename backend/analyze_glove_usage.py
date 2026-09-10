"""
AI-based E-Waste Smart Glove — Rule-Based Threshold Analytics
----------------------------------------------------------------
This is the currently deployed analytics script referenced in the
Capstone Report (Fig. 7). It fetches temperature & humidity history
from Adafruit IO and flags time periods where readings exceeded safe
thresholds (29°C for temperature, 80% for humidity), recommending
action for each flagged period.

This rule-based layer is the working, deployed analytics logic.
The SHAP/LIME explainable AI layer (see analysis.py) is the more
advanced, model-based explainability layer built on top of this.

SETUP:
1. Copy ".env.example" to ".env"
2. Fill in your Adafruit IO username and key in .env
3. .env is git-ignored — your credentials will never be committed
4. Install dependencies: pip install -r requirements.txt
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv

# ---------------- Load credentials from .env ----------------
load_dotenv()

AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

if not AIO_USERNAME or not AIO_KEY:
    raise EnvironmentError(
        "Missing AIO_USERNAME or AIO_KEY. "
        "Copy .env.example to .env and fill in your Adafruit IO credentials."
    )

TEMP_FEED = "temperature"
HUM_FEED = "humidity"
BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds"
HEADERS = {"X-AIO-Key": AIO_KEY}

TEMP_THRESHOLD_C = 29.0
HUMIDITY_THRESHOLD_PCT = 80.0


def fetch_feed_data(feed_key, limit=200):
    """Fetch the most recent `limit` readings for a given Adafruit IO feed."""
    url = f"{BASE_URL}/{feed_key}/data?limit={limit}&sort=desc"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data)[["created_at", "value"]]
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["value"] = df["value"].astype(float)
    df = df.sort_values("created_at").reset_index(drop=True)
    return df


def find_high_periods(df, threshold, threshold_name):
    """
    Scan a sensor dataframe and identify contiguous time periods where
    the value exceeded the given threshold. Returns a list of
    human-readable explanation strings, one per exceedance period.
    """
    explanations = []
    in_period = False
    start_time = None
    prev_time = None

    for _, row in df.iterrows():
        exceeded = row["value"] > threshold

        if exceeded and not in_period:
            in_period = True
            start_time = row["created_at"]
        elif not exceeded and in_period:
            in_period = False
            duration = prev_time - start_time
            explanations.append(
                f"{threshold_name} exceeded from {start_time} to {prev_time} "
                f"({duration}), action recommended."
            )

        prev_time = row["created_at"]

    # Handle a period that's still ongoing at the end of the data
    if in_period:
        duration = prev_time - start_time
        explanations.append(
            f"{threshold_name} exceeded from {start_time} to {prev_time} "
            f"({duration}), action recommended."
        )

    return explanations


def analyze_glove_usage():
    """
    Fetch recent temperature & humidity data and return a combined list
    of explanations for any unsafe periods detected. If no thresholds
    were breached, returns a single reassuring message.
    """
    temp_data = fetch_feed_data(TEMP_FEED, limit=200)
    hum_data = fetch_feed_data(HUM_FEED, limit=200)

    temp_explanations = find_high_periods(
        temp_data, threshold=TEMP_THRESHOLD_C, threshold_name="Temperature"
    )
    hum_explanations = find_high_periods(
        hum_data, threshold=HUMIDITY_THRESHOLD_PCT, threshold_name="Humidity"
    )

    combined = temp_explanations + hum_explanations
    if not combined:
        combined.append("Glove usage is within safe limits.")

    return combined


if __name__ == "__main__":
    explanations = analyze_glove_usage()
    for line in explanations:
        print(line)
