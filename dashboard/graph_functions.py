import altair as altair
import pandas as pd
import streamlit as st
from typing import List

import dashboard.database.processor_db as processor_db
from dashboard import PLATFORMS


def _to_altair_datetime(original_datetime):
    """Convert a pandas datetime to an Altair datetime object.
       Source: @jakevdp (https://github.com/vega/altair/issues/1005#issuecomment-403237407)
    """
    python_datetime = pd.to_datetime(original_datetime)
    return altair.DateTime(year=python_datetime.year, month=python_datetime.month, date=python_datetime.day,
                           hours=python_datetime.hour, minutes=python_datetime.minute, seconds=python_datetime.second,
                           milliseconds=0.001 * python_datetime.microsecond)


def _get_updated_domain(min_date: str) -> List[altair.DateTime]:
    """
    Generate time domain from min_date to current date.
    """
    end_date = pd.Timestamp.today()
    domain = [_to_altair_datetime(min_date), _to_altair_datetime(end_date)]
    return domain


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

    # concatenate all the data into a single dataframe
    chart = pd.concat(df_list)

    # Define the bar chart
    bar_chart = (
        altair.Chart(chart)
        .mark_bar()
        .encode(
            x=altair.X('day:T', axis=altair.Axis(title="Date", format="%m-%d"),
                       scale=altair.Scale(domain=_get_updated_domain(chart['day'].min()))),
            y=altair.Y('stories:Q', axis=altair.Axis(title="Story Count")),
            color=altair.Color('platform:N', legend=altair.Legend(title='Platform')),
            size=altair.SizeValue(8)
        )
    )

    st.altair_chart(bar_chart, use_container_width=True)
    return


def alerts_draw_graph(func, project_id=None):
    # fetch our data
    df_list = []
    results = func(project_id=project_id)
    df = pd.DataFrame(results)
    df_list.append(df)

    # concatenate all the data into a single dataframe
    chart = df.groupby("day")["stories"].sum().reset_index()

    # create the bar chart
    bar_chart = (
        altair.Chart(chart)
        .mark_bar()
        .encode(
            x=altair.X('day:T', scale=altair.Scale(domain=_get_updated_domain(chart['day'].min())),
                       axis=altair.Axis(title="Date", format="%m-%d")),
            y=altair.Y('stories:Q', axis=altair.Axis(title='Story Count')),
            size=altair.SizeValue(8)
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
    scores = [
        entry.values() for entry in processor_db.project_binned_model_scores(project_id)
    ]
    chart = pd.DataFrame(scores, columns=["Scores", "Number of Stories"])

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
    # Get data for above and below threshold
    a = processor_db.stories_by_processed_day(
        project_id=project_id, above_threshold=True
    )
    b = processor_db.stories_by_processed_day(
        project_id=project_id, above_threshold=False
    )

    # Convert to DataFrame and add threshold labels
    df_list = []
    a = pd.DataFrame(a)
    a["Threshold"] = "Above"
    b = pd.DataFrame(b)
    b["Threshold"] = "Below"
    df_list.append(a)
    df_list.append(b)

    # concatenate all the data into a single dataframe and update to desired domain
    chart = pd.concat(df_list)

    # create the bar chart
    bar_chart = (
        altair.Chart(chart)
        .mark_bar()
        .encode(
            x=altair.X('day:T', scale=altair.Scale(domain=_get_updated_domain(chart['day'].min())),
                       axis=altair.Axis(title="Date", format="%m-%d")),
            y=altair.Y('stories:Q', axis=altair.Axis(title="Story Count")),
            color=altair.Color('Threshold:N', legend=altair.Legend(title='Threshold')),
            size=altair.SizeValue(8)
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


def latest_articles(articles):
    data = []
    for a in articles:
        data.append({
            "id": a.get("id", ""),
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "url": a.get("url", ""),
            "publish_date": str(a.get("publish_date", "")),
        })

    df = pd.DataFrame(data)

    # Reorder columns
    column_order = ["id", "title", "source", "url", "publish_date"]
    df = df[column_order]

    # Create column configurations
    column_config = {
        "url": st.column_config.LinkColumn()
    }

    # Display DataFrame with Streamlit
    st.dataframe(
        df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )


def event_counts_draw_graph(func, project_id=None, limit=45):
    """
    Draw a graph of unique event counts by creation date.
    """
    # Fetch data using the function
    results = func(project_id=project_id, limit=limit)
    chart = pd.DataFrame(results)

    # Create the bar chart
    bar_chart = (
        altair.Chart(chart)
        .mark_bar(color='#FA8072')
        .encode(
            x=altair.X('day:T', scale=altair.Scale(domain=_get_updated_domain(chart['day'].min())),
                       axis=altair.Axis(title="Date", format="%m-%d")),
            y=altair.Y('unique_event_count:Q', axis=altair.Axis(title='Unique Event Count')),
            size=altair.SizeValue(8)
        )
    )

    st.altair_chart(bar_chart, use_container_width=True)
    return


def relevance_counts_chart(func, project_id=None, limit=45):
    """
    Generate a pie chart w/ percentages,showing the relevancy distribution of above_threshold stories for a specific project.
    """
    # fetch data using the function
    results = func(project_id=project_id, limit=limit)

    # prepare data
    data = pd.DataFrame([
        {"category": "TRUE", "count": results[0]['yes_count']},
        {"category": "FALSE", "count": results[0]['no_count']},
        {"category": "NULL", "count": results[0]['null_count']}
    ])


    total_count = data['count'].sum()
    data['percentage'] = (data['count'] / total_count) * 100

    # create the pie chart
    pie_chart = (
        altair.Chart(data)
        .mark_arc()
        .encode(
            theta=altair.Theta(field="percentage", type="quantitative"),
            color=altair.Color(field="category", type="nominal", legend=altair.Legend(title="Relevancy")),
            tooltip=[
                altair.Tooltip(field="category", type="nominal", title="Category"),
                altair.Tooltip(field="count", type="quantitative", title="Count"),
                altair.Tooltip(field="percentage", type="quantitative", format=".2f", title="Percentage (%)")
            ]
        )
        .properties(title="Relevance Distribution")
    )

    st.altair_chart(pie_chart, use_container_width=True)
    return
