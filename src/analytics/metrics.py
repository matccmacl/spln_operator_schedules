import pandas as pd
import numpy as np

def clean_and_optimize_data(movements_df: pd.DataFrame, registrations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans, joins, and optimizes the raw movements and registrations dataframes.
    Performs memory optimization using Category datatypes and date parsing.
    """
    if movements_df.empty:
        return pd.DataFrame()

    df = movements_df.copy()
    reg_df = registrations_df.copy()

    # Join with registrations if available
    if not reg_df.empty:
        df['REG'] = df['REG'].astype(str).str.strip().str.upper()
        reg_df['REG'] = reg_df['REG'].astype(str).str.strip().str.upper()
        df = df.merge(reg_df[['REG', 'SPECIES', 'MTOW', 'AC TYPE']], on='REG', how='left')

    # Date parsing
    for col in ['DATE TIME UTC', 'DATE TIME LOCAL']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Add dashboard feature engineering columns
    if 'DATE TIME UTC' in df.columns:
        df = df.dropna(subset=['DATE TIME UTC'])
        df['Month'] = df['DATE TIME UTC'].dt.strftime('%b %Y')
        df['MonthName'] = df['DATE TIME UTC'].dt.strftime('%B')
        df['Year'] = df['DATE TIME UTC'].dt.year.astype(int)
        df['Day'] = df['DATE TIME UTC'].dt.date
        df['Hour'] = df['DATE TIME UTC'].dt.hour.astype(int)
        df['Minute'] = df['DATE TIME UTC'].dt.minute.astype(int)
        df['Minute_Bin'] = df['DATE TIME UTC'].dt.floor('15min').dt.strftime('%H:%M')
    
    # Normalize Direction
    if 'DIRECTION' in df.columns:
        df['DIRECTION'] = df['DIRECTION'].astype(str).str.upper().str.strip()
        df = df[df['DIRECTION'].isin(['TAKEOFF', 'LANDING'])]
        df['DIRECTION'] = df['DIRECTION'].astype('category')

    # Category optimization for high-performance sorting/grouping
    for col in ['AIRLINE', 'REG', 'FROM', 'TO']:
        if col in df.columns:
            df[col] = df[col].astype(str).astype('category')
        
    return df

def calculate_yoy_monthly_comparison(hist_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Year-over-Year (YoY) monthly comparison metrics.
    Sorts by Month_Num and Year to correctly calculate historical shifts,
    then adds custom trend labels.
    """
    if hist_df.empty:
        return pd.DataFrame()
        
    line_df = hist_df.copy()
    line_df['Month_Num'] = line_df['DATE TIME UTC'].dt.month
    line_df['Month_Name'] = line_df['DATE TIME UTC'].dt.strftime('%B')
    line_df['Year_Val'] = line_df['DATE TIME UTC'].dt.year
    
    m_compare = line_df.groupby(['Year_Val', 'Month_Num', 'Month_Name'], observed=True).size().reset_index(name='Count')
    
    # Sort by Month_Num and Year to correctly calculate shift from the previous year
    m_compare = m_compare.sort_values(['Month_Num', 'Year_Val'])
    m_compare['Prev_Count'] = m_compare.groupby('Month_Num')['Count'].shift(1)
    m_compare['YoY_Change_Pct'] = ((m_compare['Count'] - m_compare['Prev_Count']) / m_compare['Prev_Count']) * 100
    
    m_compare['YoY_Label'] = m_compare.apply(
        lambda r: "Baseline (First Year)" if pd.isna(r['YoY_Change_Pct']) else f"{r['YoY_Change_Pct']:+.1f}% vs Prev Year",
        axis=1
    )
    m_compare['YoY_Short_Label'] = m_compare.apply(
        lambda r: "" if pd.isna(r['YoY_Change_Pct']) else f"{r['YoY_Change_Pct']:+.1f}%",
        axis=1
    )
    
    # Sort back to Year and Month_Num so Plotly draws lines chronologically per year
    m_compare = m_compare.sort_values(['Year_Val', 'Month_Num'])
    m_compare.rename(columns={'Year_Val': 'Year'}, inplace=True)
    m_compare['Year'] = m_compare['Year'].astype(str)
    
    return m_compare
