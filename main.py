import logging
import time
import uuid
import re
import asyncio

from aiogram.utils.helper import Helper, HelperMode, ListItem
from datetime import datetime
from config import TOKEN, PROXY_URL, TIMEZONE, CHANNEL_ID
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
    photo = State()
    start_date = State()
    start_time = State()
    discription = State()
    link = State()
    user_id = State()

@dp.message_handler(commands=['start'])
@dp.callback_query_handler(text_contains='restart')
async def start_hendler(message: types.Message or types.CallbackQuery):
    if 'text' not in message:
        await bot.delete_message(message.message.chat.id, message.message.message_id)
        last = Annonce.get_last_annonce()[0]
        formated_date = last[3].split('-')
        formated_date = '.'.join(formated_date[::-1])
        text_post_in_channel = f"<b>{last[1]}</b>&#010;&#010;Дата начала мероприятия: {str(formated_date)}, {last[4]}&#010;&#010;Описание: {last[2]}&#010;&#010;Ссылка на канал: {last[9]}&#010;&#010;<i>#Анонс{last[7]}</i>".replace('\n', '', 1)
        subscribe = types.inline_keyboard.InlineKeyboardButton(text="Мне интересно!", callback_data="subscribe")
        chat_kb = types.InlineKeyboardMarkup()
        chat_kb.add(subscribe)
        if len(last[2]) > 900:
            await bot.send_photo(CHANNEL_ID, photo=last[8])
            await bot.send_message(CHANNEL_ID, text_post_in_channel, parse_mode="html", reply_markup=chat_kb)
        else:
            await bot.send_photo(CHANNEL_ID, photo=last[8], caption=text_post_in_channel, parse_mode="html", reply_markup=chat_kb)
        add_annonce = types.inline_keyboard.InlineKeyboardButton(text="Анонсировать мероприятие", callback_data="add_new_annonce")
        annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Мои желаемые мероприятия", callback_data='next_0')
        go_to_channel = types.inline_keyboard.InlineKeyboardButton(text="Перейти в основной канал", url='https://t.me/practiceanytime')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(go_to_channel)
        keyboard.row(add_annonce, annonce_lsit)
        await message.message.answer("Вы хотите посмотреть анонсы мероприятий или анонсировать новое?", reply_markup=keyboard)
    else:
        user_id = message.from_user.id
        user_full_name = message.from_user.full_name
        logging.info(f'{str(time.asctime())}: User {user_id} use command "/start"')

        # await message.reply(f'Привет {user_full_name}!')
        # await message.reply('<i>Уважаемый пользователь, бот находится на стадии разработки. В случае возникновения ошибок, вы можете обратиться к разработчику: https://t.me/CorkyRapier</i>', parse_mode="html")
        await message.reply(f"""
Ассистент Места Силы приветствует вас! 

• Я буду оповещать Вас начале мероприятий, которыми Вы заинтересовались.
• Собирать Вам персональный календарь событий.
Для этого не забудьте нажимать на кнопку «Мне интересно!» под теми мероприятиями, которые вы хотите посетить 

Так же я буду помогать Вам размещать свои анонсы. 
Для размещения анонса, 
• открыть Ассистент Место Силы 
• выбрать меню «Анонсировать мероприятие»
• следовать шагам, предлагаемых скриптом
• готово! 
• в случае возникновения проблемы с загрузкой скрипта, введите в диалоговое окно слово “отмена” или нажмите на кнопку "отмена"

В случае возникновения технических проблем, обратитесь в тех. Поддержку @CorkyRapier
                            """)
        data = [str(uuid.uuid4()), user_id, user_full_name]
        Users.new_user(data)
        add_annonce = types.inline_keyboard.InlineKeyboardButton(text="Анонсировать мероприятие", callback_data="add_new_annonce")
        annonce_lsit = types.inline_keyboard.InlineKeyboardButton(text="Мои желаемые мероприятия", callback_data='next_0')
        go_to_channel = types.inline_keyboard.InlineKeyboardButton(text="Перейти в основной канал", url='https://t.me/practiceanytime')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(go_to_channel)
        keyboard.row(add_annonce, annonce_lsit)
        await message.answer("Вы хотите посмотреть анонсы мероприятий или анонсировать новое?", reply_markup=keyboard)

