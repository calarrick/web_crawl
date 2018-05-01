from datetime import date

curr_date = '08/31/2017'
start_split = curr_date.split('/')
curr_as_date = date(int(start_split[2]), int(start_split[0]), int(start_split[1]))
curr_date = curr_as_date.isoformat()


raw_month_num = curr_as_date.month - 6
real_month_num = raw_month_num
month_day = curr_as_date.day
if raw_month_num == 2 and month_day > 28:
    month_day = 28
year_num = curr_as_date.year
if raw_month_num < 1:
    real_month_num = 12 + raw_month_num
    year_num = curr_as_date.year - 1
start_as_date = curr_as_date.replace(month=real_month_num, year=year_num, day = month_day)
start = start_as_date.isoformat()
