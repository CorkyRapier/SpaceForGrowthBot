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
        await bot.delete_message(message.message.chat.id, message.message.message_id)
        last = Annonce.get_last_annonce()[0]
        text_post_in_channel = f"""
        Имя: <b>{last[1]}</b>
        Описание:: {last[2]}
        Дата начала мероприятия: {last[3]} {last[4]}
        <i>Код: {last[7]}</i>
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
    await bot.forward_message(query['from'].id, query.message.chat.id, query.message.message_id)
    code_u = query.message.text.split(':')[-1].strip()
    response = Subscribe.add_sub([code_u, query['from'].id])
    unsub = types.inline_keyboard.InlineKeyboardButton(text="Отписаться", callback_data="delete_sub")
    unsub_kb = types.InlineKeyboardMarkup()
    unsub_kb.add(unsub)
    if response:
        await bot.send_message(query['from'].id, f'Вы подписаны на событие. (Код: {str(code_u)})', reply_markup=unsub_kb)
    else:
        await bot.send_message(query['from'].id, f'Невозможно подписаться, вы уже подписаны на это событие. (Код: {str(code_u)})', reply_markup=unsub_kb)

@dp.callback_query_handler(text_contains='delete_sub')
async def delete_sub_annonce(query: types.CallbackQuery, state: FSMContext):
    code_u = query.message.text.split(':')[-1].strip().replace(')', '')
    Subscribe.delete_sub([code_u, query['from'].id])
    await query.message.edit_text('Вы отписаны от мероприятия.')

@dp.callback_query_handler(text_contains='add_new_annonce')
async def add_new_annonce(query: types.CallbackQuery, state: FSMContext):
    await addAnnonceState.name.set()
    await query.message.edit_text('Введите название мероприятия.')

@dp.message_handler(state=addAnnonceState.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await addAnnonceState.next()
    await message.answer('Введите описание мероприятия:')

@dp.message_handler(state=addAnnonceState.discription)
async def process_discription(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['discription'] = message.text

    await addAnnonceState.next()
    await message.answer('Введите дату начала в формате - день.месяц.год (например - 22.12.2023):')

@dp.message_handler(state=addAnnonceState.start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start_date'] = message.text

    await addAnnonceState.next()
    await message.answer('Введите время начала (например - 18:00):')

@dp.message_handler(state=addAnnonceState.start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start_time'] = message.text
        await message.answer("Добавлено новое мероприятие!")
        await message.answer(
                            f"Имя: {data['name']}\n"
                            f"Описание:: {data['discription']}\n"
                            f"Дата начала мероприятия: {data['start_date']} {data['start_time']}\n")
        check = Annonce.check_double([message.from_user.id, data['start_date'], data['start_time']])
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


if __name__ == '__main__':
    executor.start_polling(dp)
