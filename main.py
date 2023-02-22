import logging
import time
import uuid

from datetime import datetime
from config import TOKEN, PROXY_URL, TIMEZONE
from aiogram import Bot, Dispatcher, executor, types
from models.users import Users
from models.subscribe_annonce import Subscribe
from models.announcements import Annonce
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, proxy=PROXY_URL)

storage = MemoryStorage()

dp = Dispatcher(bot=bot, storage=storage)

#States
class addAnnonceState(StatesGroup):
    name = State()
    discription = State()
    start_date = State()
    start_time = State()
    user_id = State()

@dp.message_handler(commands=['start'])
@dp.callback_query_handler(text_contains='restart')
async def start_hendler(message: types.Message or types.CallbackQuery):
    if 'text' not in message:
        last = Annonce.get_last_annonce()[0]
        text_post_in_channel = f"""
        Имя: <b>{last[1]}</b>
        Описание:: {last[2]}
        Дата начала мероприятия: {last[3]} {last[4]}
        """
        subscribe = types.inline_keyboard.InlineKeyboardButton(text="Подписаться", callback_data="subscribe")
        chat_kb = types.InlineKeyboardMarkup()
        chat_kb.add(subscribe)
        await bot.send_message('-1001672376670', text=text_post_in_channel, reply_markup=chat_kb, parse_mode="html")
        add_annonce = types.inline_keyboard.InlineKeyboardButton(text="Новый анонс", callback_data="add_new_annonce")
        annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Посмотреть анонсы", callback_data='кал')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(add_annonce, annonce_lsit)
        await message.message.answer("Вы хотите посмотреть анонсы мероприятий или анонсировать новое?", reply_markup=keyboard)
    else:
        user_id = message.from_user.id
        user_full_name = message.from_user.full_name
        logging.info(f'{str(time.asctime())}: User {user_id} use command "/start"')

        await message.reply(f'Привет {user_full_name}!')
        data = [str(uuid.uuid4()), user_id, user_full_name]
        Users.new_user(data)
        add_annonce = types.inline_keyboard.InlineKeyboardButton(text="Новый анонс", callback_data="add_new_annonce")
        annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Посмотреть анонсы", callback_data='кал')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(add_annonce, annonce_lsit)
        await message.answer("Вы хотите посмотреть анонсы мероприятий или анонсировать новое?", reply_markup=keyboard)

@dp.callback_query_handler(text_contains='subscribe')
async def subscribe_on_annonce(query: types.CallbackQuery, state: FSMContext):
    unsubscribe = types.inline_keyboard.InlineKeyboardButton(text="Отписаться", callback_data="----")
    unsub_kb = types.InlineKeyboardMarkup()
    unsub_kb.add(unsubscribe)
    await query.message.edit_reply_markup(reply_markup=unsub_kb)
    # print(query)
    # await bot.edit_message_reply_markup(query['from'].id, query.message.message_id, reply_markup=unsub_kb)
    # await query.message.edit_text()

@dp.callback_query_handler(text_contains='add_new_annonce')
async def add_new_annonce(query: types.CallbackQuery, state: FSMContext):
    await addAnnonceState.name.set()
    await query.message.edit_text('Введите название мероприятия.')

@dp.message_handler(state=addAnnonceState.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await addAnnonceState.next()
#     genre_list = Genre.get_list()
#     keyboard = types.InlineKeyboardMarkup()
#     for genre in genre_list:
#         button = types.inline_keyboard.InlineKeyboardButton(text=str(genre[1]), callback_data=str(genre[0]))
#         keyboard.add(button)
#     await message.reply('Выберите жанр мероприятия:', reply_markup=keyboard)

# # @dp.message_handler(state=addAnnonceState.genre_id)
# @dp.callback_query_handler(state=addAnnonceState.genre_id)
# async def process_genre(query: types.CallbackQuery, state: FSMContext):
#     print(query)
#     async with state.proxy() as data:
#         data['genre_id'] = query.data

#     await addAnnonceState.next()
    await message.answer('Введите описание мероприятия:')

@dp.message_handler(state=addAnnonceState.discription)
async def process_discription(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['discription'] = message.text

    await addAnnonceState.next()
    await message.reply('Введите дату начала в формате - день.месяц.год (например - 22.12.2023):')

@dp.message_handler(state=addAnnonceState.start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start_date'] = message.text

    await addAnnonceState.next()
    await message.reply('Введите время начала (например - 18:00):')

@dp.message_handler(state=addAnnonceState.start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start_time'] = message.text
        print(data['name'], data['discription'], data['start_date'], data['start_time'])
        await message.answer("Добавлено новое мероприятие!")
        await message.answer(
                            f"Имя: {data['name']}\n"
                            f"Описание:: {data['discription']}\n"
                            f"Дата начала мероприятия: {data['start_date']} {data['start_time']}\n")
        check = Annonce.check_double([message.from_user.id, data['start_date'], data['start_time']])
        print(check)
        if check != []:
            Annonce.delete(check[0])
        add_data = [
            str(uuid.uuid4()),
            data['name'],
            data['discription'],
            data['start_date'],
            data['start_time'],
            message.from_user.id,
            datetime.now(TIMEZONE)
        ]
        Annonce.add(add_data)
    yes = types.inline_keyboard.InlineKeyboardButton(text="Да", callback_data="restart")
    no = types.inline_keyboard.InlineKeyboardButton(text="Нет", callback_data='add_new_annonce')
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(yes, no)
    await message.answer('Данные верны?', reply_markup=keyboard)
    await state.finish()

# dp.message_handler(message='hello')
# async def add_annonse_db():
#     async with state.proxy() as data:
#         print('Добавил в базу') #не забыть поставить user_id для какждой новости
#     add_annonce = types.inline_keyboard.InlineKeyboardButton(text="Новый анонс", callback_data="add_new_annonce")
#     annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Посмотреть анонсы", callback_data='кал')
#     keyboard = types.InlineKeyboardMarkup()
#     keyboard.add(add_annonce, annonce_lsit)
#     await message.answer("Вы хотите посмотреть анонсы мероприятий или анонсировать новое?", reply_markup=keyboard)


if __name__ == '__main__':
    executor.start_polling(dp)






# {
#     "message_id": 438,
#     "from": {"id": 826586914, "is_bot": false, "first_name": "Егор",
#             "last_name": "Мащенко", "username": "CorkyRapier", "language_code": "ru"},
#     "chat": {"id": 826586914, "first_name": "Егор", "last_name": "Мащенко", "username": "CorkyRapier", "type": "private"},
#     "date": 1676822389,
#     "text": "/start",
#     "entities": [{"type": "bot_command", "offset": 0, "length": 6}]}

# {
#     "id": "3550163766322039316",
#     "from": {
#         "id": 826586914, "is_bot": false, "first_name": "Егор", "last_name":
#         "Мащенко", "username": "CorkyRapier", "language_code": "ru"},
#     "message": {
#         "message_id": 450, "from": {"id": 6297688500, "is_bot": true,
#         "first_name": "Пространство роста и расширения. Бот.", "username": "space_for_growth_bot"},
#     "chat": {
#         "id": 826586914, "first_name": "Егор", "last_name": "Мащенко",
#         "username": "CorkyRapier", "type": "private"
#         },
#     "date": 1676822395,
#     "text": "Данные верны?",
#     "reply_markup": {
#         "inline_keyboard": [[{"text": "Да", "callback_data": "restart"},
#         {"text": "Нет", "callback_data": "add_new_annonce"}]]}},
#     "chat_instance": "4830946017084993614", "data": "restart"
#     }
