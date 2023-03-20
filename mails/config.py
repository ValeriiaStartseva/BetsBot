import csv


ENCODING = "utf-8"
# USERNAME1 = "dovbanute@rambler.ru"  # UserMain in Expari
# MAIL_PASS1 = "2HX7wZgM"
path = '/Users/valeriiastartseva/My_projects/VovaBetsBot/login_to_mail.csv'
with open(path, 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)
    last_row = rows[-1]
    print(last_row)
USERNAME1 = last_row[0]
MAIL_PASS1 = last_row[1]
print(USERNAME1)
print(MAIL_PASS1)
USERNAME2 = "dovbanute1@rambler.ru"         # User2 in Expari
MAIL_PASS2 = "2HX7wZgN"


