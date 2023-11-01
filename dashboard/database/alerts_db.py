import datetime as dt
import logging
from typing import Dict, List

import psycopg2
import psycopg2.extras
import streamlit as st

from dashboard import ALERTS_DB_URI

logger = logging.getLogger(__name__)


@st.cache_resource  # so it only run once
def init_connection():
    return psycopg2.connect(ALERTS_DB_URI)


db_conn = init_connection()


@st.cache_data(ttl=6 * 60 * 60)  # so we cache data for a while


def _run_query(query: str) -> List[Dict]:
    dict_cursor = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cursor.execute(query)
    results = dict_cursor.fetchall()
    return results



def _run_count_query(query: str) -> int:
    data = _run_query(query)
    return data[0]["count"]

def total_story_count() -> int:
    query = "SELECT COUNT(1) FROM articles"
    return _run_query(query)

def top_media_sources_by_story_volume(limit: int = 10) -> List:
    query = """
        SELECT media_name, COUNT(1) AS story_count
        FROM articles
        GROUP BY media_name
        ORDER BY story_count DESC
        LIMIT {}
    """.format(limit)
    return _run_query(query)

def email_alerts_stories_by_date_column(
    column_name: str, limit: int = 30
) -> List:
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    query = """
        SELECT {}::date AS day, COUNT(1) AS stories
        FROM articles
        WHERE {} IS NOT NULL AND {} >= '{}'::DATE
        GROUP BY 1
        ORDER BY 1 DESC
    """.format(column_name, column_name, column_name, earliest_date)
    return _run_query(query)
