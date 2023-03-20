import telebot
from config import token
from telebot import types
from mails.helpers import connection
import imaplib


def telegram_bot(token):
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=['start', '/return_to_main_menu'])
    def start(message):
        markup = types.ReplyKeyboardMarkup()
        button1 = types.KeyboardButton('1')
        button2 = types.KeyboardButton('Change login to mail')
        button3 = types.KeyboardButton('3')
        button4 = types.KeyboardButton('/help')

        markup.row(button1, button2)
        markup.row(button3, button4)

        bot.send_message(message.chat.id, 'Welcome to Bets bot', reply_markup=markup)
        bot.send_message(message.chat.id, 'Choose your option:', reply_markup=markup)

    @bot.message_handler(commands=['help'])
    def need_help(message):
        bot.send_message(message.chat.id, 'If something wrong with bot or bets, please, contact @eugen_vladimirov')

    @bot.message_handler(content_types=['text'])
    def login_to_mail(message):
        if message.text == 'Change login to mail':
            bot.send_message(message.chat.id, 'Please put your login to mail below:')
            bot.register_next_step_handler(message, get_login)

    def get_login(message):
        global login
        login = message.text
        bot.send_message(message.from_user.id, 'Please put your password below')
        bot.register_next_step_handler(message, get_password)

    def get_password(message):
        global password
        password = message.text
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Yes', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='No', callback_data='no')
        keyboard.add(key_no)
        question = f'Your login is: {login} and your password is: {password}?'
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_worker(call):
        if call.data == "yes":
            username = login
            mail_pass = password
            imap_server = "imap.rambler.ru"
            port = 993
            imap = imaplib.IMAP4_SSL(imap_server, port)
            sts, res = imap.login(username, mail_pass)
            if sts == "OK":
                bot.send_message(call.message.chat.id, 'Your data has been updated')
                new_login = login
                new_password = password
                bot.send_message(call.message.chat.id, f'New login is: {new_login} and new password is: {new_password}')
            elif str == "Invalid login or password":
                bot.send_message(call.message.chat.id, 'Email does not exist. Please, try again')
        elif call.data == "no":
            bot.send_message(call.message.chat.id, 'Choose your option:')
    bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    telegram_bot(token)
