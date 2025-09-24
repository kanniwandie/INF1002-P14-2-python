import pandas as pd
import numpy as np

df = pd.read_csv("AAPL.csv")

def smaCalculator(data):

    close_list = data["Close"].to_numpy()
    date_list = data["Date"].to_numpy()

    while True:
        startDate = (input("Please enter the start date for the SMA stock indicator in D/M/2020: "))
        days = int(input("Please enter the amount of days for the SMA: "))

        if startDate in date_list and 0<=days<=len(close_list):
            dateIndex = list(date_list).index(startDate)
            limit = close_list[dateIndex:dateIndex + days]
            print(f"The average from {startDate} to the next {days} day(s) is: {limit.mean()}")

            cont = input("Would you like to calculate more SMA indicator? (yes/no): ")

            if cont.lower() == 'yes':
                print("Enter your next SMA you want to find")

            elif cont.lower() == 'no':
                print("Program has stopped")

                break
        else:
            print("Try again. The date must be on a trading day in the year 2020.")

smaCalculator(df)