import altair as altair
import pandas as pd
import streamlit as st

import dashboard.database.processor_db as processor_db
from dashboard import PLATFORMS


def draw_graph(func, project_id=None, above_threshold=None):
    """
    Draw a graph based on data returned by a provided function from processor_db.

    Parameters:
        project_id (int, optional): The project ID (default is None).
        above_threshold (bool, optional): Filter results for above-threshold stories (default is None).

    Returns:
        None
    """
    df_list = []
    for p in PLATFORMS:
        # Pass the above_threshold parameter to the processor_db function
        results = func(
            project_id=project_id, platform=p, above_threshold=above_threshold
        )
        df = pd.DataFrame(results)
        df["platform"] = p
        df_list.append(df)

    chart = pd.concat(df_list)
    bar_chart = (
        altair.Chart(chart)
        .mark_bar()
        .encode(
            x=altair.X("day", axis=altair.Axis(format="%m-%d")),
            y="stories",
            color="platform",
            size=altair.SizeValue(8),
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)
    return


def alerts_draw_graph(func, project_id=None):
    df_list = []
    results = func(project_id=project_id)
    df = pd.DataFrame(results)
    df_list.append(df)

    chart_data = df.groupby("day")["stories"].sum().reset_index()

    bar_chart = (
        altair.Chart(chart_data)
        .mark_bar()
        .encode(
            x=altair.X("day:T", axis=altair.Axis(title="Date", format="%m-%d")),
            y=altair.Y("stories:Q", axis=altair.Axis(title="Story Count")),
            size=altair.SizeValue(8),
        )
    )

    st.altair_chart(bar_chart, use_container_width=True)
    return


def draw_bar_chart_sources(func, project_id=None, limit=10):
    """
    Draw a horizontal bar chart for media sources using the specified function.
    """
    results = func(project_id=project_id, limit=limit)
    df = pd.DataFrame(results)

    bar_chart = (
        altair.Chart(df)
        .mark_bar()
        .encode(
            x=altair.X("story_count:Q", title="Story Count"),
            y=altair.Y("media_name:N", title="Media Source"),
            color=altair.Color(
                "media_name:N", scale=altair.Scale(scheme="category20b")
            ),
            tooltip=["media_name:N", "story_count:Q"],
        )
        .properties(width=600)
        .interactive()
    )

    st.altair_chart(bar_chart, use_container_width=True)
    return


def draw_model_scores(project_id):
    Scores = [
        entry.values() for entry in processor_db.project_binned_model_scores(project_id)
    ]
    chart = pd.DataFrame(Scores, columns=["Scores", "Number of Stories"])

    # Convert 'scores' column to string type
    chart["Scores"] = chart["Scores"].astype(str)

    # Sort the 'scores' column in descending order
    chart = chart.sort_values("Scores", ascending=False)

    bar_chart = (
        altair.Chart(chart)
        .mark_bar()
        .encode(
            x=altair.X("Scores", sort=None, axis=altair.Axis(labelAngle=0)),
            y="Number of Stories",
            size=altair.SizeValue(35),
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)
    return


def story_results_graph(project_id=None):
    a = processor_db.stories_by_processed_day(
        project_id=project_id, above_threshold=True
    )
    b = processor_db.stories_by_processed_day(
        project_id=project_id, above_threshold=False
    )
    df_list = []
    a = pd.DataFrame(a)
    a["Threshold"] = "Above"
    b = pd.DataFrame(b)
    b["Threshold"] = "Below"
    df_list.append(a)
    df_list.append(b)
    chart = pd.concat(df_list)
    bar_chart = (
        altair.Chart(chart)
        .mark_bar()
        .encode(
            x=altair.X("day", axis=altair.Axis(format="%m-%d")),
            y="stories",
            color="Threshold",
            size=altair.SizeValue(8),
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)
    return


def clean_title(title):
    cleaned_title = " ".join(
        word.capitalize() for word in title.replace("-", " ").replace("_", " ").split()
    )
    return cleaned_title


def extract_story_title(url):
    parts = url.split("/")

    if len(parts[-1]) > 0:
        return clean_title(parts[-1])
    else:
        return clean_title(parts[-2])


def latest_stories(stories):
    data = []
    for s in stories:
        data.append(
            {
                "ID": s.get("stories_id", ""),
                "Source": s.get("source", ""),
                "Published Date": str(s.get("published_date", "")),
                "URL": f"{s.get('url', '')}",
                "Model Score": s.get("model_score", ""),
            }
        )

    # Create a DataFrame with clickable URLs & Separate titles
    df = pd.DataFrame(data)
    df["Story Headline"] = df["URL"].apply(extract_story_title)

    column_order = [
        "ID",
        "Story Headline",
        "Model Score",
        "URL",
        "Source",
        "Published Date",
    ]

    st.dataframe(
        df[column_order],
        column_config={
            "URL": st.column_config.LinkColumn("URL - Double-Click to open")
        },
        hide_index=True,
        use_container_width=True,
    )
