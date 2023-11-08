# utils/shared_functions.py
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


def latest_stories(stories):
    ids = [""] + [s.stories_id for s in stories]
    story_id = st.selectbox("Select story", (ids))
    if story_id != "":
        s = [story for story in stories_above if story.stories_id == story_id][0]  # noqa: F821
        st.markdown("ID : " + str(s.stories_id))
        st.markdown("Source: " + str(s.source))
        st.markdown("Published Date: " + str(s.published_date))
        st.markdown("URL: [link](story.url)")
        st.markdown("Model Score: " + str(s.model_score))
    return