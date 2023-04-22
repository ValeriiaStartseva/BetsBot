import imaplib
import traceback
from datetime import datetime, timedelta

import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup

from parser.config import path_bets_csv
from program_state import GLOBAL_STATE
from telegram.config import token, path_user_id, path_excel, path_data_for_header, path_mail
from telegram.states import DatePeriod, DataHeaders, LoginMail, AccountSetup

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

BASIC_MARKUP = ReplyKeyboardMarkup(resize_keyboard=True)
BASIC_MARKUP.row(
    types.KeyboardButton('Змінити headers'),
    types.KeyboardButton('Змінити дані e-mail'),
    types.KeyboardButton('Змінити дані акаунта')
)
BASIC_MARKUP.row(types.KeyboardButton('Отримати дані в Excel'), types.KeyboardButton('/commands'))


@dp.message_handler(commands=['start'])    # starts bot, save user_id to cvs, displays buttons
async def start(message):
    user_id = message.from_user.id
    GLOBAL_STATE.USER_TELEGRAM_ID = user_id

    await bot.send_message(
        message.chat.id,
        'Вітаю в Bets bot, відправте /commands для того щоб побачити список доступних команд або оберіть опцію:',
        reply_markup=BASIC_MARKUP
    )


@dp.message_handler(commands=['help'])
async def need_help(message):
    await bot.send_message(message.chat.id, 'If something wrong with bot or bets, please, contact @eugen_vladimirov')


@dp.message_handler(commands=['pause'])
async def need_help(message):
    GLOBAL_STATE.PAUSE = True
    await bot.send_message(message.chat.id, 'Програма буде призупинена перед наступним циклом перевірки пошти')


@dp.message_handler(commands=['unpause'])
async def need_help(message):
    GLOBAL_STATE.PAUSE = False
    await bot.send_message(message.chat.id, 'Програма скоро буде відновлена')


@dp.message_handler(commands=['commands'])
async def need_help(message):
    commands_with_description = {
        '/start': 'Початок роботи з ботом',
        '/help': 'Потрібна допомога?',
        '/pause': 'Призупинити програму',
        '/unpause': 'Відновити програму',
        '/commands': 'Список команд',
    }
    commands = 'Список команд:\n' + '\n'.join(
        [f'{key}: {value}' for key, value in commands_with_description.items()]
    )
    await bot.send_message(message.chat.id, commands)


@dp.message_handler(content_types=['text'])
async def login_to_mail(message):
    if message.text == 'Змінити дані e-mail':
        await bot.send_message(message.chat.id, 'Введіть логін для e-mail-у:', reply_markup=types.ReplyKeyboardRemove())
        await LoginMail.login.set()
    elif message.text == 'Змінити headers':
        await bot.send_message(message.chat.id, 'Введіть Cookies:', reply_markup=types.ReplyKeyboardRemove())
        await DataHeaders.cookies.set()
    elif message.text == 'Отримати дані в Excel':
        await bot.send_message(message.chat.id, 'Введіть період (включно) у форматі "dd/mm/yyyy-dd/mm/yyyy":', reply_markup=types.ReplyKeyboardRemove())
        await DatePeriod.date_period.set()
    elif message.text == 'Змінити дані акаунта':
        await bot.send_message(message.chat.id, f'Введіть blog id (або "-" щоб залишити {GLOBAL_STATE.BLOG_ID}):', reply_markup=types.ReplyKeyboardRemove())
        await AccountSetup.blog_id.set()


@dp.message_handler(state=LoginMail.login)
async def get_login(message: types.Message, state: FSMContext):
    await state.update_data(login=message.text)
    await message.answer("Введіть пароль для e-mail-у:")
    await LoginMail.next()


@dp.message_handler(state=LoginMail.password)
async def get_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Підтвердити', callback_data='question1_yes')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='Скасувати', callback_data='question1_no')
    keyboard.add(key_no)
    question = f'Підтвердити дані'
    await bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
    await LoginMail.next()


