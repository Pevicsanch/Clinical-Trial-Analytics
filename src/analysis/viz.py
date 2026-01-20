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
    include_ci: bool = True,
    ci_lower_col: str = 'ci_lower_pct',
    ci_upper_col: str = 'ci_upper_pct',
    small_n_threshold: int = 1000,
) -> pd.DataFrame:
    """
    Format a rate DataFrame for display (e.g., in Jupyter notebooks).
    
    Takes output from calc_completion_rate() and formats it for presentation:
    - Renames columns to human-readable names
    - Formats rate with 95% CI as "XX.X% [XX.X-XX.X%]"
    - Flags small sample sizes with asterisk
    
    Parameters:
    -----------
    df : DataFrame with rate metrics (from calc_completion_rate)
    factor_col : Column with factor values
    factor_name : Display name for factor column
    rate_col : Column with rate values (0-100 scale)
    n_col : Column with sample size
    completed_col : Column with completed count
    include_ci : Whether to include CI in output (default: True)
    ci_lower_col : Column with CI lower bound
    ci_upper_col : Column with CI upper bound
    small_n_threshold : Flag n below this with asterisk (default: 1000)
    
    Returns:
    --------
    Formatted DataFrame ready for display()
    """
    # Check if CI columns exist
    has_ci = ci_lower_col in df.columns and ci_upper_col in df.columns
    
    if include_ci and has_ci:
        t = df[[factor_col, n_col, completed_col, rate_col, ci_lower_col, ci_upper_col]].copy()
        # Format rate with CI: "85.6% [84.7-86.4%]"
        t['Rate [95% CI]'] = t.apply(
            lambda r: f"{r[rate_col]:.1f}% [{r[ci_lower_col]:.1f}-{r[ci_upper_col]:.1f}%]",
            axis=1
        )
        # Flag small n with asterisk
        t[n_col] = t[n_col].apply(
            lambda x: f"{x:,}*" if x < small_n_threshold else f"{x:,}"
        )
        t = t[[factor_col, n_col, completed_col, 'Rate [95% CI]']]
        t.columns = [factor_name, 'n', 'Completed', 'Rate [95% CI]']
    else:
        t = df[[factor_col, n_col, completed_col, rate_col]].copy()
        t[rate_col] = t[rate_col].apply(lambda x: f"{x:.1f}%")
        t[n_col] = t[n_col].apply(
            lambda x: f"{x:,}*" if x < small_n_threshold else f"{x:,}"
        )
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
    ci_lower_col: Optional[str] = None,
    ci_upper_col: Optional[str] = None,
) -> go.Figure:
    """
    Create a horizontal bar chart for rate/percentage metrics (e.g., completion rate).
    
    Unlike create_horizontal_bar_chart (for counts), this function:
    - Displays pre-calculated percentages directly
    - Shows sample size (n) in hover
    - Optionally shows confidence interval error bars
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
    ci_lower_col : Column with CI lower bound (0-100 scale) for error bars
    ci_upper_col : Column with CI upper bound (0-100 scale) for error bars
    
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
    
    # Prepare error bars if CI columns provided
    error_x = None
    if ci_lower_col and ci_upper_col and ci_lower_col in df.columns:
        error_x = dict(
            type='data',
            symmetric=False,
            array=df[ci_upper_col] - df[rate_col],  # Upper error
            arrayminus=df[rate_col] - df[ci_lower_col],  # Lower error
            color='rgba(0,0,0,0.4)',
            thickness=1.5,
            width=4,
        )
    
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
            error_x=error_x,
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
        margin=dict(l=150, r=80, t=80, b=130 if note else 50),
        font=dict(family=FONT_FAMILY, size=12, color=FONT_COLOR),
    )
    
    # Add note annotation (below x-axis title with proper spacing)
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.38,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_simple_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    subtitle: Optional[str] = None,
    y_title: Optional[str] = None,
    n_col: Optional[str] = None,
    height: int = 350,
    y_range: Optional[list] = None,
    color: str = '#2563eb',
) -> go.Figure:
    """
    Create a simple single-line chart.
    
    Parameters:
    -----------
    df : DataFrame with x and y columns
    x_col : Column for x-axis
    y_col : Column for y-axis values
    title : Main title
    subtitle : Optional subtitle
    y_title : Y-axis label
    n_col : Optional column with counts for hover
    height : Figure height
    y_range : Optional [min, max] for y-axis
    color : Line color
    
    Returns:
    --------
    Plotly Figure object
    """
    fig = go.Figure()
    
    hover_template = f'Year: %{{x}}<br>Rate: %{{y:.1f}}%'
    if n_col and n_col in df.columns:
        hover_template += '<br>n=%{customdata:,}'
        customdata = df[n_col]
    else:
        customdata = None
    hover_template += '<extra></extra>'
    
    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=6),
        hovertemplate=hover_template,
        customdata=customdata,
    ))
    
    title_text = f'<b>{title}</b>'
    if subtitle:
        title_text += f'<br><span style="font-size:12px;color:{ANNOTATION_COLOR}">{subtitle}</span>'
    
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor='center'),
        xaxis_title=None,
        yaxis_title=y_title,
        yaxis=dict(range=y_range) if y_range else {},
        template='plotly_white',
        height=height,
        margin=dict(l=60, r=40, t=80, b=60),
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
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


def create_stacked_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    color_map: dict,
    title: str,
    subtitle: Optional[str] = None,
    x_title: Optional[str] = None,
    y_title: Optional[str] = None,
    height: int = 400,
) -> go.Figure:
    """
    Create a stacked bar chart for composition analysis.
    
    Parameters:
    -----------
    df : DataFrame in long format with x, y, and color columns
    x_col : Column for x-axis (categories)
    y_col : Column for y-axis values (percentages)
    color_col : Column for color grouping
    color_map : Dict mapping color_col values to colors
    title : Main title
    subtitle : Optional subtitle
    x_title : X-axis label
    y_title : Y-axis label
    height : Figure height
    
    Returns:
    --------
    Plotly Figure object
    """
    import plotly.express as px
    
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        color_discrete_map=color_map,
        title=f'<b>{title}</b>' + (f'<br><sub>{subtitle}</sub>' if subtitle else ''),
        labels={x_col: x_title or '', y_col: y_title or ''},
        template='plotly_white',
        height=height,
    )
    
    fig.update_layout(
        barmode='stack',
        legend=dict(
            title=color_col,
            orientation='h',
            y=-0.15,
            x=0.5,
            xanchor='center'
        ),
        margin=dict(l=60, r=40, t=60, b=80),
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
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


# ============================================================
# Diagnostic Plot Functions
# ============================================================

def create_linearity_check_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    n_col: Optional[str] = None,
    title: str = 'Linearity Check: log(Enrollment) vs Log-Odds of Completion',
    height: int = 350,
    color: str = '#2563eb',
) -> go.Figure:
    """
    Create a scatter + line plot for checking linearity in the logit.
    
    Used for logistic regression diagnostics: plots empirical logit against
    a continuous predictor (binned into deciles) to verify linear relationship.
    
    Parameters:
    -----------
    data : DataFrame with x, y, and optionally n columns (binned stats)
    x_col : Column for x-axis (mean predictor value per bin)
    y_col : Column for y-axis (empirical logit per bin)
    n_col : Optional column with bin sizes for hover
    title : Chart title
    height : Figure height
    color : Line and marker color
    
    Returns:
    --------
    Plotly Figure object
    """
    fig = go.Figure()
    
    hover_template = f'{x_col}: %{{x:.2f}}<br>Empirical logit: %{{y:.2f}}'
    if n_col and n_col in data.columns:
        hover_template += '<br>n=%{customdata:,}'
        customdata = data[n_col]
    else:
        customdata = None
    hover_template += '<extra></extra>'
    
    fig.add_trace(go.Scatter(
        x=data[x_col],
        y=data[y_col],
        mode='markers+lines',
        marker=dict(size=8, color=color),
        line=dict(color=color, width=2),
        name='Empirical logit',
        customdata=customdata,
        hovertemplate=hover_template,
    ))
    
    fig.update_layout(
        title=f'<b>{title}</b>',
        xaxis_title=x_col,
        yaxis_title='Empirical Logit',
        template='plotly_white',
        height=height,
        showlegend=False,
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(l=60, r=40, t=60, b=50),
    )
    
    return fig


def create_calibration_chart(
    calibration_data: pd.DataFrame,
    predicted_col: str = 'mean_predicted',
    observed_col: str = 'observed_rate',
    n_col: str = 'n',
    title: str = 'Calibration Plot: Predicted vs Observed Completion Rate',
    height: int = 400,
) -> go.Figure:
    """
    Create a calibration plot comparing predicted probabilities to observed rates.
    
    Points sized by sample size, with a 45-degree perfect calibration line.
    
    Parameters:
    -----------
    calibration_data : DataFrame with predicted, observed, and n columns (binned)
    predicted_col : Column with mean predicted probability per bin
    observed_col : Column with observed rate per bin
    n_col : Column with sample size per bin
    title : Chart title
    height : Figure height
    
    Returns:
    --------
    Plotly Figure object
    """
    fig = go.Figure()
    
    # Calibration points
    fig.add_trace(go.Scatter(
        x=calibration_data[predicted_col],
        y=calibration_data[observed_col],
        mode='markers',
        marker=dict(
            size=calibration_data[n_col] / 50,
            color='#2563eb',
            line=dict(width=1, color='white'),
        ),
        name='Observed vs Predicted',
        hovertemplate=(
            f'Predicted: %{{x:.2f}}<br>'
            f'Observed: %{{y:.2f}}<br>'
            f'n=%{{customdata:,}}<extra></extra>'
        ),
        customdata=calibration_data[n_col],
    ))
    
    # Perfect calibration line (45-degree)
    fig.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode='lines',
        line=dict(color='#dc2626', width=2, dash='dash'),
        name='Perfect calibration',
        hoverinfo='skip',
    ))
    
    fig.update_layout(
        title=f'<b>{title}</b>',
        xaxis_title='Mean Predicted Probability',
        yaxis_title='Observed Completion Rate',
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
        template='plotly_white',
        height=height,
        showlegend=True,
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(l=60, r=40, t=60, b=50),
    )
    
    return fig


def create_cooks_distance_chart(
    cooks_d: np.ndarray,
    threshold: float,
    title: str = "Cook's Distance: Influence of Individual Observations",
    height: int = 350,
) -> go.Figure:
    """
    Create a scatter plot for Cook's distance diagnostic.
    
    Visualizes influence of individual observations on regression coefficients.
    Points are colored by Cook's D value, with a threshold line.
    
    Parameters:
    -----------
    cooks_d : Array of Cook's distance values
    threshold : Threshold value for influential observations (typically 4/n)
    title : Chart title
    height : Figure height
    
    Returns:
    --------
    Plotly Figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(len(cooks_d))),
        y=cooks_d,
        mode='markers',
        marker=dict(
            size=4,
            color=cooks_d,
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Cook's D"),
        ),
        hovertemplate="Index: %{x}<br>Cook's D: %{y:.6f}<extra></extra>",
    ))
    
    fig.add_hline(
        y=threshold,
        line_dash='dash',
        line_color='red',
        annotation_text=f'Threshold: {threshold:.6f}',
    )
    
    fig.update_layout(
        title=f'<b>{title}</b>',
        xaxis_title='Observation Index',
        yaxis_title="Cook's Distance",
        template='plotly_white',
        height=height,
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        margin=dict(l=60, r=40, t=60, b=50),
    )
    
    return fig


