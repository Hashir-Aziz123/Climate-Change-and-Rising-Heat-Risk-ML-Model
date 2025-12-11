import numpy as np
import pandas as pd

def calculate_heat_index(temp, rh):
    """
    Vectorized Heat Index Calculation (NOAA Standard).
    Accepts scalar floats or pandas Series.
    """
    # Convert to Fahrenheit
    T_F = (temp * 9/5) + 32
    
    # Simple formula
    hi_simple = 0.5 * (T_F + 61.0 + ((T_F-68.0)*1.2) + (rh*0.094))
    
    # Full regression formula constants
    c1, c2, c3, c4 = -42.379, 2.04901523, 10.14333127, -0.22475541
    c5, c6, c7, c8, c9 = -6.83783e-3, -5.481717e-2, 1.22874e-3, 8.5282e-4, -1.99e-6
    
    hi_full = (c1 + c2*T_F + c3*rh + c4*T_F*rh + c5*T_F**2 + 
               c6*rh**2 + c7*T_F**2*rh + c8*T_F*rh**2 + c9*T_F**2*rh**2)
    
    # Logic: If simple HI > 80F, use full regression. 
    # Works for both scalars and Series using numpy where
    if isinstance(temp, (int, float)):
        return (hi_full if hi_simple > 80 else hi_simple - 32) * 5/9
    else:
        hi_final_f = np.where(hi_simple > 80, hi_full, hi_simple)
        return (hi_final_f - 32) * 5/9

def run_prediction(model, df):
    """
    Runs the ML model on a dataframe.
    Ensures columns are in the exact order the model expects.
    """
    # The exact feature list used in Notebook 04
    required_features = [
        'population_2020', 'pop_log', 
        'temp_c', 'humidity_relative', 'wind_speed_m_s', 'solar_w_m2',
        'temp_roll_24h', 'hi_max_72h', 'risk_lag_1h'
    ]
    
    # Validation
    for col in required_features:
        if col not in df.columns:
            raise ValueError(f"Missing feature: {col}")
            
    # Predict
    preds = model.predict(df[required_features])
    probs = model.predict_proba(df[required_features])
    
    return preds, probs