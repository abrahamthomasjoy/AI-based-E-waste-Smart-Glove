# AI-based E-Waste Smart Glove ♻️🧤

An **Explainable AI (XAI)-driven** IoT wearable system designed to enhance worker safety during e-waste handling — combining real-time environmental sensing with transparent, interpretable AI insights for plant supervisors.

## 🎯 Problem
Workers handling e-waste are often exposed to elevated temperatures and unsafe conditions without real-time feedback, and plant supervisors typically lack centralized, trustworthy tools to monitor worker safety. Many AI safety-monitoring systems act as "black boxes," making their outputs hard to trust or act on.

## 💡 Solution
The Smart Glove captures real-time temperature and humidity data at the point of contact, alerts the wearer locally, and streams data to the cloud. On the backend, machine learning models forecast upcoming sensor trends, and an **Explainable AI layer (SHAP & LIME)** reveals *which factors* — time of day, recent readings — are driving those trends, giving plant owners transparent, interpretable insight rather than a black-box alert.

## 🏗️ System Architecture

**1. Edge Device (Glove)**
- HTU21D-F sensor reads temperature & humidity
- OLED display (SSD1306) shows live readings to the wearer
- Piezo buzzer provides immediate audible alerts when temp > 29°C or humidity > 80%
- ESP32 (DFRobot Beetle ESP32-C6 Mini) handles sensing, display, and connectivity

**2. Connectivity**
- ESP32 connects to WiFi
- Sensor data published via **MQTT** to **Adafruit IO**, which acts as the cloud broker and feed storage

**3. Backend Processing**
- Python script pulls historical feed data from the Adafruit IO REST API
- Feature engineering: hour of day, day of week, and lagged (previous) temperature/humidity readings
- Two **Random Forest Regressor** models are trained — one for temperature, one for humidity — to model sensor trends

**4. 🧠 Explainable AI (XAI) — Core Component**
- **SHAP** (`TreeExplainer`) generates summary plots showing which features most influence predicted temperature/humidity
- **LIME** explains individual predictions on a per-instance basis
- Goal: make the AI's reasoning behind trend predictions interpretable for non-technical plant supervisors, not just a black-box number

**5. Visualization**
- Time-series plots of temperature and humidity
- SHAP summary plots and LIME instance explanations for supervisor-facing insight

## 🛠️ Hardware
| Component | Purpose |
|---|---|
| DFRobot Beetle ESP32-C6 Mini | Main microcontroller — sensing, display, buzzer, WiFi/MQTT |
| HTU21D-F Sensor | Temperature & moisture sensing |
| SSD1306 OLED Display | Real-time readout for the wearer |
| Piezo Buzzer | Audible safety alerts (temp > 29°C or humidity > 80%) |
| 3.7V LiPo Battery | Portable power source |
| TP4056 Module | Battery charging management |

## 🧠 Software & AI Stack
- **Firmware:** ESP32 (Arduino/C++) — sensor reading, OLED display, WiFi & MQTT publishing to Adafruit IO
- **Backend:** Python — Adafruit IO REST API client, pandas for data prep
- **ML Models:** scikit-learn `RandomForestRegressor` (temperature & humidity trend prediction)
- **Explainability:** SHAP, LIME *(core differentiator of the project)*
- **Visualization:** matplotlib

## 🔮 Planned Additions
- **PCM (Phase Change Material) integration** for active thermal regulation within the glove
- **3D-modeled cooling chamber** to house and integrate the PCM material into the glove structure
- Web dashboard for real-time supervisor monitoring (currently local script-based visualization)

## 🔐 Configuration
This project keeps credentials out of source code. Before running:
1. Copy `config.example.h` → `config.h` (Arduino) and fill in your WiFi + Adafruit IO credentials
2. Copy `.env.example` → `.env` (Python) and fill in your Adafruit IO credentials
3. Both `config.h` and `.env` are git-ignored and will never be committed

## 🚀 Getting Started
1. Flash `smart_glove.ino` to the ESP32 after setting up `config.h`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Set up `.env` with your Adafruit IO credentials
4. Run `analysis.py` to fetch feed data and generate SHAP/LIME visualizations

## 📸 Demo / CAD Models
*(Add photos of the physical prototype, plots/screenshots of SHAP & LIME output, and PCM cooling chamber 3D renders)*

## 👤 Author
Abraham Thomas Joy — Robotics & Mechatronics undergraduate, AI/ML minor