# @dp.channel_post_handler(lambda message: re.match('Добавлено новое мероприятие!', message.text))
# async def check_grab_annonce(message: types.Message):
#     print(message.text)
#     subscribe = types.inline_keyboard.InlineKeyboardButton(text="Подписаться", callback_data="subscribe")
#     keyboard = types.InlineKeyboardMarkup()
#     keyboard.add(subscribe)
#     # await message.edit_text(text=message.text, reply_markup=keyboard)
#     await bot.edit_message_reply_markup(CHANNEL_ID, message_id=message.message_id, reply_markup=keyboard)

#Subscribe and unsub annonce -------------------------------------------------------
@dp.callback_query_handler(text_contains='subscribe')
async def subscribe_on_annonce(query: types.CallbackQuery, state: FSMContext):
    one_annonce = None
    if query.message.caption:
        code_u = query.message.caption.split('с')[-1].strip()
        elem_list = query.message.caption.split('\n')
    else:
        code_u = query.message.text.split('с')[-1].strip()
        elem_list = query.message.text.split('\n')
        one_annonce = Annonce.get_one_annocne_by_code(code_u)[0]
    values = [value for value in elem_list if value]
    response = Subscribe.add_sub([code_u, query['from'].id])
    unsub = types.inline_keyboard.InlineKeyboardButton(text="Не интересно", callback_data="delete_sub")
    unsub_kb = types.InlineKeyboardMarkup()
    unsub_kb.add(unsub)
    if response:
        await bot.send_photo(query['from'].id, photo=query.message.photo[0].file_id if not one_annonce else one_annonce[6], caption=f'Вы подписаны на событие: {values[0]}.&#010;&#010;{values[1]}. &#010;&#010; {values[-2]}&#010;&#010; <i>#Анонс{str(code_u)}</i>', reply_markup=unsub_kb, parse_mode="html")
    else:
        await bot.send_message(query['from'].id, f'Невозможно подписаться, вы уже подписаны на событие {values[0]}. <i>#Анонс{str(code_u)}</i>', reply_markup=unsub_kb, parse_mode="html")

@dp.callback_query_handler(text_contains='delete_sub')
async def delete_sub_annonce(query: types.CallbackQuery, state: FSMContext):
    if query.message.caption != None:
        code_u = query.message.caption.split('с')[-1].strip()
    else:
        code_u = query.message.text.split('с')[-1].strip()
    Subscribe.delete_sub([code_u, query['from'].id])
    await query.message.delete()
    await query.message.answer('Вы отписаны от мероприятия.')
#End subscribe block ----------------------------------------------------------

# Change state aplication, add new annonce -----------------------------
@dp.message_handler(state="*", commands='отмена')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    reply_markup=types.ReplyKeyboardRemove()
    await message.reply('Добавление отменено, если хотите выполнить другие действия, напишите /start.', reply_markup=reply_markup)

@dp.callback_query_handler(text_contains='add_new_annonce')
async def add_new_annonce(query: types.CallbackQuery, state: FSMContext):
    await addAnnonceState.name.set()
    stop_add = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    b_stop_add = types.KeyboardButton('отмена')
    stop_add.add(b_stop_add)
    await query.message.answer('Введите название мероприятия. (Если вы передумали, нажмите "отмена")', reply_markup=stop_add)

