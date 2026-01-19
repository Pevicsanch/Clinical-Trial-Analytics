"""
Visualization utilities for clinical trial analysis.

This module provides reusable plotting functions with consistent styling
for distribution analysis (bar charts) and temporal trends (line charts, heatmaps).

Usage:
    from src.analysis.viz import create_horizontal_bar_chart, create_multi_line_chart
"""

from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale


# ============================================================
# Visual Constants (Theme)
# ============================================================

COLORSCALE = [[0, "#f1f5f9"], [1, "#2563eb"]]  # Light gray → Blue
FONT_FAMILY = "Arial"
FONT_COLOR = "#374151"
ANNOTATION_COLOR = "#6b7280"

# Default color palette for categorical data
DEFAULT_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2']


# ============================================================
# Helper Functions
# ============================================================

def format_rate_table(
    df: pd.DataFrame,
    factor_col: str,
    factor_name: str,
    rate_col: str = 'completion_rate_pct',
    n_col: str = 'n_resolved',
    completed_col: str = 'n_completed',
) -> pd.DataFrame:
    """
    Format a rate DataFrame for display (e.g., in Jupyter notebooks).
    
    Takes output from calc_completion_rate() and formats it for presentation:
    - Renames columns to human-readable names
    - Formats rate as "XX.X%"
    
    Parameters:
    -----------
    df : DataFrame with rate metrics
    factor_col : Column with factor values
    factor_name : Display name for factor column
    rate_col : Column with rate values (0-100 scale)
    n_col : Column with sample size
    completed_col : Column with completed count
    
    Returns:
    --------
    Formatted DataFrame ready for display()
    """
    t = df[[factor_col, n_col, completed_col, rate_col]].copy()
    t[rate_col] = t[rate_col].apply(lambda x: f"{x:.1f}%")
    t.columns = [factor_name, 'n', 'Completed', 'Rate']
    return t.reset_index(drop=True)


def format_pct_label(value: float, total: float, include_count: bool = True) -> str:
    """
    Format a percentage label with smart decimal handling.
    
    - Shows 2 decimals for percentages < 1% (e.g., 0.05%)
    - Shows 1 decimal otherwise (e.g., 12.3%)
    
    Parameters:
    -----------
    value : The count value
    total : Total for percentage calculation
    include_count : Whether to include the count in parentheses
    """
    pct = value / total * 100 if total > 0 else 0
    
    if pct < 1 and pct > 0:
        pct_str = f"{pct:.2f}%"
    else:
        pct_str = f"{pct:.1f}%"
    
    if include_count:
        return f"{pct_str} ({int(value):,})"
    return pct_str


# ============================================================
# Chart Functions
# ============================================================

