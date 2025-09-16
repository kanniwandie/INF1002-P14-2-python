import csv
import streamlit as st
import datetime

st.set_page_config(
    page_title="Daily Returns"
)

default_date = datetime.date(2020, 1, 2)
min_selectable_date = datetime.date(2020, 1, 2)
max_selectable_date = datetime.date(2020, 12, 31)

selected_date_custom = st.date_input(
    "Choose your date",
    value=default_date,
    min_value=min_selectable_date,
    max_value=max_selectable_date,
    format="YYYY-MM-DD"
)
dropdown_date = selected_date_custom.strftime("%Y-%m-%d")