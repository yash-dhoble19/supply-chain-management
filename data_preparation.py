# backend/data_preparation.py
# ---------------------------
# Responsibility:
# - Standardize data & handle column mapping
# - Filter by category
# - Convert Daily data to Monthly Aggregation (Sum of units sold)
# - Validate data sufficiency (Initial check for basic viability)

import pandas as pd
from config import settings


def prepare_category_data(
    df: pd.DataFrame,
    category: str,
    date_col: str = "Date",
    category_col: str = "Category",
    units_col: str = "Units_Sold",
    time_grouping: str = "Monthly"
) -> pd.DataFrame:
    """
    Standardizes and aggregates raw data into required frequency ('ds' and 'y') 
    for the Prophet model.
    
    Args:
        df: Raw input DataFrame
        category: Category/Product to filter for
        date_col: Name of the date column in input
        category_col: Name of the category column in input
        units_col: Name of the units sold column in input
        
    Returns:
        pd.DataFrame: Monthly aggregated data with 'ds' and 'y' columns
        
    Raises:
        ValueError: If data is insufficient or category not found
    """
    
    df = df.copy()

    # 1. Column Standardization & Cleanup
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    if df.empty:
        raise ValueError("No valid dates found in the uploaded data.")

    # Ensure numeric units
    df[units_col] = pd.to_numeric(df[units_col], errors="coerce").fillna(0)
    df[units_col] = df[units_col].clip(lower=0)

    # 2. Filter by category
    df = df[df[category_col] == category]

    if df.empty:
        raise ValueError(
            f"No data available for category '{category}'. "
            "Please check if the category exists in your data."
        )

    # Keep required columns and rename for Prophet
    clean_df = df[[date_col, units_col]].rename(columns={
        date_col: "ds",   # Prophet date column
        units_col: "y"    # Prophet value column
    })

    # 3. Aggregation and Sorting based on time_grouping
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "MS"}
    freq = freq_map.get(time_grouping, "MS")

    monthly_df = (
        clean_df
        .set_index("ds")["y"]
        .resample(freq)
        .sum()
        .reset_index()
    )
    
    # Sort by date
    monthly_df = monthly_df.sort_values("ds").reset_index(drop=True)
    
    if monthly_df.empty:
        raise ValueError("Data became empty after resampling.")

    # 4. Data sufficiency check based on exact business rules
    data_span_days = (monthly_df["ds"].max() - monthly_df["ds"].min()).days

    if time_grouping == "Daily":
        # Rule: Daily needs 3-6 months (approx 90 days minimum)
        if data_span_days < 90:
            raise ValueError(f"Daily forecast requires 3-6 months of data for weekly patterns. Only {data_span_days} days found.")
    elif time_grouping == "Weekly":
        # Rule: Weekly needs 1 year (365 days minimum)
        if data_span_days < 365:
            raise ValueError(f"Weekly forecast requires 1 year of data for yearly seasonality. Only ~{int(data_span_days/7)} weeks found.")
    elif time_grouping == "Monthly":
        # Rule: Monthly needs 2-3 years (approx 730 days minimum)
        if data_span_days < 730:
            raise ValueError(f"Monthly forecast requires 2-3 years of data for long trends. Only ~{int(data_span_days/30)} months found.")

    # 5. Calculate additional statistics for context
    monthly_df.attrs["category"] = category
    monthly_df.attrs["total_units"] = int(monthly_df["y"].sum())
    monthly_df.attrs["avg_monthly_units"] = float(monthly_df["y"].mean())
    monthly_df.attrs["data_start"] = monthly_df["ds"].min()
    monthly_df.attrs["data_end"] = monthly_df["ds"].max()

    return monthly_df


def get_data_summary(monthly_df: pd.DataFrame) -> dict:
    """
    Generate a summary of the prepared data.
    
    Args:
        monthly_df: Monthly aggregated DataFrame
        
    Returns:
        dict: Summary statistics
    """
    return {
        "num_months": len(monthly_df),
        "total_units": int(monthly_df["y"].sum()),
        "avg_monthly_units": round(monthly_df["y"].mean(), 2),
        "min_monthly_units": int(monthly_df["y"].min()),
        "max_monthly_units": int(monthly_df["y"].max()),
        "std_monthly_units": round(monthly_df["y"].std(), 2),
        "date_range_start": monthly_df["ds"].min().strftime("%Y-%m-%d"),
        "date_range_end": monthly_df["ds"].max().strftime("%Y-%m-%d")
    }

# anything
