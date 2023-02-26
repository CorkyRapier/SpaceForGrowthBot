import logging
import time
import uuid
import re

from aiogram.utils.helper import Helper, HelperMode, ListItem
from datetime import datetime
from config import TOKEN, PROXY_URL, TIMEZONE
from aiogram import Bot, Dispatcher, executor, types, filters
from models.users import Users
from models.subscribe_annonce import Subscribe
from models.announcements import Annonce
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from core.handlers import apshed

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
        formated_date = last[3].split('-')
        formated_date = '.'.join(formated_date[::-1])
        text_post_in_channel = f"<b>{last[1]}</b>&#010;&#010;Описание: {last[2]}&#010;&#010;Дата начала мероприятия: {str(formated_date)}, {last[4]}&#010;<i>Код: {last[7]}</i>".replace('\n', '', 1)
        subscribe = types.inline_keyboard.InlineKeyboardButton(text="Подписаться", callback_data="subscribe")
        chat_kb = types.InlineKeyboardMarkup()
        chat_kb.add(subscribe)
        await bot.send_message('-1001672376670', text=text_post_in_channel, reply_markup=chat_kb, parse_mode="html")
        add_annonce = types.inline_keyboard.InlineKeyboardButton(text="Новый анонс", callback_data="add_new_annonce")
        annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Посмотреть анонсы", callback_data='next_0')
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
        annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Посмотреть анонсы", callback_data='next_0')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(add_annonce, annonce_lsit)
        await message.answer("Вы хотите посмотреть анонсы мероприятий или анонсировать новое?", reply_markup=keyboard)

#Subscribe and unsub annonce -------------------------------------------------------
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
#End subscribe block ----------------------------------------------------------

# Change state aplication, add new annonce -----------------------------
@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Добавление отменено, если хотите выполнить другие действия, напишите /start.')
    
@dp.callback_query_handler(text_contains='add_new_annonce')
async def add_new_annonce(query: types.CallbackQuery, state: FSMContext):
    await addAnnonceState.name.set()
    await query.message.edit_text('Введите название мероприятия. (Если вы передумали, напишите "отмена")')

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

@dp.message_handler(lambda message: not re.match('(\d{2})[/.-](\d{2})[/.-](\d{4})$', message.text), state=addAnnonceState.start_date)
async def process_start_date_invalid(message: types.Message):
    """
    If start_date is invalid
    """
    return await message.reply("Неверный формат даты!\n (Верный формат День.Месяц.Год, например - 12.12.2023)")

@dp.message_handler(lambda message: re.match('(\d{2})[/.-](\d{2})[/.-](\d{4})$', message.text), state=addAnnonceState.start_date)
async def process_start_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        date = message.text.split('.')
        new_date = '-'.join(date[::-1])
        data['start_date'] = new_date

    await addAnnonceState.next()
    await message.answer('Введите время начала (например - 18:00):')

@dp.message_handler(lambda message: not re.match('(\d{2})[:](\d{2})$', message.text), state=addAnnonceState.start_time)
async def process_start_time_invalid(message: types.Message):
    """
    If start_time is invalid
    """
    return await message.reply("Неверный формат введенного времени!\n (Верный формат Часы:Минуты, например - 18:00)")

@dp.message_handler(lambda message: re.match('(\d{2})[:](\d{2})$', message.text), state=addAnnonceState.start_time)
async def process_start_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['start_time'] = message.text
        await message.answer("Добавлено новое мероприятие!")
        formated_date = data['start_date'].split('-')
        formated_date = '.'.join(formated_date[::-1])
        await message.answer(
                            f"Имя: {data['name']}\n"
                            f"Описание:: {data['discription']}\n"
                            f"Дата начала мероприятия: {str(formated_date)} {data['start_time']}\n")
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
# End to work with state ----------------------------------------------------------------

@dp.callback_query_handler(lambda query: 'next_' in query.data or 'prev_' in query.data)
async def next_event(query: types.CallbackQuery):
    list_events = Subscribe.get_list_events(query['from'].id)
    before = query.data.split("_")[0]
    serial_number = int(query.data.split("_")[1])
    visible_event = Annonce.get_one_annocne(list_events[serial_number][0])[0]
    if 'next' in before:   
        serial_number += 1
    elif 'prev' in before:
        serial_number -= 1
    if (len(list_events) <= serial_number):
        serial_number = 0
    elif serial_number < 0:
        serial_number = len(list_events) - 1
    next_annonce = types.inline_keyboard.InlineKeyboardButton(text="Следующее", callback_data="next_"+str(serial_number))
    prev_annonce = types.inline_keyboard.InlineKeyboardButton(text="Предыдущее", callback_data="prev_"+str(serial_number))
    # return_back = types.inline_keyboard.InlineKeyboardButton(text="Вернуться в меню", callback_data="restart")
    unsub = types.inline_keyboard.InlineKeyboardButton(text="Отписаться", callback_data='delete_sub')
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(next_annonce, prev_annonce, unsub)
    formated_date = visible_event[3].split('-')
    formated_date = '.'.join(formated_date[::-1])
    text_post_in_private = f"<b>{visible_event[1]}</b>&#010;&#010;Описание: {visible_event[2]}&#010;&#010;Дата начала мероприятия: {str(formated_date)}, {visible_event[4]}&#010;<i>Код: {visible_event[5]}</i>".replace('\n', '', 1)
    if not list_events:
        await query.message.edit_text(f'У вас нет мероприятий на которые вы подписаны.')
    elif len(list_events) == 1:
        await query.message.edit_text(text=text_post_in_private, parse_mode="html")
    else:
        await query.message.edit_text(text=text_post_in_private, reply_markup=keyboard, parse_mode="html")

if __name__ == '__main__':
    executor.start_polling(dp)
