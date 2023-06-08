from telebot import TeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from database import *
from datetime import datetime as dt
import pytz
from handle.utils import add_queue_keyboard_admin


def admin_create_hd(message: Message, bot: TeleBot, session: Session):
    bot.send_message(message.chat.id, text="Создание очереди")
    bot.send_message(message.chat.id, text="Введи имя очереди, которую хочешь создать")
    bot.register_next_step_handler(message, callback_admin_create_hd_a, bot, session)


def callback_admin_create_hd_a(message: Message, bot: TeleBot, session: Session):
    try:
        bot.send_message(message.chat.id,
                         text="Введи время в которое нужно занять очередь, которую хочешь создать (DD-MM HH:MM)")
        bot.register_next_step_handler(message, callback_admin_create_hd_b, bot, session, message.text)
    except Exception as e:
        print("FUNC: callback_create_handler ERR:", e)


def callback_admin_create_hd_b(message: Message, bot: TeleBot, session: Session, table_name: str):
    try:
        datetime = message.text.split(' ')
        day, month = map(int, datetime[0].split('-'))
        hour, minute = map(int, datetime[1].split(':'))

        tables = get_all_tables(session)

        if message.text == 'admins' or message.text == 'tables' or message.text == 'users':
            bot.send_message(message.chat.id, text='Самый умный что-ли?')
            return

        for table in tables:
            if table[1] == message.text:
                bot.send_message(message.chat.id, text='Очередь с таким именем уже существует')
                return

        database_init(session, table_name)
        insert_table(session, {'name': table_name,
                               'date': dt.now(pytz.timezone('Europe/Minsk')),
                               'time': dt.strptime(f"{day}-{month}-{dt.now(pytz.timezone('Europe/Minsk')).year} {hour}:{minute}", '%d-%m-%Y %H:%M').strftime('%d-%m-%Y %H:%M')})

        bot.send_message(message.chat.id, text=f"Очередь создана")
    except Exception as e:
        bot.send_message(message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_create2_handler ERR:", e)


def admin_delete_hd(message: Message, bot: TeleBot, session: Session):
    add_queue_keyboard_admin(message, bot, 'admindeletebutton', session)


def callback_query_admin_delete_hd(call: CallbackQuery, bot: TeleBot, session: Session):
    table_name = call.data[18:]
    tables = get_all_tables(session)
    exist = False
    if table_name == 'admins' or table_name == 'tables' or table_name == 'users':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text='Самый умный что-ли?')
        return
    for table in tables:
        if table[1] == table_name:
            exist = True
    if not exist:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text='Очередь с таким именем не существует')
        return
    delete_table(session, table_name)
    delete_table_from_table(session, table_name)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, text=f"Очередь с именем {table_name} удалена")


def admin_time_hd(message: Message, bot: TeleBot, session: Session):
    add_queue_keyboard_admin(message, bot, 'admintimebutton', session)


def callback_query_admin_time_hd(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        table_name = call.data[16:]
        tables = get_all_tables(session)
        exist = False
        no = 0
        if table_name == 'admins' or table_name == 'tables' or table_name == 'users':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text='Самый умный что-ли?')
            return
        for table in tables:
            if table[1] == table_name:
                exist = True
                break
            no += 1
        if not exist:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text='Очередь с таким именем не существует')
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text=f"Введи новое время как в примере (DD-MM HH:MM)")
        bot.register_next_step_handler(call.message, callback_admin_time_hd, session, get_table_name(session, no + 1))
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_settime_handler ERR:", e)


def callback_admin_time_hd(message: Message, bot: TeleBot, session: Session, table_name: str):
    try:
        datetime = message.text.split(' ')
        day, month = map(int, datetime[0].split('-'))
        hour, minute = map(int, datetime[1].split(':'))

        if is_exist_table(session, table_name):
            set_table_time(session, table_name,
                           dt.strptime(f"{day}-{month}-{dt.now(pytz.timezone('Europe/Minsk')).year} {hour}:{minute}", '%d-%m-%Y %H:%M').strftime('%d-%m-%Y %H:%M'))

            bot.send_message(message.chat.id, "Время занятия очереди изменено")
        else:
            print("Нет такой очереди")
    except Exception as e:
        bot.send_message(message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_settime2_handler ERR:", e)


def admin_edit_hd(message: Message, bot: TeleBot, session: Session):
    add_queue_keyboard_admin(message, bot, 'admineditbutton', session)


def callback_query_admin_edit_hd_a(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        table_name = call.data[16:]
        if not is_exist_table(session, table_name):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text=f'Такой очереди нет, посмотрите список доступных очередей в /queues')
            return
        markup = InlineKeyboardMarkup()
        lst = get_all(session, table_name)
        if lst:
            for human in lst:
                markup.add(InlineKeyboardButton(f"{human[2]}", callback_data=f"adminedit2button {human[0]} {table_name}"))
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Выбери человека", reply_markup=markup)
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text='Очередь пуста :(')
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_edit_handler ERR:", e)


def callback_query_admin_edit_hd_b(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        data = call.data.split(' ')
        db_id = int(data[1])
        table_name = data[2]
        lst = get_all(session, table_name)
        if lst:
            if len(lst) >= db_id:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, text='Введите имя и фамилию человека')
                bot.register_next_step_handler(call.message, callback_admin_edit_hd, session, table_name, db_id)
            else:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, text='Неправильный номер')
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text='Очередь пуста :(')
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_edit2_handler ERR:", e)