def create_horizontal_bar_chart(
    data: pd.DataFrame,
    value_col: str,
    label_col: str,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    colorscale: Optional[list] = None,
    height: int = 450,
    show_pct: bool = True,
    order_by_value: bool = False,
    total_for_pct: Optional[int] = None,
) -> go.Figure:
    """
    Create a standardized horizontal bar chart for distribution analysis.
    
    Parameters:
    -----------
    data : DataFrame with value_col and label_col
    value_col : Column name for bar values (x-axis)
    label_col : Column name for bar labels (y-axis)
    title : Main title (bold)
    subtitle : Subtitle (smaller, gray)
    note : Optional footnote annotation
    colorscale : Plotly colorscale (default: blue gradient)
    height : Figure height in pixels
    show_pct : Whether to show percentage in labels
    order_by_value : If True, sort by value descending (largest at top)
    total_for_pct : Total for percentage calculation (default: sum of values)
    
    Returns:
    --------
    Plotly Figure object
    """
    df = data.copy()
    
    # Sort by value if requested
    if order_by_value:
        df = df.sort_values(value_col, ascending=False)
    
    total = total_for_pct if total_for_pct else df[value_col].sum()
    
    # Create labels
    if show_pct:
        df['_label'] = df[value_col].apply(lambda v: format_pct_label(v, total))
    else:
        df['_label'] = df[value_col].apply(lambda v: f"{int(v):,}")
    
    # Color gradient based on value
    colorscale = colorscale or COLORSCALE
    min_v = float(df[value_col].min())
    max_v = float(df[value_col].max())
    ratios = [
        (float(v) - min_v) / (max_v - min_v) if max_v > min_v else 1.0
        for v in df[value_col]
    ]
    colors = sample_colorscale(colorscale, ratios)
    
    # Create figure
    fig = go.Figure(
        go.Bar(
            x=df[value_col],
            y=df[label_col],
            orientation='h',
            text=df['_label'],
            textposition='outside',
            marker_color=colors,
            cliponaxis=False,
            hovertemplate='<b>%{y}</b><br>Trials: %{x:,}<extra></extra>',
        )
    )
    
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px; color:{ANNOTATION_COLOR}'>{subtitle}</span>"
            ),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(showgrid=False, showticklabels=False, title=None, rangemode='tozero'),
        yaxis=dict(title=None, tickfont=dict(size=12), autorange='reversed'),
        height=height,
        template='plotly_white',
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(l=180, r=180, t=80, b=120 if note else 50),
        bargap=0.22,
    )
    
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.25,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_rate_bar_chart(
    data: pd.DataFrame,
    rate_col: str,
    label_col: str,
    n_col: str,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    colorscale: Optional[list] = None,
    height: int = 400,
    x_title: str = 'Rate (%)',
) -> go.Figure:
    """
    Create a horizontal bar chart for rate/percentage metrics (e.g., completion rate).
    
    Unlike create_horizontal_bar_chart (for counts), this function:
    - Displays pre-calculated percentages directly
    - Shows sample size (n) in hover
    - Uses consistent styling with other viz functions
    
    Parameters:
    -----------
    data : DataFrame with rate_col, label_col, and n_col
    rate_col : Column with pre-calculated rate (0-100 scale)
    label_col : Column for bar labels (y-axis)
    n_col : Column with sample size for hover info
    title : Main title (bold)
    subtitle : Subtitle (smaller, gray)
    note : Optional footnote annotation
    colorscale : Plotly colorscale (default: blue gradient)
    height : Figure height in pixels
    x_title : X-axis title
    
    Returns:
    --------
    Plotly Figure object
    """
    df = data.copy()
    colorscale = colorscale or COLORSCALE
    
    # Color gradient based on rate
    min_v = float(df[rate_col].min())
    max_v = float(df[rate_col].max())
    ratios = [
        (float(v) - min_v) / (max_v - min_v) if max_v > min_v else 1.0
        for v in df[rate_col]
    ]
    colors = sample_colorscale(colorscale, ratios)
    
    # Create figure
    fig = go.Figure(
        go.Bar(
            x=df[rate_col],
            y=df[label_col],
            orientation='h',
            text=df[rate_col].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            marker_color=colors,
            cliponaxis=False,
            hovertemplate=(
                '<b>%{y}</b><br>'
                f'{x_title}: %{{x:.1f}}%<br>'
                'n=%{customdata:,}<extra></extra>'
            ),
            customdata=df[n_col],
        )
    )
    
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px; color:{ANNOTATION_COLOR}'>{subtitle}</span>"
            ),
            x=0.5,
            xanchor='center',
            font=dict(family=FONT_FAMILY, size=16, color=FONT_COLOR),
        ),
        xaxis=dict(
            title=x_title,
            showgrid=True,
            gridcolor='#f3f4f6',
            zeroline=False,
            range=[0, 105],  # Leave room for labels
        ),
        yaxis=dict(
            title=None,
            showgrid=False,
            # No autorange='reversed' - caller controls order via data sorting
        ),
        template='plotly_white',
        height=height,
        margin=dict(l=150, r=80, t=80, b=100 if note else 50),
        font=dict(family=FONT_FAMILY, size=12, color=FONT_COLOR),
    )
    
    # Add note annotation (below x-axis title with more spacing)
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.28,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_multi_line_chart(
    pivot_data: pd.DataFrame,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    colors: Optional[dict] = None,
    height: int = 500,
    show_total: bool = False,
    y_title: str = 'Number of Trials',
) -> go.Figure:
    """
    Create a multi-line chart for temporal trends.
    
    Parameters:
    -----------
    pivot_data : DataFrame with index=year, columns=categories, values=counts
    title : Main title
    subtitle : Subtitle
    note : Optional footnote
    colors : Dict mapping column names to colors
    height : Figure height
    show_total : Whether to add a total line
    y_title : Y-axis title
    
    Returns:
    --------
    Plotly Figure object
    """
    fig = go.Figure()
    
    colors = colors or {}
    
    for idx, col in enumerate(pivot_data.columns):
        color = colors.get(col, DEFAULT_COLORS[idx % len(DEFAULT_COLORS)])
        fig.add_trace(
            go.Scatter(
                x=pivot_data.index,
                y=pivot_data[col],
                name=col,
                mode='lines+markers',
                line=dict(width=2.5, color=color),
                marker=dict(size=5),
                hovertemplate=f'<b>{col}</b><br>Year: %{{x}}<br>Trials: %{{y:,}}<extra></extra>',
            )
        )
    
    if show_total:
        fig.add_trace(
            go.Scatter(
                x=pivot_data.index,
                y=pivot_data.sum(axis=1),
                name='Total',
                mode='lines',
                line=dict(color='#1f2937', width=2, dash='dot'),
                hovertemplate='<b>Total</b><br>Year: %{x}<br>Trials: %{y:,}<extra></extra>',
            )
        )
    
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px; color:{ANNOTATION_COLOR}'>{subtitle}</span>"
            ),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(title=None, tickmode='linear', dtick=5),
        yaxis=dict(title=y_title, tickformat=','),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.08,
            xanchor='center',
            x=0.5,
        ),
        height=height,
        template='plotly_white',
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(t=80, b=160 if note else 100, l=80, r=30),
        hovermode='x unified',
    )
    
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.32,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_stacked_area_chart(
    pivot_data: pd.DataFrame,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    colors: Optional[dict] = None,
    height: int = 500,
    normalize: bool = True,
) -> go.Figure:
    """
    Create a stacked area chart for composition over time.
    
    Parameters:
    -----------
    pivot_data : DataFrame with index=year, columns=categories, values=counts
    title : Main title
    subtitle : Subtitle
    note : Optional footnote
    colors : Dict mapping column names to colors
    height : Figure height
    normalize : If True, show as 100% stacked (proportions); if False, show absolute values
    
    Returns:
    --------
    Plotly Figure object
    """
    fig = go.Figure()
    
    colors = colors or {}
    
    # Calculate row totals for hover (cohort size)
    row_totals = pivot_data.sum(axis=1)
    
    # Normalize to percentages if requested
    if normalize:
        plot_data = pivot_data.div(row_totals, axis=0) * 100
        y_title = None  # 0-100% is self-explanatory
    else:
        plot_data = pivot_data
        y_title = 'Number of Trials'
    
    # Helper to add opacity to hex color
    def add_opacity(hex_color: str, opacity: float = 0.75) -> str:
        """Convert hex color to rgba with opacity."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f'rgba({r},{g},{b},{opacity})'
    
    # Add traces in reverse order so first category is at bottom
    for col in reversed(plot_data.columns.tolist()):
        color = colors.get(col, DEFAULT_COLORS[list(plot_data.columns).index(col) % len(DEFAULT_COLORS)])
        fill_color = add_opacity(color, 0.75)  # Reduce opacity for less visual dominance
        
        # Build custom hover with cohort N
        if normalize:
            customdata = list(zip(pivot_data[col].values, row_totals.values))
            hovertemplate = f'<b>{col}</b><br>%{{y:.1f}}% (n=%{{customdata[0]:,}} of %{{customdata[1]:,}})<extra></extra>'
        else:
            customdata = None
            hovertemplate = f'<b>{col}</b><br>Year: %{{x}}<br>%{{y:,}}<extra></extra>'
        
        fig.add_trace(
            go.Scatter(
                x=plot_data.index,
                y=plot_data[col],
                name=col,
                mode='lines',
                line=dict(width=0.5, color=color),
                stackgroup='one',
                groupnorm='percent' if normalize else None,
                fillcolor=fill_color,
                customdata=customdata,
                hovertemplate=hovertemplate,
            )
        )
    
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px; color:{ANNOTATION_COLOR}'>{subtitle}</span>"
            ),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(title=None, tickmode='linear', dtick=5),
        yaxis=dict(
            title=y_title,
            ticksuffix='%' if normalize else '',
            range=[0, 100] if normalize else None,
        ),
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.08,
            xanchor='center',
            x=0.5,
            traceorder='reversed',  # Match visual stacking order
        ),
        height=height,
        template='plotly_white',
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(t=80, b=160 if note else 100, l=80, r=30),
        hovermode='x unified',
    )
    
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.32,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_temporal_heatmap(
    pivot_data: pd.DataFrame,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    height: int = 500,
    colorscale: Optional[list] = None,
) -> go.Figure:
    """
    Create a heatmap for temporal trends by category.
    
    Parameters:
    -----------
    pivot_data : DataFrame with index=category, columns=years, values=counts
    title : Main title
    subtitle : Subtitle
    note : Optional footnote
    height : Figure height
    colorscale : Plotly colorscale
    
    Returns:
    --------
    Plotly Figure object
    """
    colorscale = colorscale or COLORSCALE
    
    # Cap at p95 for visibility (avoids outliers washing out the scale)
    z = pivot_data.to_numpy()
    zmax = float(np.percentile(z[z > 0], 95)) if (z > 0).any() else 1.0
    
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=pivot_data.columns.tolist(),
            y=pivot_data.index.tolist(),
            zmin=0,
            zmax=zmax,
            colorscale=colorscale,
            xgap=1,
            ygap=2,
            showscale=True,
            colorbar=dict(title='Studies', thickness=15),
            hovertemplate='<b>%{y}</b><br>Year: %{x}<br>Studies: %{z:,}<extra></extra>',
        )
    )
    
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px; color:{ANNOTATION_COLOR}'>{subtitle}</span>"
            ),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(title=None, tickmode='linear', dtick=5, tickangle=0),
        yaxis=dict(title=None, tickfont=dict(size=11), autorange='reversed'),
        height=height,
        template='plotly_white',
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(t=80, b=140 if note else 60, l=180, r=80),
    )
    
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.22,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_annotated_heatmap(
    pivot_data: pd.DataFrame,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    height: int = 600,
    colorscale: Optional[list] = None,
    show_colorbar: bool = False,
    x_tickangle: int = -30,
) -> go.Figure:
    """
    Create a heatmap with value annotations in each cell.
    
    Ideal for Phase × Status cross-tabulations where exact counts matter.
    
    Parameters:
    -----------
    pivot_data : DataFrame with index=row labels, columns=column labels, values=counts
    title : Main title
    subtitle : Subtitle
    note : Optional footnote
    height : Figure height
    colorscale : Plotly colorscale
    show_colorbar : Whether to show the color scale bar
    x_tickangle : Angle for x-axis tick labels
    
    Returns:
    --------
    Plotly Figure object
    """
    colorscale = colorscale or COLORSCALE
    
    # Cap at p95 for visibility
    z = pivot_data.to_numpy()
    zmax = float(np.percentile(z[z > 0], 95)) if (z > 0).any() else 1.0
    
    # Build cell annotations
    annotations = []
    for row in pivot_data.index:
        for col in pivot_data.columns:
            val = pivot_data.loc[row, col]
            if val > 0:
                annotations.append(
                    dict(
                        x=col,
                        y=row,
                        text=f"{int(val):,}",
                        showarrow=False,
                        font=dict(
                            size=11,
                            color='white' if val >= zmax * 0.6 else FONT_COLOR,
                            family=FONT_FAMILY,
                        ),
                    )
                )
    
    fig = go.Figure(
        data=go.Heatmap(
            z=z,
            x=pivot_data.columns.tolist(),
            y=pivot_data.index.tolist(),
            zmin=0,
            zmax=zmax,
            colorscale=colorscale,
            xgap=1,
            ygap=1,
            showscale=show_colorbar,
            hovertemplate='<b>%{y}</b><br>%{x}: %{z:,}<extra></extra>',
        )
    )
    
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title}</b><br>"
                f"<span style='font-size:12px; color:{ANNOTATION_COLOR}'>{subtitle}</span>"
            ),
            x=0.5,
            xanchor='center',
        ),
        xaxis=dict(tickangle=x_tickangle, tickfont=dict(size=11)),
        yaxis=dict(autorange='reversed', tickfont=dict(size=11)),
        annotations=annotations,
        height=height,
        template='plotly_white',
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(t=80, b=180 if note else 100, l=120, r=30),
    )
    
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.35,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig
