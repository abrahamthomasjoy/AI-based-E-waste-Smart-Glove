"""
AI-based E-Waste Smart Glove — Backend Analysis
------------------------------------------------
Pulls temperature & humidity history from Adafruit IO, trains Random
Forest regressors to model sensor trends, and uses SHAP + LIME to
explain what's driving those trends (time of day, recent readings).

SETUP:
1. Copy ".env.example" to ".env"
2. Fill in your Adafruit IO username and key in .env
3. .env is git-ignored — your credentials will never be committed
4. Install dependencies: pip install -r requirements.txt
"""

import os
import matplotlib
matplotlib.use('TkAgg')  # Or use 'Qt5Agg' if you have PyQt5 installed

import requests
import pandas as pd
import shap
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from lime.lime_tabular import LimeTabularExplainer

# ---------------- Load credentials from .env ----------------
load_dotenv()

AIO_USERNAME = os.getenv("AIO_USERNAME")
AIO_KEY = os.getenv("AIO_KEY")

if not AIO_USERNAME or not AIO_KEY:
    raise EnvironmentError(
        "Missing AIO_USERNAME or AIO_KEY. "
        "Copy .env.example to .env and fill in your Adafruit IO credentials."
    )

TEMP_FEED = 'temperature'
HUM_FEED = 'humidity'
BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds"
HEADERS = {"X-AIO-Key": AIO_KEY}


def fetch_feed_data(feed_key, limit=200):
    url = f"{BASE_URL}/{feed_key}/data?limit={limit}&sort=desc"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def create_df(data):
    df = pd.DataFrame(data)[['created_at', 'value']]
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['value'] = df['value'].astype(float)
    df = df.sort_values('created_at')
    df.set_index('created_at', inplace=True)
    return df


def main():
    # Fetch and prepare data
    df_temp = create_df(fetch_feed_data(TEMP_FEED))
    df_hum = create_df(fetch_feed_data(HUM_FEED))

    # Merge temperature and humidity on timestamps
    df = pd.merge_asof(df_temp, df_hum, left_index=True, right_index=True,
                        suffixes=('_temp', '_hum'))

    # Feature engineering: time features + lagged sensors
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek
    df['temp_lag1'] = df['value_temp'].shift(1)
    df['hum_lag1'] = df['value_hum'].shift(1)
    df = df.dropna()

    # Define input features X and target variables y
    X = df[['hour', 'dayofweek', 'temp_lag1', 'hum_lag1']]
    y_temp = df['value_temp']
    y_hum = df['value_hum']

    # ---------------- Temperature model ----------------
    model_temp = RandomForestRegressor(n_estimators=100, random_state=42)
    model_temp.fit(X, y_temp)

    explainer_temp = shap.TreeExplainer(model_temp)
    shap_values_temp = explainer_temp.shap_values(X)
    shap.summary_plot(shap_values_temp, X, show=True)

    # ---------------- Humidity model ----------------
    model_hum = RandomForestRegressor(n_estimators=100, random_state=42)
    model_hum.fit(X, y_hum)

    explainer_hum = shap.TreeExplainer(model_hum)
    shap_values_hum = explainer_hum.shap_values(X)
    shap.summary_plot(shap_values_hum, X, show=True)

    # ---------------- LIME explanation (example instance) ----------------
    explainer_lime_temp = LimeTabularExplainer(
        X.values, feature_names=X.columns, verbose=True, mode='regression'
    )
    i = 10  # choose any test instance index
    exp_temp = explainer_lime_temp.explain_instance(
        X.iloc[i].values, model_temp.predict, num_features=4
    )
    exp_temp.show_in_notebook(show_table=True)

    # ---------------- Raw sensor visualization ----------------
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['value_temp'], label='Temperature (C)')
    plt.plot(df.index, df['value_hum'], label='Humidity (%)')
    plt.xlabel('Time')
    plt.ylabel('Sensor Readings')
    plt.title('Temperature and Humidity over Time')
    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()
