from __future__ import annotations

import altair as alt
import pandas as pd


TEAL = "#087F8C"
NAVY = "#163B65"
BLUE = "#5C91A8"
AMBER = "#F0A202"
RED = "#C44536"
MUTED = "#627D98"
BORDER = "#D9E2EC"


def _style(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(
            labelColor=MUTED,
            titleColor=MUTED,
            domain=False,
            tickColor=BORDER,
        )
    )


def horizontal_bar(
    data: pd.DataFrame,
    category: str,
    value: str,
    *,
    color: str = TEAL,
    height: int = 280,
    value_title: str = "Amount (EUR)",
) -> alt.Chart:
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=5, color=color)
        .encode(
            y=alt.Y(
                f"{category}:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelLimit=150),
            ),
            x=alt.X(
                f"{value}:Q",
                title=value_title,
                axis=alt.Axis(format="~s", grid=False),
            ),
            tooltip=[
                alt.Tooltip(f"{category}:N", title="Category"),
                alt.Tooltip(f"{value}:Q", format=",.0f", title=value_title),
            ],
        )
        .properties(height=height)
    )
    return _style(chart)


def aging_bar(data: pd.DataFrame) -> alt.Chart:
    order = ["current", "1-30 days", "31-60 days", "60+ days"]
    plot_data = data.copy()
    plot_data["aging_bucket"] = pd.Categorical(
        plot_data["aging_bucket"], order, ordered=True
    )
    chart = (
        alt.Chart(plot_data)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("aging_bucket:N", sort=order, title=None),
            y=alt.Y(
                "amount_eur:Q",
                title="Outstanding (EUR)",
                axis=alt.Axis(format="~s", grid=False),
            ),
            color=alt.Color(
                "aging_bucket:N",
                scale=alt.Scale(
                    domain=order,
                    range=["#9FB3C8", BLUE, AMBER, RED],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("aging_bucket:N", title="Age"),
                alt.Tooltip("amount_eur:Q", format=",.0f", title="EUR"),
            ],
        )
        .properties(height=290)
    )
    return _style(chart)


def quality_trend(data: pd.DataFrame) -> alt.Chart:
    chart = (
        alt.Chart(data)
        .mark_line(point=True, color=TEAL, strokeWidth=3)
        .encode(
            x=alt.X("completed_at:T", title=None),
            y=alt.Y(
                "quality_score:Q",
                title="Quality score",
                scale=alt.Scale(zero=False),
            ),
            tooltip=[
                alt.Tooltip("completed_at:T", title="Run"),
                alt.Tooltip("quality_score:Q", format=".1f"),
            ],
        )
        .properties(height=260)
    )
    return _style(chart)
