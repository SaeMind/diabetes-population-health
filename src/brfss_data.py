"""
CDC BRFSS State-Level Diabetes Data
=====================================
Generates synthetic state-level diabetes metrics calibrated to
CDC BRFSS 2021 published estimates. Used when live CDC API is
unavailable or for reproducible demo purposes.

Metrics per state:
  - diabetes_prevalence_pct     (diagnosed diabetes %)
  - prediabetes_prevalence_pct  (prediabetes %)
  - obesity_prevalence_pct      (BMI ≥ 30 %)
  - physical_inactivity_pct     (no leisure-time physical activity %)
  - high_bp_prevalence_pct      (hypertension %)
  - uninsured_pct               (no health insurance %)
  - median_hba1c_controlled_pct (% diabetics with HbA1c < 8%)
  - diabetes_mortality_rate     (age-adjusted deaths per 100K)
  - n_respondents               (BRFSS survey sample size)

Source calibration:
  CDC BRFSS 2021 Prevalence & Trends Data
  https://www.cdc.gov/brfss/brfssprevalence/
"""

import numpy as np
import pandas as pd

# State FIPS codes and abbreviations
STATES = {
    "Alabama": ("AL", "01"), "Alaska": ("AK", "02"), "Arizona": ("AZ", "04"),
    "Arkansas": ("AR", "05"), "California": ("CA", "06"), "Colorado": ("CO", "08"),
    "Connecticut": ("CT", "09"), "Delaware": ("DE", "10"), "Florida": ("FL", "12"),
    "Georgia": ("GA", "13"), "Hawaii": ("HI", "15"), "Idaho": ("ID", "16"),
    "Illinois": ("IL", "17"), "Indiana": ("IN", "18"), "Iowa": ("IA", "19"),
    "Kansas": ("KS", "20"), "Kentucky": ("KY", "21"), "Louisiana": ("LA", "22"),
    "Maine": ("ME", "23"), "Maryland": ("MD", "24"), "Massachusetts": ("MA", "25"),
    "Michigan": ("MI", "26"), "Minnesota": ("MN", "27"), "Mississippi": ("MS", "28"),
    "Missouri": ("MO", "29"), "Montana": ("MT", "30"), "Nebraska": ("NE", "31"),
    "Nevada": ("NV", "32"), "New Hampshire": ("NH", "33"), "New Jersey": ("NJ", "34"),
    "New Mexico": ("NM", "35"), "New York": ("NY", "36"), "North Carolina": ("NC", "37"),
    "North Dakota": ("ND", "38"), "Ohio": ("OH", "39"), "Oklahoma": ("OK", "40"),
    "Oregon": ("OR", "41"), "Pennsylvania": ("PA", "42"), "Rhode Island": ("RI", "44"),
    "South Carolina": ("SC", "45"), "South Dakota": ("SD", "46"), "Tennessee": ("TN", "47"),
    "Texas": ("TX", "48"), "Utah": ("UT", "49"), "Vermont": ("VT", "50"),
    "Virginia": ("VA", "51"), "Washington": ("WA", "53"), "West Virginia": ("WV", "54"),
    "Wisconsin": ("WI", "55"), "Wyoming": ("WY", "56"),
}

# Regional diabetes belt — Southern states have higher prevalence
# Based on CDC "Diabetes Belt" designation
HIGH_PREVALENCE_STATES = {
    "Alabama", "Arkansas", "Florida", "Georgia", "Kentucky", "Louisiana",
    "Mississippi", "North Carolina", "Oklahoma", "South Carolina",
    "Tennessee", "Texas", "West Virginia",
}

MODERATE_HIGH_STATES = {
    "Indiana", "Michigan", "Missouri", "New Mexico", "Ohio", "Virginia",
}


