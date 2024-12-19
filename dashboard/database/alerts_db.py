import datetime as dt
import logging
from typing import Dict, List
import pandas as pd

import psycopg
from psycopg.rows import dict_row
import streamlit as st

from dashboard import ALERTS_DB_URI

logger = logging.getLogger(__name__)


@st.cache_resource  # so it only run once
def init_connection():
    return psycopg.connect(ALERTS_DB_URI, row_factory=dict_row)


db_conn = init_connection()


@st.cache_data(ttl=1 * 60 * 60)  # so we cache data for a while
def _run_query(query: str) -> List[Dict]:
    dict_cursor = db_conn.cursor()
    dict_cursor.execute(query)
    results = dict_cursor.fetchall()
    return results



def _run_count_query(query: str) -> int:
    data = _run_query(query)
    return data[0]["count"]


# In alerts_db.py
def total_story_count(project_id: int = None) -> int:
    if project_id is not None:
        query = f"SELECT COUNT(1) FROM articles WHERE project_id = {project_id}"
    else:
        query = "SELECT COUNT(1) FROM articles"
    result = _run_query(query)
    return result[0]["count"] if result else 0


def top_media_sources_by_story_volume_22(
    project_id: int = None, limit: int = 10
) -> List:
    query = """
        SELECT media_name, COUNT(1) AS story_count
        FROM articles
        WHERE project_id = {}
        GROUP BY media_name
        ORDER BY story_count DESC
        LIMIT {}
    """.format(
        project_id, limit
    )
    return _run_query(query)


def _alerts_by_date_col(
    column_name: str,
    project_id: int = None,
    limit: int = None,
) -> List:
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    clauses = []
    if project_id is not None:
        clauses.append("(project_id={})".format(project_id))
    query = (
        "select " + column_name + "::date as day, count(1) as stories from Articles "
        "where ("
        + column_name
        + " is not Null) and ("
        + column_name
        + " >= '{}'::DATE) AND {} "
        "group by 1 order by 1 DESC".format(earliest_date, " AND ".join(clauses))
    )
    return _run_query(query)


def stories_by_publish_date(
    project_id: str = None,
    limit: int = 45,
) -> List:
    return _alerts_by_date_col("publish_date", project_id, limit)


def stories_by_creation_date(
    project_id: str = None,
    limit: int = 45,
) -> List:
    return _alerts_by_date_col("created_at", project_id, limit)

def recent_articles(project_id: int, limit: int = 100) -> List:
    """
    UI: show a list of the most recent articles in email alerts for a specific project
    """
    query = """
            SELECT 
                id,
                title,
                source,
                url,
                publish_date
            FROM 
                articles
            WHERE 
                project_id = {project_id}
                AND publish_date >= NOW() - INTERVAL '30 days'
            ORDER BY 
                publish_date DESC
            LIMIT {limit};
        """.format(project_id=project_id, limit=limit)
    return _run_query(query)


def event_counts_by_creation_date(
        project_id: int = None,
        limit: int = 45
) -> List[Dict]:
    """
    Retrieve the count of distinct article_event_id values grouped by created_at day.
    """
    earliest_date = dt.date.today() - dt.timedelta(days=limit)

    clauses = []
    if project_id is not None:
        clauses.append(f"project_id = {project_id}")

    query = (
        f"SELECT created_at::date AS day, "
        f"       COUNT(DISTINCT article_event_id) AS unique_event_count "
        f"FROM articles "
        f"WHERE created_at IS NOT NULL "
        f"  AND created_at >= '{earliest_date}'::DATE "
        f"{' AND ' + ' AND '.join(clauses) if clauses else ''} "
        f"GROUP BY day "
        f"ORDER BY day DESC;"
    )
    return _run_query(query)

def relevance_counts_by_project(
        project_id: int = None,
        limit: int = 45
) -> List[Dict]:
    """
    Retrieve relevancy counts filtered by project_id and a date range based on updated_at day (latest reporting).

    """
    earliest_date = dt.date.today() - dt.timedelta(days=limit)

    clauses = []
    if project_id is not None:
        clauses.append(f"project_id = {project_id}")

    query = (
        f"SELECT "
        f"    COUNT(CASE WHEN is_relevant = TRUE THEN 1 END) AS yes_count, "
        f"    COUNT(CASE WHEN is_relevant = FALSE THEN 1 END) AS no_count, "
        f"    COUNT(CASE WHEN is_relevant IS NULL THEN 1 END) AS null_count "
        f"FROM article_events "
        f"WHERE updated_at IS NOT NULL "
        f"  AND updated_at >= '{earliest_date}'::DATE "
        f"{' AND ' + ' AND '.join(clauses) if clauses else ''};"
    )
    return _run_query(query)