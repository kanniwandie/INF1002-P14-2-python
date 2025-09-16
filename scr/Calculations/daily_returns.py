import csv

dr_date_list = []
dr_close_list = []
with open('AAPL.csv', mode='r', newline='') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        dr_date_list.append(row['Date'])
        dr_close_list.append(row['Close'])


def dr_calc(index):
    dc = float(dr_close_list[index])
    pc = float(dr_close_list[index-1])
    daily_return = ((dc-pc)/pc)*100
    return daily_return