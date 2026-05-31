"""
Diabetes Population Health — US State Choropleth Dashboard
============================================================
Interactive Streamlit dashboard visualizing CDC BRFSS state-level
diabetes metrics across the continental United States.

Pages:
  1. 🗺️  Choropleth Map    — Interactive US choropleth by metric
  2. 📊  State Rankings    — Sortable state comparison table + bar chart
  3. 🔗  Correlation       — Scatter plot matrix of risk factors
  4. 📈  Risk Profile      — Radar chart for selected state vs national avg

Run:
    streamlit run src/choropleth_dashboard.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Diabetes Population Health — US Choropleth",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    [data-testid="stMetric"] { background: #1e2130; border-radius: 8px; padding: 0.8rem; }
    .stat-good  { color: #66bb6a; font-weight: 700; }
    .stat-bad   { color: #ef5350; font-weight: 700; }
    .stat-mid   { color: #ffa726; font-weight: 700; }
    .section-hdr {
        font-size: 1.05rem; font-weight: 600; color: #e0e8ff;
        border-bottom: 2px solid #4fc3f7; padding-bottom: 0.25rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data
def load_data() -> pd.DataFrame:
    from brfss_data import generate_brfss_state_data
    return generate_brfss_state_data(seed=42)


@st.cache_data
def load_geojson():
    """Load US states GeoJSON from public CDN."""
    import urllib.request, json
    url = (
        "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/"
        "master/data/geojson/us-states.json"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


df = load_data()

from brfss_data import METRIC_CONFIG

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🗺️ Diabetes Population Health")
    st.markdown("**CDC BRFSS 2021 State-Level Data**")
    st.divider()

    page = st.radio(
        "Navigate",
        ["🗺️ Choropleth Map", "📊 State Rankings",
         "🔗 Risk Factor Correlations", "📈 State Risk Profile"],
    )

    st.divider()
    selected_metric = st.selectbox(
        "Primary Metric",
        options=list(METRIC_CONFIG.keys()),
        format_func=lambda x: METRIC_CONFIG[x]["label"],
        index=0,
    )
    cfg = METRIC_CONFIG[selected_metric]

    st.divider()
    st.caption("Data: CDC BRFSS 2021 (synthetic calibration)")
    st.caption("Population: US adults ≥ 18 years")
    st.caption("n = 50 states, ~8,500 respondents/state")

# ---------------------------------------------------------------------------
# Shared stats
# ---------------------------------------------------------------------------

metric_vals = df[selected_metric]
national_avg = cfg["national_avg"]
worst_state = df.loc[
    df[selected_metric].idxmax() if cfg["lower_is_better"] else df[selected_metric].idxmin(),
    "state"
]
best_state = df.loc[
    df[selected_metric].idxmin() if cfg["lower_is_better"] else df[selected_metric].idxmax(),
    "state"
]

# ---------------------------------------------------------------------------
# Page: Choropleth Map
# ---------------------------------------------------------------------------

if page == "🗺️ Choropleth Map":
    st.title("🗺️ US Diabetes Population Health Choropleth")
    st.markdown(f"**{cfg['label']}** — {cfg['description']}")

    # Summary metrics row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("National Average", f"{national_avg}{cfg['unit']}")
    c2.metric("Highest State", f"{metric_vals.max()}{cfg['unit']}", worst_state)
    c3.metric("Lowest State",  f"{metric_vals.min()}{cfg['unit']}", best_state)
    c4.metric("Range", f"{metric_vals.max() - metric_vals.min():.1f}{cfg['unit']}")
    c5.metric("States Above Avg",
              f"{(metric_vals > national_avg).sum() if cfg['lower_is_better'] else (metric_vals < national_avg).sum()}")

    st.divider()

    # Build choropleth
    try:
        import plotly.graph_objects as go
        import plotly.express as px

        geojson = load_geojson()

        if geojson:
            # Map state names in GeoJSON to our df
            fig = px.choropleth(
                df,
                locations="state_abbr",
                locationmode="USA-states",
                color=selected_metric,
                hover_name="state",
                hover_data={
                    "state_abbr": False,
                    selected_metric: f":.1f",
                    "diabetes_prevalence_pct": ":.1f",
                    "obesity_prevalence_pct": ":.1f",
                    "n_respondents": ":,",
                },
                color_continuous_scale=cfg["colorscale"],
                scope="usa",
                title=f"{cfg['label']} by State — CDC BRFSS 2021",
                labels={selected_metric: f"{cfg['label']} ({cfg['unit']})"},
            )
            fig.update_layout(
                geo=dict(
                    showlakes=True,
                    lakecolor="rgb(20,25,40)",
                    bgcolor="rgba(0,0,0,0)",
                    landcolor="rgb(30,36,56)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12),
                margin=dict(l=0, r=0, t=40, b=0),
                height=520,
                coloraxis_colorbar=dict(
                    title=f"{cfg['unit']}",
                    thickness=15,
                    len=0.7,
                    tickfont=dict(color="white"),
                    titlefont=dict(color="white"),
                ),
            )
            fig.update_traces(
                marker_line_color="rgba(255,255,255,0.3)",
                marker_line_width=0.5,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback: colored table if GeoJSON unavailable
            st.warning("GeoJSON unavailable (network). Showing ranked table instead.")
            _show_ranked_table(df, selected_metric, cfg)

    except ImportError:
        st.error("Install plotly: pip install plotly")

    # Bottom: top 10 / bottom 10 states
    col_worst, col_best = st.columns(2)
    sort_asc = cfg["lower_is_better"]

    with col_worst:
        label = "Highest" if cfg["lower_is_better"] else "Lowest"
        st.markdown(f'<div class="section-hdr">⚠️ {label} 10 States</div>',
                    unsafe_allow_html=True)
        worst10 = df.nlargest(10, selected_metric) if cfg["lower_is_better"] \
            else df.nsmallest(10, selected_metric)
        st.dataframe(
            worst10[["state", "state_abbr", selected_metric]].rename(
                columns={selected_metric: f"{cfg['label']} ({cfg['unit']})"}
            ).reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )

    with col_best:
        label = "Lowest" if cfg["lower_is_better"] else "Highest"
        st.markdown(f'<div class="section-hdr">✅ {label} 10 States</div>',
                    unsafe_allow_html=True)
        best10 = df.nsmallest(10, selected_metric) if cfg["lower_is_better"] \
            else df.nlargest(10, selected_metric)
        st.dataframe(
            best10[["state", "state_abbr", selected_metric]].rename(
                columns={selected_metric: f"{cfg['label']} ({cfg['unit']})"}
            ).reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )

# ---------------------------------------------------------------------------
# Page: State Rankings
# ---------------------------------------------------------------------------

elif page == "📊 State Rankings":
    st.title("📊 State Rankings")
    st.markdown(f"All 50 states ranked by **{cfg['label']}**.")

    import plotly.express as px

    sort_col = selected_metric
    ascending = not cfg["lower_is_better"]  # show worst first for "lower is better"
    ranked = df.sort_values(sort_col, ascending=ascending).reset_index(drop=True)
    ranked["rank"] = ranked.index + 1
    ranked["vs_national"] = (ranked[sort_col] - national_avg).round(1)
    ranked["vs_national_str"] = ranked["vs_national"].apply(
        lambda x: f"+{x}" if x > 0 else str(x)
    )

    # Bar chart
    fig_bar = px.bar(
        ranked,
        x="state_abbr",
        y=selected_metric,
        color=selected_metric,
        color_continuous_scale=cfg["colorscale"],
        hover_name="state",
        labels={selected_metric: f"{cfg['label']} ({cfg['unit']})"},
        title=f"All States — {cfg['label']}",
    )
    fig_bar.add_hline(
        y=national_avg,
        line_dash="dash",
        line_color="white",
        annotation_text=f"National avg: {national_avg}{cfg['unit']}",
        annotation_font_color="white",
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,17,23,1)",
        font=dict(color="white"),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(tickfont=dict(size=9), gridcolor="#2d3250"),
        yaxis=dict(gridcolor="#2d3250"),
        coloraxis_showscale=False,
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Full ranked table
    display_cols = ["rank", "state", "state_abbr"] + list(METRIC_CONFIG.keys())
    display_cols = [c for c in display_cols if c in ranked.columns]
    st.dataframe(
        ranked[display_cols],
        use_container_width=True,
        height=450,
        column_config={
            "rank": st.column_config.NumberColumn("Rank", width="small"),
            "state": st.column_config.TextColumn("State"),
            "state_abbr": st.column_config.TextColumn("Abbr", width="small"),
            "diabetes_prevalence_pct":    st.column_config.NumberColumn("Diabetes %",    format="%.1f"),
            "prediabetes_prevalence_pct": st.column_config.NumberColumn("Prediabetes %", format="%.1f"),
            "obesity_prevalence_pct":     st.column_config.NumberColumn("Obesity %",     format="%.1f"),
            "physical_inactivity_pct":    st.column_config.NumberColumn("Inactivity %",  format="%.1f"),
            "high_bp_prevalence_pct":     st.column_config.NumberColumn("High BP %",     format="%.1f"),
            "uninsured_pct":              st.column_config.NumberColumn("Uninsured %",   format="%.1f"),
            "hba1c_controlled_pct":       st.column_config.NumberColumn("HbA1c Ctrl %",  format="%.1f"),
            "diabetes_mortality_rate":    st.column_config.NumberColumn("Mortality/100K",format="%.1f"),
        }
    )

# ---------------------------------------------------------------------------
# Page: Risk Factor Correlations
# ---------------------------------------------------------------------------

elif page == "🔗 Risk Factor Correlations":
    st.title("🔗 Risk Factor Correlations")
    st.markdown("Scatter plots of diabetes prevalence vs key modifiable risk factors.")

    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    risk_factors = [
        ("obesity_prevalence_pct",      "Obesity Prevalence (%)"),
        ("physical_inactivity_pct",     "Physical Inactivity (%)"),
        ("high_bp_prevalence_pct",      "Hypertension Prevalence (%)"),
        ("uninsured_pct",               "Uninsured Rate (%)"),
    ]

    cols = st.columns(2)
    for i, (rf_col, rf_label) in enumerate(risk_factors):
        with cols[i % 2]:
            corr = df["diabetes_prevalence_pct"].corr(df[rf_col])
            fig_sc = px.scatter(
                df,
                x=rf_col,
                y="diabetes_prevalence_pct",
                text="state_abbr",
                trendline="ols",
                color="diabetes_prevalence_pct",
                color_continuous_scale="Reds",
                labels={
                    rf_col: rf_label,
                    "diabetes_prevalence_pct": "Diabetes Prevalence (%)",
                },
                title=f"r = {corr:.3f}",
                hover_name="state",
            )
            fig_sc.update_traces(
                textposition="top center",
                textfont=dict(size=7, color="white"),
                marker=dict(size=8),
                selector=dict(mode="markers+text"),
            )
            fig_sc.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(14,17,23,1)",
                font=dict(color="white", size=10),
                height=320,
                margin=dict(l=0, r=0, t=35, b=0),
                xaxis=dict(gridcolor="#2d3250"),
                yaxis=dict(gridcolor="#2d3250"),
                coloraxis_showscale=False,
                showlegend=False,
            )
            st.plotly_chart(fig_sc, use_container_width=True)

    # Correlation heatmap
    st.markdown('<div class="section-hdr">Correlation Matrix — All Metrics</div>',
                unsafe_allow_html=True)
    numeric_cols = list(METRIC_CONFIG.keys())
    corr_matrix = df[numeric_cols].corr().round(3)
    short_labels = [METRIC_CONFIG[c]["label"].replace(" Prevalence", "").replace(" Rate", "")
                    for c in numeric_cols]

    fig_heat = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=short_labels,
        y=short_labels,
        colorscale="RdBu_r",
        zmid=0,
        zmin=-1, zmax=1,
        text=corr_matrix.values.round(2),
        texttemplate="%{text}",
        textfont={"size": 9},
        hovertemplate="x: %{x}<br>y: %{y}<br>r = %{z:.3f}<extra></extra>",
    ))
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(14,17,23,1)",
        font=dict(color="white", size=9),
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(tickangle=-35),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ---------------------------------------------------------------------------
# Page: State Risk Profile
# ---------------------------------------------------------------------------

elif page == "📈 State Risk Profile":
    st.title("📈 State Risk Profile")
    st.markdown("Radar chart comparing a selected state to the national average.")

    import plotly.graph_objects as go

    selected_state = st.selectbox(
        "Select State",
        options=sorted(df["state"].tolist()),
        index=sorted(df["state"].tolist()).index("Mississippi"),
    )

    state_row = df[df["state"] == selected_state].iloc[0]

    # Radar metrics (normalize to 0–100 percentile rank)
    radar_metrics = [
        "diabetes_prevalence_pct",
        "obesity_prevalence_pct",
        "physical_inactivity_pct",
        "high_bp_prevalence_pct",
        "uninsured_pct",
        "diabetes_mortality_rate",
        "prediabetes_prevalence_pct",
    ]
    radar_labels = [METRIC_CONFIG[m]["label"].replace(" Prevalence", "")
                    .replace(" Rate", "").replace(" Inactivity", " Inactiv.")
                    for m in radar_metrics]

    # Percentile rank (higher percentile = worse for "lower is better" metrics)
    state_pct = []
    national_pct = []
    for m in radar_metrics:
        rank = (df[m] <= state_row[m]).mean() * 100
        nat_rank = 50.0  # National average always at 50th percentile
        state_pct.append(round(rank, 1))
        national_pct.append(nat_rank)

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=state_pct + [state_pct[0]],
        theta=radar_labels + [radar_labels[0]],
        fill="toself",
        name=selected_state,
        line=dict(color="#ef5350", width=2),
        fillcolor="rgba(239,83,80,0.15)",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=national_pct + [national_pct[0]],
        theta=radar_labels + [radar_labels[0]],
        fill="toself",
        name="National Average (50th pct)",
        line=dict(color="#4fc3f7", width=2, dash="dash"),
        fillcolor="rgba(79,195,247,0.08)",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(color="white", size=9),
                gridcolor="#2d3250",
            ),
            angularaxis=dict(tickfont=dict(color="white", size=10)),
            bgcolor="rgba(14,17,23,1)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(font=dict(color="white")),
        title=dict(
            text=f"{selected_state} vs National Average<br>"
                 f"<sup>Percentile rank — higher = worse outcome</sup>",
            font=dict(color="white", size=14),
        ),
        height=500,
        margin=dict(l=60, r=60, t=80, b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # State metrics vs national avg table
    st.markdown('<div class="section-hdr">Metric Comparison</div>',
                unsafe_allow_html=True)
    rows = []
    for m in METRIC_CONFIG:
        val = state_row[m]
        nat = METRIC_CONFIG[m]["national_avg"]
        diff = val - nat
        lower_better = METRIC_CONFIG[m]["lower_is_better"]
        worse = (diff > 0 and lower_better) or (diff < 0 and not lower_better)
        rows.append({
            "Metric": METRIC_CONFIG[m]["label"],
            f"{selected_state}": f"{val:.1f}{METRIC_CONFIG[m]['unit']}",
            "National Avg": f"{nat:.1f}{METRIC_CONFIG[m]['unit']}",
            "Difference": f"{'+' if diff > 0 else ''}{diff:.1f}{METRIC_CONFIG[m]['unit']}",
            "Status": "⚠️ Worse" if worse else "✅ Better",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Population summary
    st.divider()
    n_worse = sum(1 for r in rows if r["Status"] == "⚠️ Worse")
    n_better = sum(1 for r in rows if r["Status"] == "✅ Better")
    col1, col2, col3 = st.columns(3)
    col1.metric("Metrics Worse Than National Avg", n_worse, delta=None)
    col2.metric("Metrics Better Than National Avg", n_better, delta=None)
    col3.metric(
        "Diabetes Prevalence Percentile",
        f"{(df['diabetes_prevalence_pct'] <= state_row['diabetes_prevalence_pct']).mean()*100:.0f}th",
    )