def create_crosstab_heatmap(
    counts: pd.DataFrame,
    pct: pd.DataFrame,
    title: str,
    subtitle: str,
    note: Optional[str] = None,
    height: int = 450,
    colorscale: str = 'Reds',
    x_title: str = '',
    y_title: str = '',
) -> go.Figure:
    """
    Create a heatmap showing counts AND percentages in each cell.
    
    Designed for crosstab analysis where both raw counts and row %
    are informative. Cell text shows "count\\n(pct%)".
    
    Parameters:
    -----------
    counts : DataFrame of counts (rows × columns)
    pct : DataFrame of row percentages (same shape as counts)
    title : Main title
    subtitle : Subtitle
    note : Optional footnote
    height : Figure height
    colorscale : Plotly colorscale name (default: 'Reds')
    x_title : X-axis title
    y_title : Y-axis title
    
    Returns:
    --------
    Plotly Figure object
    
    Example:
    --------
    >>> result = calc_crosstab_analysis(df_stopped, 'phase_group', 'failure_type')
    >>> fig = create_crosstab_heatmap(
    ...     result['counts'].drop('All'),  # Exclude margin row
    ...     result['pct_row'],
    ...     title='Failure Type by Phase',
    ...     subtitle='Row percentages',
    ... )
    """
    # Build cell annotations (count + percentage)
    annotations = []
    for i, row in enumerate(pct.index):
        for j, col in enumerate(pct.columns):
            p = pct.loc[row, col]
            c = counts.loc[row, col] if row in counts.index else 0
            annotations.append(
                dict(
                    x=j,
                    y=i,
                    text=f"{c:,}<br>({p:.0f}%)",
                    showarrow=False,
                    font=dict(
                        color='white' if p > 50 else 'black',
                        size=10,
                        family=FONT_FAMILY,
                    )
                )
            )
    
    fig = go.Figure(data=go.Heatmap(
        z=pct.values,
        x=list(pct.columns),
        y=list(pct.index),
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(title='%', len=0.6),
    ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>{title}</b><br><sub>{subtitle}</sub>',
            font=dict(size=16, family=FONT_FAMILY, color=FONT_COLOR),
        ),
        xaxis=dict(
            title=x_title,
            tickfont=dict(size=11, family=FONT_FAMILY),
        ),
        yaxis=dict(
            title=y_title,
            tickfont=dict(size=11, family=FONT_FAMILY),
            autorange='reversed',
        ),
        template='plotly_white',
        height=height,
        annotations=annotations,
        margin=dict(l=120, r=80, t=80, b=60),
    )
    
    if note:
        fig.add_annotation(
            text=note,
            xref='paper', yref='paper',
            x=0, y=-0.18,
            showarrow=False,
            align='left',
            font=dict(size=10, color=ANNOTATION_COLOR, family=FONT_FAMILY),
        )
    
    return fig


