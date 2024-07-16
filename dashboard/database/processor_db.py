import datetime as dt
import logging
from typing import Dict, List
import csv
import base64
from io import StringIO

import psycopg2
import psycopg2.extras
import streamlit as st

from dashboard import PROCESSOR_DB_URI

logger = logging.getLogger(__name__)


@st.cache_resource  # so it only run once
def init_connection():
    return psycopg2.connect(PROCESSOR_DB_URI)


db_conn = init_connection()


@st.cache_data(ttl=6 * 60 * 60)  # so we cache data for a while
def _run_query(query: str) -> List[Dict]:
    dict_cursor = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cursor.execute(query)
    results = dict_cursor.fetchall()
    return results


def recent_stories(project_id: int, above_threshold: bool, limit: int = 5) -> List:
    """
    UI: show a list of the most recent stories we have processed
    """
    earliest_date = dt.date.today() - dt.timedelta(days=80)
    sql = """
        SELECT * FROM stories WHERE
            project_id={} AND above_threshold={} AND published_date >= '{}'::DATE
            ORDER BY RANDOM() DESC LIMIT {}
    """.format(
        project_id, above_threshold, earliest_date, limit
    )
    return _run_query(sql)


def _stories_by_date_col(
    column_name: str,
    project_id: int = None,
    platform: str = None,
    above_threshold: bool = None,
    is_posted: bool = None,
    limit: int = None,
) -> List:
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    clauses = []
    if project_id is not None:
        clauses.append("(project_id={})".format(project_id))
    if platform is not None:
        clauses.append("(source='{}')".format(platform))
    if above_threshold is not None:
        clauses.append(
            "(above_threshold is {})".format("True" if above_threshold else "False")
        )
    if is_posted is not None:
        clauses.append("(posted_date {} Null)".format("is not" if is_posted else "is"))
    query = (
        "select " + column_name + "::date as day, count(1) as stories from stories "
        "where ("
        + column_name
        + " is not Null) and ("
        + column_name
        + " >= '{}'::DATE) AND {} "
        "group by 1 order by 1 DESC".format(earliest_date, " AND ".join(clauses))
    )
    return _run_query(query)


def stories_by_posted_day(
    project_id: int = None,
    platform: str = None,
    above_threshold: bool = None,
    is_posted: bool = None,
    limit: int = 85,
) -> List:
    return _stories_by_date_col(
        "posted_date", project_id, platform, above_threshold, is_posted, limit
    )


def stories_by_processed_day(
    project_id: int = None,
    platform: str = None,
    above_threshold: bool = None,
    is_posted: bool = None,
    limit: int = 85,
) -> List:
    return _stories_by_date_col(
        "processed_date", project_id, platform, above_threshold, is_posted, limit
    )


def stories_by_published_day(
    project_id: int = None,
    platform: str = None,
    above_threshold: bool = None,
    is_posted: bool = None,
    limit: int = 85,
) -> List:
    return _stories_by_date_col(
        "published_date", project_id, platform, above_threshold, is_posted, limit
    )


@st.cache_data(ttl=12 * 60 * 60)  # Cache data for 12 hours
def fetch_stories_by_project_id(project_id: int) -> List[Dict]:
    """
    Fetch all stories for a given project_id.
    """
    db_conn = init_connection()
    dict_cursor = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    query = """
        SELECT * FROM stories
        WHERE project_id={} 
    """.format(project_id)

    dict_cursor.execute(query)
    results = dict_cursor.fetchall()
    dict_cursor.close()
    db_conn.close()

    return results


# Function to download CSV file
def download_csv(project_id: int):
    stories_data = fetch_stories_by_project_id(project_id)

    if stories_data:
        # Convert data to CSV format
        csv_str = StringIO()
        csv_writer = csv.DictWriter(csv_str, fieldnames=stories_data[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(stories_data)

        # Generate download link
        b64 = base64.b64encode(csv_str.getvalue().encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="project{project_id}_data.csv">Download CSV File</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("No data found for the project ID.")


def _run_count_query(query: str) -> int:
    data = _run_query(query)
    return data[0]["count"]


def unposted_above_story_count(project_id: int, limit: int = None) -> int:
    """
    UI: How many stories about threshold have *not* been sent to the main server (should be zero!).
    """
    date_clause = "(posted_date is Null)"
    if limit:
        earliest_date = dt.date.today() - dt.timedelta(days=limit)
        date_clause += " AND (posted_date >= '{}'::DATE)".format(earliest_date)
    query = "select count(1) from stories where project_id={} and above_threshold is True and {}".format(
        project_id, date_clause
    )
    return _run_count_query(query)


def posted_above_story_count(project_id: int) -> int:
    """
    UI: How many stories above threshold have we sent to the main server (like all should be)
    :param project_id:
    :return:
    """
    query = (
        "select count(1) from stories "
        "where project_id={} and posted_date is not Null and above_threshold is True".format(
            project_id
        )
    )
    return _run_count_query(query)


def below_story_count(project_id: int) -> int:
    """
    UI: How many stories total were below threshold (should be same as uposted_stories)
    :param project_id:
    :return:
    """
    query = "select count(1) from stories where project_id={} and above_threshold is False".format(
        project_id
    )
    return _run_count_query(query)


def unposted_stories(project_id: int, limit: int):
    """
    How many stories were not posted to the main server (should be same as below_story_count)
    :return:
    """
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    query = (
        "select * from stories "
        "where project_id={} and posted_date is Null and (posted_date >= '{}'::DATE) and above_threshold is True".format(
            project_id, earliest_date
        )
    )
    return _run_query(query)


def project_binned_model_scores(project_id: int) -> List:
    query = """
        select ROUND(CAST(model_score as numeric), 1) as value, count(1) as frequency
        from stories
        where project_id={} and model_score is not NULL
        group by 1
        order by 1
    """.format(
        project_id
    )
    return _run_query(query)
