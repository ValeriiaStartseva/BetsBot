import csv

token = '6118793699:AAFgCEaIcW15jT-idZVptU6K25cngmilAEk'
path = '/Users/valeriiastartseva/My_projects/VovaBetsBot/user_id.csv'

with open(path, 'r') as f:  # looking for user_id for sending mails to telegram bot
    reader = csv.reader(f)
    rows = list(reader)
    last_row = rows[-1]
user_id = str(last_row[0])