def create_distribution_comparison(
    data: pd.Series,
    log_data: pd.Series,
    title: str = "Enrollment Distribution",
    subtitle: Optional[str] = None,
    height: int = 380,
    nbins: int = 50,
) -> go.Figure:
    """
    Create side-by-side histograms comparing original and log-transformed distributions.
    
    Used to demonstrate why log-transformation is appropriate for heavy-tailed data.
    
    Parameters:
    -----------
    data : Series with original values (e.g., enrollment)
    log_data : Series with log-transformed values (e.g., log(enrollment+1))
    title : Main title
    subtitle : Optional subtitle
    height : Figure height
    nbins : Number of histogram bins
    
    Returns:
    --------
    Plotly Figure object with two subplots
    
    Example:
    --------
    >>> fig = create_distribution_comparison(
    ...     df_enr['enrollment'],
    ...     df_enr['log_enrollment'],
    ...     title='Enrollment Distribution',
    ...     subtitle=f'n = {len(df_enr):,} trials'
    ... )
    """
    from plotly.subplots import make_subplots
    
    # Calculate statistics
    median_raw = data.median()
    median_log = log_data.dropna().median()
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Original Scale', 'Log-Transformed'),
        horizontal_spacing=0.12,
    )
    
    # Original scale histogram
    fig.add_trace(
        go.Histogram(
            x=data,
            nbinsx=nbins,
            marker=dict(color=DEFAULT_COLORS[0], line=dict(width=0)),
            opacity=0.85,
            name='Enrollment',
            hovertemplate='Enrollment: %{x:,.0f}<br>Count: %{y:,}<extra></extra>',
        ),
        row=1, col=1
    )
    
    # Median line (original)
    fig.add_vline(
        x=median_raw,
        line=dict(dash='dash', color='#dc2626', width=2),
        row=1, col=1
    )
    fig.add_annotation(
        x=median_raw,
        y=1,
        yref='y domain',
        text=f'Median: {median_raw:,.0f}',
        showarrow=False,
        yshift=10,
        font=dict(size=11, color='#dc2626', family=FONT_FAMILY),
        row=1, col=1
    )
    
    # Log-transformed histogram
    fig.add_trace(
        go.Histogram(
            x=log_data.dropna(),
            nbinsx=nbins,
            marker=dict(color=DEFAULT_COLORS[2], line=dict(width=0)),
            opacity=0.85,
            name='Log(Enrollment)',
            hovertemplate='Log(enroll+1): %{x:.2f}<br>Count: %{y:,}<extra></extra>',
        ),
        row=1, col=2
    )
    
    # Median line (log)
    fig.add_vline(
        x=median_log,
        line=dict(dash='dash', color='#dc2626', width=2),
        row=1, col=2
    )
    fig.add_annotation(
        x=median_log,
        y=1,
        yref='y2 domain',
        text=f'Median: {median_log:.2f}',
        showarrow=False,
        yshift=10,
        font=dict(size=11, color='#dc2626', family=FONT_FAMILY),
        row=1, col=2
    )
    
    # Axis labels
    fig.update_xaxes(title_text='Enrollment', row=1, col=1)
    fig.update_xaxes(title_text='log(Enrollment + 1)', row=1, col=2)
    fig.update_yaxes(title_text='Frequency', row=1, col=1)
    fig.update_yaxes(title_text='Frequency', row=1, col=2)
    
    # Title
    title_text = f'<b>{title}</b>'
    if subtitle:
        title_text += f'<br><span style="font-size:12px;color:{ANNOTATION_COLOR}">{subtitle}</span>'
    
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor='center'),
        template='plotly_white',
        height=height,
        showlegend=False,
        margin=dict(l=60, r=40, t=90, b=60),
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
    )
    
    # Style subplot titles
    for annotation in fig['layout']['annotations']:
        if annotation['text'] in ['Original Scale', 'Log-Transformed']:
            annotation['font'] = dict(size=13, family=FONT_FAMILY, color=FONT_COLOR)
    
    return fig


