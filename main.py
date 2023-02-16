import logging
import time
import uuid

from config import TOKEN
from aiogram import Bot, Dispatcher, executor, types
from models.users import Users

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

@dp.message_handler(commands=['start'])
async def start_hendler(message: types.Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'{str(time.asctime())}: User {user_id} use command "/start"')

    await message.reply(f'Привет {user_full_name}!')
    data = [str(uuid.uuid4()), user_id, user_full_name]
    Users.new_user(data)

if __name__ == '__main__':
    executor.start_polling(dp)