import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.config import (
    C_DONUT_1,
    C_DONUT_2,
    AIRLINE_PALETTE,
    DIR_COLOR_MAP,
    C_BAR
)

def build_direction_donut(df: pd.DataFrame) -> go.Figure:
    """Generates a donut chart displaying movements by direction."""
    dir_counts = df.groupby('DIRECTION', observed=True).size().reset_index(name='Count')
    fig = px.pie(
        dir_counts, 
        values='Count', 
        names='DIRECTION', 
        hole=0.55,
        color='DIRECTION',
        color_discrete_map={'TAKEOFF': C_DONUT_1, 'LANDING': C_DONUT_2}
    )
    total_count = df.shape[0]
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, title=None),
        annotations=[
            dict(
                text=f"<span style='color: black;'><b>{total_count:,}</b></span><br><span style='font-size: 14px; color: gray;'>Total</span>",
                x=0.5,
                y=0.5,
                font_size=24,
                showarrow=False,
                align="center"
            )
        ]
    )
    return fig

def build_airline_donut(df: pd.DataFrame) -> go.Figure:
    """Generates a donut chart displaying movements by airline."""
    al_counts = df.groupby('AIRLINE', observed=True).size().reset_index(name='Count')
    fig = px.pie(
        al_counts, 
        values='Count', 
        names='AIRLINE', 
        hole=0.55,
        color_discrete_sequence=AIRLINE_PALETTE
    )
    total_count = df.shape[0]
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5, title=None),
        annotations=[
            dict(
                text=f"<span style='color: black;'><b>{total_count:,}</b></span><br><span style='font-size: 14px; color: gray;'>Total</span>",
                x=0.5,
                y=0.5,
                font_size=24,
                showarrow=False,
                align="center"
            )
        ]
    )
    return fig

def build_airline_bar(df: pd.DataFrame) -> go.Figure:
    """Generates a bar chart displaying movement count by airline."""
    al_counts = df.groupby('AIRLINE', observed=True).size().reset_index(name='Count')
    al_counts = al_counts.sort_values('Count', ascending=False)
    fig = px.bar(
        al_counts, 
        x='AIRLINE', 
        y='Count', 
        text='Count',
        color='AIRLINE',
        color_discrete_sequence=AIRLINE_PALETTE,
        labels={'AIRLINE': 'Airline', 'Count': 'Movements'}
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False
    )
    return fig