def callback_admin_edit_hd(message: Message, bot: TeleBot, session: Session, table_name: str, no: int):
    try:
        update_name(session,
                    get_status_by_no(session, no, table_name)[0][1],
                    message.text, table_name)

        bot.send_message(message.chat.id, text='Готово')
    except Exception as e:
        print("FUNC: callback_admin_edit3_handler ERR:", e)


def admin_change_hd(message: Message, bot: TeleBot, session: Session):
    add_queue_keyboard_admin(message, bot, 'adminchangebutton', session)


def callback_query_admin_change_hd(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        table_name = call.data[18:]
        if not is_exist_table(session, table_name):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text=f'Такой очереди нет, посмотрите список доступных очередей в /queues')
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, text=f'Введи два номера людей через пробел, которых хочешь поменять')
        bot.register_next_step_handler(call.message, callback_admin_change_hd, session, table_name)
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_change_handler ERR:", e)


def callback_admin_change_hd(message: Message, bot: TeleBot, session: Session, table_name: str):
    try:
        lst = get_all(session, table_name)
        no1, no2 = map(int, message.text.split(' '))

        if lst:
            if len(lst) >= no1 and len(lst) >= no2:
                change_queue(session,
                             get_status_by_no(session, no1, table_name)[0],
                             get_status_by_no(session, no2, table_name)[0], table_name)

                bot.send_message(message.chat.id, 'Очередь изменена')
            else:
                bot.send_message(message.chat.id, text='Неправильный номер')
        else:
            bot.send_message(message.chat.id, text='Очередь пуста :(')
    except Exception as e:
        bot.send_message(message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_change2_handler ERR:", e)


def admin_remove_hd(message: Message, bot: TeleBot, session: Session):
    add_queue_keyboard_admin(message, bot, 'adminremovebutton', session)


def callback_query_admin_remove_hd_a(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        table_name = call.data[18:]
        if not is_exist_table(session, table_name):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text=f'Такой очереди нет, посмотрите список доступных очередей в /queues')
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        markup = InlineKeyboardMarkup()
        lst = get_all(session, table_name)
        for human in lst:
            markup.add(InlineKeyboardButton(f"№{human[0]} {human[2]}", callback_data=f"adminremove2button {human[0]} {table_name}"))
        bot.send_message(call.message.chat.id, "Выбери человека", reply_markup=markup)
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_delete_handler ERR:", e)


def callback_query_admin_remove_hd_b(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        data = call.data.split(' ')
        no = int(data[1])
        table_name = data[2]
        lst = get_all(session, table_name)
        if lst:
            if len(lst) >= no:
                cancel_take(session, get_status_by_no(session, no, table_name)[0][1], table_name)
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, 'Удалено')
            else:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, text='Неправильный номер')
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text='Очередь пуста :(')
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_delete2_handler ERR:", e)


def admin_list_hd(message: Message, bot: TeleBot, session: Session):
    admins = get_all_admins(session)
    if not admins:
        bot.send_message(message.chat.id, text="Нет ни одного админа")
        return

    s = "Администраторы:\n"
    for admin in admins:
        s += f"{admin[2]}\n"

    bot.send_message(message.chat.id, text=s)


def admin_kick_hd(message: Message, bot: TeleBot, session: Session):
    markup = InlineKeyboardMarkup()
    users = get_all_users(session)

    if not users:
        bot.send_message(message.chat.id, text="Нет ни одного пользователя")
        close_connection(session)
        return

    for human in users:
        markup.add(InlineKeyboardButton(f"{human[2]}", callback_data=f"adminkickbutton {human[1]}"))

    bot.send_message(message.chat.id, "Выбери пользователя", reply_markup=markup)


def callback_query_admin_kick_hd(call: CallbackQuery, bot: TeleBot, session: Session):
    try:
        data = call.data.split(' ')
        tg_id = data[1]
        remove_admin(session, tg_id)
        remove_user(session, tg_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Пользователь удален')
    except Exception as e:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, 'Что-то не так с вводом, попробуй еще раз')
        print("FUNC: callback_admin_delete2_handler ERR:", e)


def admin_users_hd(message: Message, bot: TeleBot, session: Session):
    users = get_all_users(session)

    if not users:
        bot.send_message(message.chat.id, text="Нет ни одного пользователя")
        return

    s = "Пользователи:\n"
    for human in users:
        s += f"{human[2]}, приоритет: {human[3]}\n"

    bot.send_message(message.chat.id, text=s)


admin_handlers = [
    admin_kick_hd,
    admin_users_hd,
    admin_list_hd,
    admin_remove_hd,
    admin_change_hd,
    admin_edit_hd,
    admin_time_hd,
    admin_delete_hd,
    admin_create_hd,
]

admin_handlers_names = [
    'kick',
    'users',
    'list',
    'remove',
    'change',
    'edit',
    'time',
    'delete',
    'create'
]

admin_query_handlers = [
    callback_query_admin_change_hd,
    callback_query_admin_remove_hd_a,
    callback_query_admin_remove_hd_b,
    callback_query_admin_edit_hd_a,
    callback_query_admin_edit_hd_b,
    callback_query_admin_time_hd,
    callback_query_admin_delete_hd,
    callback_query_admin_kick_hd,
]

admin_query_handlers_names = [
    'adminchangebutton',
    'adminremovebutton',
    'adminremove2button',
    'admineditbutton',
    'adminedit2button',
    'admintimebutton',
    'admindeletebutton',
    'adminkickbutton',
]