@dp.callback_query_handler(lambda call: call.data.startswith('question1'), state=LoginMail.calltest)
async def callback_worker_1(call, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    if call.data.endswith('yes'):
        imap_server = "imap.rambler.ru"
        try:
            port = 993
            imap = imaplib.IMAP4_SSL(imap_server, port)
            sts, res = imap.login(data['login'], data['password'])
            if sts == "OK":
                await bot.send_message(call.message.chat.id, 'Дані почти оновлено')
                new_login = data['login']
                new_password = data['password']
                dict_data = {
                    'USERNAME1': [new_login],
                    'MAIL_PASS1': [new_password],
                }
                await bot.send_message(call.message.chat.id, f'Новий логін: {new_login}\n'
                                                             f'Новий пароль: {new_password}')
                data = pd.DataFrame(dict_data)
                data.to_csv(path_mail, mode='a', header=False, index=False)
        except Exception as exp:
            traceback.print_exc()
            await bot.send_message(call.message.chat.id, f'Перевірка e-mail-у невдала. Помилка: {exp}')
            await bot.send_message(call.message.chat.id, 'Оберіть опцію', reply_markup=BASIC_MARKUP)
    elif call.data.endswith('no'):
        await bot.send_message(call.message.chat.id, 'Оберіть опцію', reply_markup=BASIC_MARKUP)
    await state.reset_state()


@dp.message_handler(state=AccountSetup.blog_id)
async def get_blog_id(message: types.Message, state: FSMContext):
    if message.text == '-':
        await state.update_data(blog_id=GLOBAL_STATE.BLOG_ID)
    else:
        try:
            blog_id = int(message.text)
            if blog_id <= 0:
                raise ValueError
            await state.update_data(blog_id=blog_id)
        except ValueError:
            await message.answer(f"Blog id має бути позитивним цілим числом, спробуйте ще раз")
            return
    await message.answer(f"Введіть суму для ставок або '-' щоб залишити {GLOBAL_STATE.STAKE_AMOUNT}")
    await AccountSetup.next()


@dp.message_handler(state=AccountSetup.stake_amount)
async def get_stake_amount(message: types.Message, state: FSMContext):
    if message.text == '-':
        await state.update_data(stake_amount=GLOBAL_STATE.STAKE_AMOUNT)
    else:
        try:
            stake_amount = float(message.text.replace(',', '.'))
            if stake_amount < 0:
                raise ValueError
            await state.update_data(stake_amount=stake_amount)
        except ValueError:
            await message.answer(f"Сума ставки має бути позитивним числом, спробуйте ще раз")
            return
    await message.answer(
        f"Введіть час очікування (у секундах) для перевірок на наявність нових e-mail-ів "
        f"або '-' щоб залишити {GLOBAL_STATE.WAITING_TIME} секунд"
    )
    await AccountSetup.next()


@dp.message_handler(state=AccountSetup.waiting_time)
async def get_waiting_time(message: types.Message, state: FSMContext):
    if message.text == '-':
        await state.update_data(waiting_time=GLOBAL_STATE.WAITING_TIME)
    else:
        try:
            waiting_time = int(message.text)
            if waiting_time <= 0:
                raise ValueError
            await state.update_data(waiting_time=waiting_time)
        except ValueError:
            await message.answer(f"Час очікування має бути позитивним цілим числом, спробуйте ще раз")
            return

    data = await state.get_data()
    GLOBAL_STATE.BLOG_ID = data['blog_id']
    GLOBAL_STATE.STAKE_AMOUNT = data['stake_amount']
    GLOBAL_STATE.WAITING_TIME = data['waiting_time']

    pd.DataFrame({
        'user_id': [GLOBAL_STATE.USER_TELEGRAM_ID],
        'telegram_name': [message.from_user.username],
        'time_now': [datetime.today()],
        'blog_id': [GLOBAL_STATE.BLOG_ID],
        'waiting_time': [GLOBAL_STATE.WAITING_TIME],
        'stake_amount': [GLOBAL_STATE.STAKE_AMOUNT],
    }).to_csv(path_user_id, mode='a', header=False, index=False, sep=',')

    await message.answer("Дані акаунта успішно змінено", reply_markup=BASIC_MARKUP)
    await state.reset_state()


@dp.message_handler(state=DataHeaders.cookies)
async def get_cookies(message: types.Message, state: FSMContext):
    await state.update_data(cookies=message.text)
    await message.answer("Введіть параметр Content-Length")
    await DataHeaders.next()


@dp.message_handler(state=DataHeaders.content_length)
async def get_content_length(message: types.Message, state: FSMContext):
    await state.update_data(content_length=message.text)
    await message.answer("Введіть параметр X_CSRF_TOKEN")
    await DataHeaders.next()


@dp.message_handler(state=DataHeaders.token_req)
async def get_token_req(message: types.Message, state: FSMContext):
    await state.update_data(token_req=message.text)
    data = await state.get_data()
    keyboard = types.InlineKeyboardMarkup()
    key_yes = types.InlineKeyboardButton(text='Yes', callback_data='question2_yes')
    keyboard.add(key_yes)
    key_no = types.InlineKeyboardButton(text='No', callback_data='question2_no')
    keyboard.add(key_no)
    question = f'Cookies: {data["cookies"]}\n ' \
               f'Content-Length: {data["content_length"]}\n' \
               f'X_CSRF_TOKEN: {data["token_req"]}'
    await bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)
    await DataHeaders.next()


