import os
import sys
import pandas as pd
import numpy as np
import pytest

# Ensure the project root is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics.metrics import clean_and_optimize_data, calculate_yoy_monthly_comparison

def test_clean_and_optimize_data():
    """Verify that raw movements are correctly joined, parsed, and converted to optimized Category types."""
    # Mock movements
    movements_df = pd.DataFrame([
        {
            "FILENAME": "schedule.xlsx",
            "DATE TIME UTC": "2026-05-22 05:00:00",
            "DATE TIME LOCAL": "2026-05-22 10:00:00",
            "AIRLINE": "MALDIVIAN",
            "FLT NUMBER": "Q2 101",
            "REG": "8Q-IAK",
            "FROM": "MLE",
            "TO": "DRV",
            "DIRECTION": "TAKEOFF"
        }
    ])
    
    # Mock registrations
    registrations_df = pd.DataFrame([
        {
            "REG": "8Q-IAK",
            "SPECIES": "TWIN OTTER",
            "MTOW": 5670,
            "AC TYPE": "DHC6"
        }
    ])
    
    optimized_df = clean_and_optimize_data(movements_df, registrations_df)
    
    assert not optimized_df.empty
    # Assert join worked
    assert "SPECIES" in optimized_df.columns
    assert optimized_df["SPECIES"].iloc[0] == "TWIN OTTER"
    assert optimized_df["AC TYPE"].iloc[0] == "DHC6"
    
    # Assert date column types
    assert pd.api.types.is_datetime64_any_dtype(optimized_df["DATE TIME UTC"])
    assert pd.api.types.is_datetime64_any_dtype(optimized_df["DATE TIME LOCAL"])
    
    # Assert feature engineering columns
    for col in ["Month", "MonthName", "Year", "Day", "Hour", "Minute", "Minute_Bin"]:
        assert col in optimized_df.columns
    assert optimized_df["Year"].iloc[0] == 2026
    assert optimized_df["MonthName"].iloc[0] == "May"
    assert optimized_df["Month"].iloc[0] == "May 2026"
    
    # Assert memory optimizations (Categories)
    assert isinstance(optimized_df["AIRLINE"].dtype, pd.CategoricalDtype)
    assert isinstance(optimized_df["REG"].dtype, pd.CategoricalDtype)
    assert isinstance(optimized_df["DIRECTION"].dtype, pd.CategoricalDtype)

def test_calculate_yoy_monthly_comparison():
    """Verify that YoY monthly counts, percentage changes, and labels are computed correctly."""
    # Create mock movements for March 2025 and March 2026
    data = []
    
    # 10 movements in March 2025
    for _ in range(10):
        data.append({
            "DATE TIME UTC": pd.Timestamp("2025-03-15 10:00:00")
        })
    # 15 movements in March 2026 (50% increase YoY)
    for _ in range(15):
        data.append({
            "DATE TIME UTC": pd.Timestamp("2026-03-15 10:00:00")
        })
        
    hist_df = pd.DataFrame(data)
    hist_df["Year"] = hist_df["DATE TIME UTC"].dt.year
    
    m_compare = calculate_yoy_monthly_comparison(hist_df)
    
    assert not m_compare.empty
    assert len(m_compare) == 2  # 2025 and 2026 entries
    
    # Sort for assertion
    m_compare = m_compare.sort_values("Year")
    
    row_2025 = m_compare.iloc[0]
    row_2026 = m_compare.iloc[1]
    
    # 2025 asserts (first year, so baseline)
    assert row_2025["Year"] == "2025"
    assert row_2025["Count"] == 10
    assert pd.isna(row_2025["Prev_Count"])
    assert pd.isna(row_2025["YoY_Change_Pct"])
    assert row_2025["YoY_Short_Label"] == ""
    
    # 2026 asserts (+50% YoY)
    assert row_2026["Year"] == "2026"
    assert row_2026["Count"] == 15
    assert row_2026["Prev_Count"] == 10
    assert row_2026["YoY_Change_Pct"] == 50.0
    assert row_2026["YoY_Short_Label"] == "+50.0%"
    assert "50.0%" in row_2026["YoY_Label"]