def generate_brfss_state_data(seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic CDC BRFSS state-level diabetes metrics.
    Values calibrated to published 2021 CDC BRFSS state estimates.
    """
    np.random.seed(seed)
    records = []

    for state_name, (abbr, fips) in STATES.items():
        # Diabetes prevalence (national mean ~11.3%, range 7–18%)
        if state_name in HIGH_PREVALENCE_STATES:
            base_diab = np.random.normal(14.2, 1.4)
        elif state_name in MODERATE_HIGH_STATES:
            base_diab = np.random.normal(12.1, 1.1)
        else:
            base_diab = np.random.normal(9.8, 1.3)

        diabetes_prev = np.clip(base_diab, 6.5, 18.5)

        # Correlated metrics (higher diabetes → higher comorbidities)
        diabetes_factor = (diabetes_prev - 9.0) / 5.0  # normalized deviation

        prediabetes = np.clip(
            np.random.normal(33.5, 2.8) + diabetes_factor * 2.5, 26, 42
        )
        obesity = np.clip(
            np.random.normal(32.1, 4.2) + diabetes_factor * 3.8, 22, 42
        )
        physical_inactivity = np.clip(
            np.random.normal(28.4, 4.8) + diabetes_factor * 4.2, 18, 45
        )
        high_bp = np.clip(
            np.random.normal(34.2, 3.9) + diabetes_factor * 3.1, 24, 46
        )
        uninsured = np.clip(
            np.random.normal(10.8, 4.2) - diabetes_factor * 1.2, 2.5, 22
        )

        # HbA1c control — inversely correlated with prevalence/poverty
        hba1c_controlled = np.clip(
            np.random.normal(58.2, 6.1) - diabetes_factor * 4.8, 40, 75
        )

        # Mortality — strongly correlated with prevalence
        mortality = np.clip(
            np.random.normal(22.1, 4.8) + diabetes_factor * 5.2, 10, 38
        )

        n_respondents = int(np.random.normal(8500, 2200))

        records.append({
            "state": state_name,
            "state_abbr": abbr,
            "fips": fips,
            "diabetes_prevalence_pct": round(diabetes_prev, 1),
            "prediabetes_prevalence_pct": round(prediabetes, 1),
            "obesity_prevalence_pct": round(obesity, 1),
            "physical_inactivity_pct": round(physical_inactivity, 1),
            "high_bp_prevalence_pct": round(high_bp, 1),
            "uninsured_pct": round(uninsured, 1),
            "hba1c_controlled_pct": round(hba1c_controlled, 1),
            "diabetes_mortality_rate": round(mortality, 1),
            "n_respondents": max(n_respondents, 3000),
            "data_year": 2021,
            "source": "CDC BRFSS 2021 (synthetic calibration)",
        })

    df = pd.DataFrame(records).sort_values("state").reset_index(drop=True)
    return df


# Metric display configuration
METRIC_CONFIG = {
    "diabetes_prevalence_pct": {
        "label": "Diabetes Prevalence",
        "unit": "%",
        "colorscale": "Reds",
        "description": "% adults with diagnosed diabetes (BRFSS 2021)",
        "lower_is_better": True,
        "national_avg": 11.3,
    },
    "prediabetes_prevalence_pct": {
        "label": "Prediabetes Prevalence",
        "unit": "%",
        "colorscale": "Oranges",
        "description": "% adults with prediabetes (BRFSS 2021)",
        "lower_is_better": True,
        "national_avg": 33.5,
    },
    "obesity_prevalence_pct": {
        "label": "Obesity Prevalence",
        "unit": "%",
        "colorscale": "YlOrRd",
        "description": "% adults with BMI ≥ 30 (BRFSS 2021)",
        "lower_is_better": True,
        "national_avg": 32.1,
    },
    "physical_inactivity_pct": {
        "label": "Physical Inactivity",
        "unit": "%",
        "colorscale": "PuRd",
        "description": "% adults with no leisure-time physical activity (BRFSS 2021)",
        "lower_is_better": True,
        "national_avg": 28.4,
    },
    "high_bp_prevalence_pct": {
        "label": "Hypertension Prevalence",
        "unit": "%",
        "colorscale": "RdPu",
        "description": "% adults with high blood pressure (BRFSS 2021)",
        "lower_is_better": True,
        "national_avg": 34.2,
    },
    "uninsured_pct": {
        "label": "Uninsured Rate",
        "unit": "%",
        "colorscale": "Blues",
        "description": "% adults without health insurance (BRFSS 2021)",
        "lower_is_better": True,
        "national_avg": 10.8,
    },
    "hba1c_controlled_pct": {
        "label": "HbA1c Controlled",
        "unit": "%",
        "colorscale": "Greens",
        "description": "% diabetics with HbA1c < 8% (good control) (BRFSS 2021)",
        "lower_is_better": False,
        "national_avg": 58.2,
    },
    "diabetes_mortality_rate": {
        "label": "Diabetes Mortality Rate",
        "unit": "per 100K",
        "colorscale": "Reds",
        "description": "Age-adjusted diabetes mortality rate per 100,000 (2021)",
        "lower_is_better": True,
        "national_avg": 22.1,
    },
}