@dp.callback_query_handler(lambda call: call.data.startswith('question2'), state=DataHeaders.calltest)
async def callback_worker_1(call, state: FSMContext):
    data = await state.get_data()
    await call.answer()
    if call.data.endswith('yes'):
        try:
            new_cookies = data['cookies']
            new_content_length = data['content_length']
            new_token = data['token_req']
            GLOBAL_STATE.headers_post_check(new_cookies, new_content_length, new_token)
            if GLOBAL_STATE.HEADERS_ARE_BROKEN:
                GLOBAL_STATE.HEADERS_ARE_BROKEN = False
                raise Exception('Headers не працюють, перевірте свої дані та спробуйте ще раз')
        except Exception as exp:
            await bot.send_message(
                call.message.chat.id,
                f'Введені дані не спрацювали з помилкою "{exp}". Спробуйте ще раз!',
                reply_markup=BASIC_MARKUP
            )
            await state.reset_state()
            return
        else:
            GLOBAL_STATE.update_headers(new_cookies, new_content_length, new_token)
            dict_data = {
                'Cookie': [new_cookies],
                'Content-Length': [new_content_length],
                'X-CSRF-TOKEN': [new_token],
            }
            data = pd.DataFrame(dict_data)
            data.to_csv(path_data_for_header, mode='w', header=False, index=False)
    elif call.data.endswith('no'):
        await bot.send_message(call.message.chat.id, 'Оберіть опцію', reply_markup=BASIC_MARKUP)
    await state.reset_state()


@dp.message_handler(state=DatePeriod.date_period)
async def get_end_date(message: types.Message, state: FSMContext):
    date_period = message.text
    try:
        start_date, end_date = date_period.split('-')
        start_date = datetime.strptime(start_date, '%d/%m/%Y').strftime('%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%d/%m/%Y').strftime('%Y-%m-%d')
    except ValueError:
        month_ago = (datetime.today() - timedelta(days=30)).strftime('%d/%m/%Y')
        today = datetime.today().strftime('%d/%m/%Y')
        await message.answer(
            f'Формат невірний (має бути "dd/mm/yyyy-dd/mm/yyyy", наприклад, `{month_ago}-{today}`), спробуйте ще раз:'
        )
        return
    df = pd.read_csv(path_bets_csv, sep=",")
    file = df.loc[(df['Дата внесення/ставки'] >= start_date) & (df['Дата внесення/ставки'] <= end_date + ' 23:59:59')]
    file.to_excel(path_excel, header=True, index=False)
    await bot.send_message(message.chat.id, 'Тримай свій файл 😉')
    f = open(path_excel, "rb")
    await bot.send_document(message.chat.id, f, reply_markup=BASIC_MARKUP)
    await state.reset_state()


@dp.message_handler()
async def get_message(message: types.Message):
    msg = 'Що ти хочеш зробити сьогодні 🤨?'
    await message.answer(msg, reply_markup=BASIC_MARKUP)