@dp.message_handler(state=addAnnonceState.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    await addAnnonceState.next()
    await message.answer('Отправьте фото, которое отражает ваше мероприятие(обязательно поставьте галочку "Сжать изображение"):')

@dp.message_handler(lambda message: message.photo, content_types=['photo'], state=addAnnonceState.photo)
async def process_photo(message: types.message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[-1].file_id

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

    await addAnnonceState.next()
    await message.answer('Введите описание мероприятия:')

# @dp.message_handler(lambda message: len(message.text) > 900, state=addAnnonceState.discription)
# async def process_discription_invalid(message: types.Message):
#     """
#     If discription is invalid
#     """
#     return await message.reply("Превышен максимальный размер поста")

@dp.message_handler(state=addAnnonceState.discription)
async def process_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['discription'] = message.text

    await addAnnonceState.next()
    await message.answer('Введите ссылку на ваш канал:')

@dp.message_handler(state=addAnnonceState.link)
async def process_link(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['link'] = message.text
        reply_markup=types.ReplyKeyboardRemove()
        await message.answer("Добавлено новое мероприятие!", reply_markup=reply_markup)
        formated_date = data['start_date'].split('-')
        formated_date = '.'.join(formated_date[::-1])
        await message.answer(
                            f"Имя: {data['name']}\n"
                            f"Дата начала мероприятия: {str(formated_date)} {data['start_time']}\n"
                            f"Описание: {data['discription']}\n"
                            f"Ссылка на канал: {data['link']}\n")
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
            datetime.now(TIMEZONE),
            data['photo'],
            data['link']
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
    if not list_events:
        await query.message.edit_text(f'У вас нет мероприятий на которые вам интересны.')
        return
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
    unsub = types.inline_keyboard.InlineKeyboardButton(text="Не интересно", callback_data='delete_sub')
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(next_annonce, prev_annonce, unsub)
    keyboard_only_unsub = types.InlineKeyboardMarkup()
    keyboard_only_unsub.add(unsub)
    formated_date = visible_event[3].split('-')
    formated_date = '.'.join(formated_date[::-1])
    text_post_in_private = f"<b>{visible_event[1]}</b>&#010;&#010;Дата начала мероприятия: {str(formated_date)}, {visible_event[4]}&#010;&#010;Описание: {visible_event[2]}&#010;&#010;Ссылка на канал: {visible_event[7]}&#010;&#010;<i>#Анонс{visible_event[5]}</i>".replace('\n', '', 1)
    if len(list_events) == 1:
        # await query.message.edit_text(text=text_post_in_private, reply_markup=keyboard_only_unsub, parse_mode="html")
        if len(text_post_in_private) > 900:
            await bot.send_photo(query['from'].id, photo=visible_event[6], caption=f'{text_post_in_private[0:895]}...&#010;&#010;<i>#Анонс{visible_event[5]}</i>', reply_markup=keyboard_only_unsub, parse_mode="html")
        else:
            await bot.send_photo(query['from'].id, photo=visible_event[6], caption=text_post_in_private, reply_markup=keyboard_only_unsub, parse_mode="html")
    else:
        # await query.message.edit_text(text=text_post_in_private, reply_markup=keyboard, parse_mode="html")
        if len(text_post_in_private) > 900:
            await bot.send_photo(query['from'].id, photo=visible_event[6], caption=f'{text_post_in_private[0:895]}...&#010;&#010;<i>#Анонс{visible_event[5]}</i>', reply_markup=keyboard, parse_mode="html")
        else:
            await bot.send_photo(query['from'].id, photo=visible_event[6], caption=text_post_in_private, reply_markup=keyboard, parse_mode="html")

async def periodic(sleep_for):
    while True:
        await asyncio.sleep(sleep_for)
        event_soon_list = Subscribe.get_events_soon()
        if event_soon_list == []:
            continue
        for event in event_soon_list:
            one = Annonce.get_one_annocne(event[0])[0]
            formated_date = one[3].split('-')
            formated_date = '.'.join(formated_date[::-1])
            text_post_in_private = f"Скоро состоится мероприятие, которое вам интересно:&#010;&#010;<b>{one[1]}</b>&#010;&#010;Дата начала мероприятия: {str(formated_date)}, {one[4]}&#010;&#010;Описание: {one[2]}&#010;&#010;Ссылка на канал: {one[7]}&#010;&#010;<i>#Анонс{one[5]}</i>".replace('\n', '', 1)
            Subscribe.update_send_status(event[2])
            if len(text_post_in_private) > 900:
                await bot.send_photo(event[1], photo=one[6], caption=f'{text_post_in_private[0:900]}...&#010;&#010;<i>#Анонс{one[5]}</i>', parse_mode="html")
            else:
                await bot.send_photo(event[1], photo=one[6], caption=text_post_in_private, parse_mode="html")

async def info_message(sleep_for):
    while True:
        await asyncio.sleep(sleep_for)
        go_to_bot = types.inline_keyboard.InlineKeyboardButton(text="запустить Ассистента", url="https://t.me/space_for_growth_bot")
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(go_to_bot)
        await bot.send_message(CHANNEL_ID, text="""
Обратите внимание!
Для получения максимальных возможностей от пользования каналом Место Силы: 

- напоминания о начале понравившегося мероприятия 
- персональный обновляющийся календарь запланированных событий 
- размещение анонсов в канале Место Силы 

Необходимо запустить Бота-Ассистента. 
@space_for_growth_bot""", parse_mode="html", reply_markup=keyboard)
        continue

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(periodic(7200))
    loop.create_task(info_message(10))
    executor.start_polling(dp)