def create_grouped_box_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    category_order: list,
    title: str,
    subtitle: Optional[str] = None,
    y_log: bool = True,
    height: int = 400,
    color: str = '#2563eb',
) -> go.Figure:
    """
    Create a simple grouped box plot for comparing distributions across categories.
    
    Designed as a visual confirmation of tabular/statistical findings, not primary evidence.
    Uses consistent single color and minimal styling.
    
    Parameters:
    -----------
    df : DataFrame with data
    x_col : Column for x-axis categories
    y_col : Column for y-axis values
    category_order : List of categories in display order (filters to only these)
    title : Main title
    subtitle : Optional subtitle
    y_log : Whether to use log scale on y-axis (default: True for skewed data)
    height : Figure height
    color : Box color (single color for all, keeps focus on pattern)
    
    Returns:
    --------
    Plotly Figure object
    
    Example:
    --------
    >>> fig = create_grouped_box_plot(
    ...     df_enr, 'phase_group', 'enrollment',
    ...     category_order=['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4'],
    ...     title='Enrollment by Phase',
    ...     subtitle='Log scale, clinical phases only'
    ... )
    """
    # Filter to specified categories only
    df_plot = df[df[x_col].isin(category_order)].copy()
    
    fig = go.Figure()
    
    for category in category_order:
        data = df_plot[df_plot[x_col] == category][y_col]
        if len(data) > 0:
            fig.add_trace(go.Box(
                y=data,
                name=category,
                marker=dict(color=color, opacity=0.6),
                line=dict(color=color),
                boxmean=False,
                showlegend=False,
                hovertemplate=f'{category}<br>Value: %{{y:,.0f}}<extra></extra>',
            ))
    
    # Title
    title_text = f'<b>{title}</b>'
    if subtitle:
        title_text += f'<br><span style="font-size:12px;color:{ANNOTATION_COLOR}">{subtitle}</span>'
    
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor='center'),
        xaxis_title=None,
        yaxis_title=y_col.replace('_', ' ').title(),
        yaxis_type='log' if y_log else 'linear',
        template='plotly_white',
        height=height,
        margin=dict(l=60, r=40, t=80, b=60),
        font=dict(family=FONT_FAMILY, color=FONT_COLOR),
        xaxis_tickangle=-30,
    )
    
    return fig
