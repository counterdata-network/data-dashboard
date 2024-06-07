import streamlit as st

st.set_page_config(layout="wide")


import dashboard.database.processor_db as processor_db  # noqa: E402
from dashboard import graph_functions as helper  # noqa: E402

VERSION = "0.0.1"


st.title("Feminicides Story Dashboard {}".format(VERSION))
st.markdown("Investigate stories moving through the feminicides detection pipeline")
st.divider()

st.subheader("Stories Sent to Main Server")
# By posted day
st.write(
    "Stories sent to the email alerts server based on the day they were run against the classifiers, "
    "grouped by the data source they originally came from."
)
try:
    helper.draw_graph(processor_db.stories_by_posted_day, above_threshold=True)
except ValueError:  # prob no stories to show here
    st.write("_Error creating chart. Perhaps no stories to show here?_")

st.divider()
# History (by discovery date)
st.subheader("More History")
st.write(
    "Stories discovered on each platform based on the guessed date of publication, grouped by the "
    "data source they originally came from."
)
try:
    helper.draw_graph(processor_db.stories_by_published_day)
except ValueError:  # prob no stories to show here
    st.write("_Error creating chart. Perhaps no stories to show here?_")

st.write(
    "Stories based on the date they were run against the classifiers, grouped by the data source"
    "they originally came from."
)
try:
    helper.draw_graph(processor_db.stories_by_processed_day)
except ValueError:  # prob no stories to show here
    st.write("_Error creating chart. Perhaps no stories to show here?_")

st.write(
    "Stories based on the date they were run against the classifiers, grouped by whether they were above"
    "threshold for their associated project or not."
)
try:
    helper.story_results_graph()
except ValueError:  # prob no stories to show here
    st.write("_Error creating chart. Perhaps no stories to show here?_")

st.divider()
