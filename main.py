import telebot
from telebot import types
from config import BOT_TOKEN
from database import add_task, get_tasks, delete_task, update_task_name, update_task_description

bot = telebot.TeleBot(BOT_TOKEN)

def generate_tasks_inline_keyboard(user_id, page=1):
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    user_tasks = get_tasks(user_id)
    if user_tasks:
        start_index = (page - 1) * 6
        end_index = min(start_index + 6, len(user_tasks))

        for index in range(start_index, end_index, 2):
            task1 = user_tasks[index]
            callback_data1 = f'task_{index}'
            button1 = types.InlineKeyboardButton(text=task1.split(':')[0], callback_data=callback_data1)

            if index + 1 < end_index:
                task2 = user_tasks[index + 1]
                callback_data2 = f'task_{index + 1}'
                button2 = types.InlineKeyboardButton(text=task2.split(':')[0], callback_data=callback_data2)
                keyboard.add(button1, button2)
            else:
                keyboard.add(button1)

        if end_index < len(user_tasks):
            next_page = page + 1
            callback_data_next = f'next_{next_page}'
            keyboard.add(types.InlineKeyboardButton(text='➡️ Далее', callback_data=callback_data_next))

        if page > 1:
            prev_page = page - 1
            callback_data_prev = f'prev_{prev_page}'
            keyboard.add(types.InlineKeyboardButton(text='⬅️ Назад', callback_data=callback_data_prev))

    return keyboard


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button1 = types.KeyboardButton('📆 Задачи')
    button2 = types.KeyboardButton('ℹ️ Информация')
    markup.add(button1, button2)

    bot.send_message(message.chat.id, "Привет! Я бот задачник", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Информация')
def send_info(message):
    bot.send_message(message.chat.id, "Если у вас есть вопросы или предложения, вы можете связаться с создателем.")

@bot.message_handler(func=lambda message: message.text == '📆 Задачи')
def send_tasks_menu(message):
    tasks_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    task_button1 = types.KeyboardButton('➕ Добавить задачу')
    task_button2 = types.KeyboardButton('🔍 Просмотреть задачи')
    back_button = types.KeyboardButton('⬅️ Назад')
    tasks_markup.add(task_button1, task_button2, back_button)

    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=tasks_markup)

@bot.message_handler(func=lambda message: message.text == '⬅️ Назад')
def go_back(message):
    send_welcome(message)

users_waiting_for_description = {}

@bot.message_handler(func=lambda message: message.text == '➕ Добавить задачу')
def add_task_handler(message):
    msg = bot.send_message(message.chat.id, "Введите название задачи:")
    bot.register_next_step_handler(msg, ask_task_description)

def ask_task_description(message):
    task_title = message.text
    user_id = message.from_user.id

    users_waiting_for_description[user_id] = task_title

    msg = bot.send_message(message.chat.id, "Теперь введите описание задачи:")
    bot.register_next_step_handler(msg, save_task)

def save_task(message):
    task_description = message.text
    user_id = message.from_user.id

    task_title = users_waiting_for_description.get(user_id)
    if task_title:
        add_task(user_id, task_title, task_description)
        bot.send_message(message.chat.id, "Задача добавлена!")
    else:
        bot.send_message(message.chat.id, "Что-то пошло не так. Попробуйте снова добавить задачу.")

    users_waiting_for_description.pop(user_id, None)

    send_tasks_menu(message)

@bot.message_handler(func=lambda message: message.text == '🔍 Просмотреть задачи')
def view_tasks(message):
    user_id = message.from_user.id
    user_tasks = get_tasks(user_id)

    if user_tasks:
        keyboard = generate_tasks_inline_keyboard(user_id)
        bot.send_message(message.chat.id, "Выберите задачу для просмотра:", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "У вас нет задач.")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('task_', 'next_', 'prev_')))
def handle_task_inline(call):
    user_id = call.from_user.id
    user_tasks = get_tasks(user_id)

    if user_tasks:
        if call.data.startswith('task_'):
            task_index = int(call.data.split('_')[1])
            if 0 <= task_index < len(user_tasks):
                task_info = user_tasks[task_index]

                task_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
                edit_button = types.KeyboardButton('✏️ Редактировать')
                delete_button = types.KeyboardButton('❌ Удалить')
                back_button = types.KeyboardButton('⬅️ Назад')
                task_markup.add(edit_button, delete_button)
                task_markup.add(back_button)

                bot.send_message(call.message.chat.id, task_info, reply_markup=task_markup)
                bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_task_action, task_index)
            else:
                bot.send_message(call.message.chat.id, "Не удалось найти задачу.")
        elif call.data.startswith('next_'):
            page = int(call.data.split('_')[1])
            keyboard = generate_tasks_inline_keyboard(user_id, page)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
        elif call.data.startswith('prev_'):
            page = int(call.data.split('_')[1])
            keyboard = generate_tasks_inline_keyboard(user_id, page)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard)
    else:
        bot.send_message(call.message.chat.id, "У вас нет задач.")


def handle_task_action(message, task_index):
    user_id = message.from_user.id
    user_tasks = get_tasks(user_id)

    if message.text == '✏️ Редактировать':
        edit_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        edit_title_button = types.KeyboardButton('Изменить название')
        edit_description_button = types.KeyboardButton('Изменить описание')
        back_button = types.KeyboardButton('⬅️ Назад')
        edit_markup.add(edit_title_button, edit_description_button)
        edit_markup.add(back_button)

        bot.send_message(message.chat.id, "Выберите, что вы хотите изменить:", reply_markup=edit_markup)
        bot.register_next_step_handler_by_chat_id(message.chat.id, lambda m: handle_edit_option(m, user_id, task_index))
    elif message.text == '❌ Удалить':
        delete_task(user_id, task_index)
        bot.send_message(message.chat.id, "Задача удалена.")
        send_tasks_menu(message)
    elif message.text == '⬅️ Назад':
        send_tasks_menu(message)

def handle_edit_option(message, user_id, task_index):
    if message.text == 'Изменить название':
        msg = bot.send_message(message.chat.id, "Введите новое название задачи:")
        bot.register_next_step_handler(msg, lambda m: update_task_title_handler(m, user_id, task_index))
    elif message.text == 'Изменить описание':
        msg = bot.send_message(message.chat.id, "Введите новое описание задачи:")
        bot.register_next_step_handler(msg, lambda m: update_task_description_handler(m, user_id, task_index))
    elif message.text == '⬅️ Назад':
        send_tasks_menu(message)

def update_task_title_handler(message, user_id, task_index):
    new_title = message.text
    user_tasks = get_tasks(user_id)
    if 0 <= task_index < len(user_tasks):
        updated_task = f"{new_title}"
        update_task_name(user_id, task_index, updated_task)
        bot.send_message(message.chat.id, "Название задачи обновлено.")
    send_tasks_menu(message)

def update_task_description_handler(message, user_id, task_index):
    new_description = message.text
    user_tasks = get_tasks(user_id)
    if 0 <= task_index < len(user_tasks):
        updated_task = f"{new_description}"
        update_task_description(user_id, task_index, updated_task)
        bot.send_message(message.chat.id, "Описание задачи обновлено.")
    send_tasks_menu(message)

bot.polling()