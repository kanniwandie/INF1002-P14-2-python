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

                        
dr_date_list = []
dr_close_list = []
with open('AAPL.csv', mode='r', newline='') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        dr_date_list.append(row['Date'])
        dr_close_list.append(row['Close'])

if dropdown_date in dr_date_list:
    index = dr_date_list.index(dropdown_date)
    if index != 0:
        dc = float(dr_close_list[index])
        pc = float(dr_close_list[index-1])
        daily_return = ((dc-pc)/pc)*100
        st.write(f"Daily return for {dropdown_date}: {daily_return:.3f}%")
    else:
        st.write("Unable to calculate daily return")
else: 
    st.write("Unable to calculate daily return")