def build_hourly_movements(df: pd.DataFrame, by_direction: bool = False) -> go.Figure:
    """Generates a bar chart showing movements by hour."""
    if by_direction:
        h_counts = df.groupby(['Hour', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        fig = px.bar(
            h_counts, 
            x='Hour', 
            y='Count', 
            color='DIRECTION', 
            barmode='group',
            text='Count',
            color_discrete_map=DIR_COLOR_MAP,
            labels={'Hour': 'Hour (UTC)', 'Count': 'Movements'}
        )
    else:
        h_counts = df.groupby('Hour', observed=True).size().reset_index(name='Count')
        fig = px.bar(
            h_counts, 
            x='Hour', 
            y='Count', 
            text='Count',
            color_discrete_sequence=[C_BAR],
            labels={'Hour': 'Hour (UTC)', 'Count': 'Movements'}
        )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
    )
    return fig

def build_minute_drilldown(min_df: pd.DataFrame) -> go.Figure:
    """Generates a detailed minute-by-minute bar chart for a single hour."""
    m_counts = min_df.groupby(['Minute', 'DIRECTION'], observed=True).size().reset_index(name='Count')
    fig = px.bar(
        m_counts, 
        x='Minute', 
        y='Count', 
        color='DIRECTION', 
        barmode='group',
        text='Count',
        color_discrete_map=DIR_COLOR_MAP,
        labels={'Minute': 'Minute', 'Count': 'Movements'}
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis=dict(
            tickmode='linear', 
            tick0=0, 
            dtick=5, 
            range=[-0.5, 59.5]
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None),
        margin=dict(l=5, r=5, t=5, b=5),
        bargap=0
    )
    fig.update_traces(width=0.5)
    return fig

def build_yearly_trends(df: pd.DataFrame, by_direction: bool = False) -> go.Figure:
    """Generates a bar chart showing yearly seaplane movement volume."""
    if by_direction:
        y_counts = df.groupby(['Year', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        fig = px.bar(
            y_counts, 
            x='Year', 
            y='Count', 
            color='DIRECTION', 
            barmode='group',
            text='Count',
            color_discrete_map=DIR_COLOR_MAP
        )
    else:
        y_counts = df.groupby('Year', observed=True).size().reset_index(name='Count')
        fig = px.bar(
            y_counts, 
            x='Year', 
            y='Count', 
            text='Count',
            color_discrete_sequence=[C_BAR]
        )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis=dict(tickmode='linear'),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
    )
    return fig

def build_monthly_trends(df: pd.DataFrame, by_direction: bool = False) -> go.Figure:
    """Generates a bar chart showing monthly volume trends chronologically."""
    if by_direction:
        m_counts = df.groupby(['Month', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        m_counts['Month_DT'] = pd.to_datetime(m_counts['Month'], format='%b %Y')
        m_counts = m_counts.sort_values('Month_DT')
        fig = px.bar(
            m_counts, 
            x='Month', 
            y='Count', 
            color='DIRECTION', 
            barmode='group',
            text='Count',
            color_discrete_map=DIR_COLOR_MAP
        )
    else:
        m_counts = df.groupby('Month', observed=True).size().reset_index(name='Count')
        m_counts['Month_DT'] = pd.to_datetime(m_counts['Month'], format='%b %Y')
        m_counts = m_counts.sort_values('Month_DT')
        fig = px.bar(
            m_counts, 
            x='Month', 
            y='Count', 
            text='Count',
            color_discrete_sequence=[C_BAR]
        )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
    )
    return fig

def build_yoy_comparison(m_compare: pd.DataFrame) -> go.Figure:
    """Generates a line chart to compare monthly movement volumes across different years (YoY)."""
    fig = px.line(
        m_compare, 
        x='Month_Name', 
        y='Count', 
        color='Year', 
        markers=True,
        text='YoY_Short_Label',
        hover_data={'Month_Name': True, 'Count': ':,', 'Year': True, 'YoY_Short_Label': False, 'YoY_Label': True},
        labels={'Month_Name': 'Month', 'Count': 'Movements', 'Year': 'Year', 'YoY_Label': 'YoY Change'}
    )
    fig.update_xaxes(
        categoryorder='array',
        categoryarray=['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None),
        hovermode="x unified"
    )
    return fig

def build_daily_volume(df: pd.DataFrame, by_direction: bool = False) -> go.Figure:
    """Generates a bar chart showing daily volume trends in a selected month."""
    if by_direction:
        d_counts = df.groupby(['Day', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        d_counts = d_counts.sort_values('Day')
        fig = px.bar(
            d_counts, 
            x='Day', 
            y='Count', 
            color='DIRECTION', 
            barmode='group',
            text='Count',
            color_discrete_map=DIR_COLOR_MAP,
            labels={'Day': 'Date', 'Count': 'Movements'}
        )
    else:
        d_counts = df.groupby('Day', observed=True).size().reset_index(name='Count')
        d_counts = d_counts.sort_values('Day')
        fig = px.bar(
            d_counts, 
            x='Day', 
            y='Count', 
            text='Count',
            color_discrete_sequence=[C_BAR],
            labels={'Day': 'Date', 'Count': 'Movements'}
        )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis=dict(tickformat='%d %b'),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
    )
    return fig

def build_historical_hourly(day_df: pd.DataFrame, by_direction: bool = False) -> go.Figure:
    """Generates a bar chart of hourly movements (local time) for historical drilldown."""
    if by_direction:
        h_counts = day_df.groupby(['Hour', 'DIRECTION'], observed=True).size().reset_index(name='Count')
        fig = px.bar(
            h_counts, 
            x='Hour', 
            y='Count', 
            color='DIRECTION', 
            barmode='group',
            text='Count',
            color_discrete_map=DIR_COLOR_MAP,
            labels={'Hour': 'Hour (Local)', 'Count': 'Movements'}
        )
    else:
        h_counts = day_df.groupby('Hour', observed=True).size().reset_index(name='Count')
        fig = px.bar(
            h_counts, 
            x='Hour', 
            y='Count', 
            text='Count',
            color_discrete_sequence=[C_BAR],
            labels={'Hour': 'Hour (Local)', 'Count': 'Movements'}
        )

    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis=dict(
            tickmode='linear', 
            tick0=0, 
            dtick=1,
            ticktext=[f"{h:02d}:00" for h in range(24)],
            tickvals=list(range(24))
        ),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, title=None)
    )
    return fig
