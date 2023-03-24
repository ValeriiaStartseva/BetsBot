import csv

ENCODING = "utf-8"
path = '/Users/valeriiastartseva/My_projects/VovaBetsBot/login_to_mail.csv'
with open(path, 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)
    last_row = rows[-1]
    print(last_row)
USERNAME1 = str(last_row[0])
MAIL_PASS1 = str(last_row[1])


# USERNAME1 = "dovbanute@rambler.ru"  # UserMain in Expari
# MAIL_PASS1 = "2HX7wZgM"
USERNAME2 = "dovbanute1@rambler.ru"         # User2 in Expari
MAIL_PASS2 = "2HX7wZgN"


