# Pakistan Heat Risk ML Algorithm

## 01_OVERVIEW
The **Pakistan Heat Risk ML Algorithm** is a machine learning-powered decision support system designed to predict human health risks during extreme heat events.

Unlike traditional tools that rely on static Heat Index formulas (which fail to capture cumulative stress), this system utilizes a **Machine Learning Classifier** to model the non-linear interactions between weather variables, environmental stressors, and **historical heat accumulation** (hysteresis).

The application is engineered with a **"Terminal-Style"** interface to simulate a crisis monitoring environment for government/disaster management agencies.

---

## 02_MACHINE_LEARNING_IMPLEMENTATION

This project solves a **Classification Problem**. While the NOAA Heat Index provides a snapshot of current conditions, it ignores the physiological reality of heat death. Our ML model improves upon this by integrating:

1.  **Temporal Memory (Hysteresis):**
    * We engineered Lag Features (`risk_lag_1h`, `hi_max_72h`) to teach the model that duration matters.
    * *Result:* The model correctly identifies "Extreme Danger" during prolonged heatwaves even when daily peak temperatures drop slightly, capturing the cumulative stress that simple formulas miss.

2.  **Non-Linear Physics:**
    * Standard formulas assume wind always cools. Our model captures complex interactions (e.g., the "Convection Oven Effect") where high wind speeds at temperatures >37°C actually accelerate dehydration and risk.

3.  **Multi-Dimensional Decision Boundaries:**
    * The model classifies risk into 4 actionable categories (**Safe, Caution, Danger, Extreme**) by analyzing a 6-dimensional feature space (Temp, Humidity, Solar Radiation, Wind, Population Density, and Lags).

---

## 03_SYSTEM_MODULES

###  SIMULATION_ZONE
* **Purpose:** Counterfactual analysis for policy planning.
* **Input:** User-controlled sliders for Global Warming (+0°C to +5°C), Humidity Shifts, and Population Booms.
* **Output:** GPU-Accelerated PyDeck map rendering risk zones across 141 districts instantly.

### LIVE_UPLINK 
* **Purpose:** Operational situational awareness.
* **Tech:** Connects to **Open-Meteo Satellite API** to fetch real-time telemetry.
* **Output:** Live "Thermal Stress Index" gauge and instantaneous Risk Classification for any selected district.

### HISTORICAL_PRESENTATION
* **Purpose:** Model validation and post-disaster analysis.
* **Data:** Reconstructs the deadly **June 2015 Karachi Heatwave**.
* **Output:** 4-Hour interval time-series animation visualizing the spread of the heatwave from the coast to the interior.

---

## 04_INSTALLATION_PROTOCOLS

**Prerequisites:** Python 3.8+

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-username/heat-risk-command-center.git](https://github.com/Hashir-Aziz123/Climate-Change-and-Rising-Heat-Risk-ML-Model.git)
    cd Climate-Change-and-Rising-Heat-Risk-ML-Model

    ```

2.  **Initialize Environment**
    ```bash
    # Optional: Create virtual env
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute System**
    ```bash
    streamlit run app/main.py
    ```

---

## 05_PROJECT_STRUCTURE

```text
heat-risk-command-center/
├── app/
│   ├── main.py              # Entry Point (Navigation & Routing)
│   ├── style.css            # Custom CSS (Terminal Theme)
│   │   
│   ├── data/
│   │   ├── app_baseline.csv                # Monthly Climatology Data
│   │   ├── app_history_2015.csv            # 2015 Heatwave Data
│   │   └── pakistan_districts.geojson      # Optimized Map Boundaries
|   |   └─── district_coords.csv            # District Coordinates
│   ├── utils/
│   │   ├── data_loader.py   # Caching & I/O Operations
│   │   └── model_engine.py  # Physics Formulas & ML Inference
│   └── views/
│       ├── dashboard.py     # Simulation View logic
│       ├── live_monitor.py  # API Connection logic
│       └── history.py       # Animation logic
├── models/
│   └── heat_risk_model.pkl  # Trained Model Artifact
├── notebooks/               # Research & Training Logs
│   ├── 01_exploration.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_model_training.ipynb
│   ├── 05_evaluation.ipynb
│   
├── src/
│   └── ...
├── tests/
│   └── ...
├── report/
│   └── ...
├── requirements.txt         # Dependency Manifest
└── README.md                # System Manual