# pages/project_Reports.py
import streamlit as st

import dashboard.database.alerts_db as alerts
import dashboard.database.processor_db as processor_db  # noqa: E402
import dashboard.projects as projects
from dashboard import sh_functions as helper


def display_projects(selected_project_id):
    # Projects
    st.title("Projects")
list_of_projects = projects.load_project_list(
    force_reload=True, download_if_missing=True
)
titles = [""] + [p["title"] for p in list_of_projects]
option = st.selectbox("Select project", (titles))

if option != "":
    selected = [p for p in list_of_projects if p["title"] == option][0]
    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 25px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    # Project Attributes
    st.caption("Project Attributes")
    col1, col2, col3 = st.columns(3)
    col1.metric("ID", str(selected["id"]))
    st.markdown("Title : " + str(selected["title"]))
    st.markdown("Model : " + str(selected["language_model"]))
    st.divider()

    # Project Statistics
    unposted_above_story_count = processor_db.unposted_above_story_count(selected["id"])
    posted_above_story_count = processor_db.posted_above_story_count(selected["id"])
    below_story_count = processor_db.below_story_count(selected["id"])
    try:
        above_threshold_pct = (
            100
            * (unposted_above_story_count + posted_above_story_count)
            / below_story_count
        )
    except ZeroDivisionError:
        above_threshold_pct = 100

    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 25px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    st.caption("Statistics")
    col1, col2 = st.columns(2)
    col1.metric("Average Above Threshold Percentage", above_threshold_pct)
    col2.metric("Unposted Above Threshold Stories", unposted_above_story_count)
    col3, col4 = st.columns(2)
    col3.metric("Posted Above Threshold Stories", posted_above_story_count)
    col4.metric("Below Threshold Stories", below_story_count)
    st.divider()

    # Model Scores
    st.subheader("Model Scores")
    helper.draw_model_scores(project_id=selected["id"])
    st.divider()

    st.subheader("Above Threshold Stories")
    # by posted day
    st.caption("Platform Stories by Posted Day")
    helper.draw_graph(processor_db.stories_by_posted_day, selected["id"])
    st.divider()
    # History (by discovery date)
    st.subheader("History")
    st.caption("Platform Stories by Published Day")
    helper.draw_graph(processor_db.stories_by_published_day, selected["id"])
    st.caption("Platform Stories by Discovery Day")
    helper.draw_graph(processor_db.stories_by_processed_day, selected["id"])
    st.caption("Platform Stories by Discovery Day")
    helper.story_results_graph(selected["id"])
    st.divider()

    # Add a section for Email-Alerts database visualizations
    st.title("Email-Alerts Database")

    # Total story count in Email-Alerts
    total_email_alerts_story_count = alerts.total_story_count()
    st.subheader("Total Story Count in Email-Alerts Database")
    st.write(f"Total Stories: {total_email_alerts_story_count}")

    # Top 10 media sources/domains by story volume
    st.subheader("Top 10 Media Sources/Domains by Story Volume")
    top_media_sources = alerts.top_media_sources_by_story_volume()
    st.write(top_media_sources)

    # Email-Alerts Story volume by publication date
    st.subheader("Story Volume by Publication Date (Email-Alerts Database)")
    email_alerts_publication_chart = alerts.email_alerts_stories_by_date_column('publish_date')
    # Visualize the chart using Altair or other plotting libraries
    st.write(email_alerts_publication_chart)

    # Email-Alerts Story volume by discovery/creation date
    st.subheader("Story Volume by Discovery/Creation Date (Email-Alerts Database)")
    email_alerts_discovery_chart = alerts.email_alerts_stories_by_date_column('created_at')
    # Visualize the chart using Altair or other plotting libraries
    st.write(email_alerts_discovery_chart)