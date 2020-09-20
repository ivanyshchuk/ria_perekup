#python-telegram-bot
import logging
from datetime import datetime
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, MessageHandler, Filters, ConversationHandler, CommandHandler)
from model import User
from parserr import get_page, parse_page, add_url_params
from task import start_task


BOT_ID = '1357168238:AAE-TV1QADoccJtTL1VMmJGxKLZPsKpbGQ0'

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

# reply_keyboard = [{'Додати': 'add'}, {'Показати': 'view'}]
reply_keyboard = [['add'], ['delete']]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

logging.basicConfig(filename='bot_log.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger('telegram bot')


def start(update, context):
    chat_id = update.message.chat_id
    first_name = update.effective_chat.first_name or ''
    last_name = update.effective_chat.last_name or ''
    user_name = first_name + last_name
    user = User.select().where(User.chat_id == chat_id)
    if not user:
        User.create(chat_id=chat_id, username=user_name)
    update.message.reply_text("Вас вітає бот якій допоможе придбати авто з auto ria\n"
                              "Кнопка add для додавання або редагування посилання на відфільтрований список автомобілів.\n"
                              "Кнопка delete - видаляє відслідковування автомобілів.",
                              reply_markup=markup)
    return CHOOSING


def add_url(update, context):
    chat_id = update.message.chat_id
    user = User.get_or_none(User.chat_id == chat_id)
    if user:
        if user.search_url:
            update.message.reply_text('Ваш список автомобілів буде замінений')
        update.message.reply_text('Вставте посилання на новий список автомобілів. Який виб хотіли відслідковувати. Потрібно вставити посилання на автомобілі посортовані за най новішими.')
    else:
        start(update, context)
    return TYPING_CHOICE


def delete_url(update, context):
    chat_id = update.message.chat_id
    user = User.get_or_none(User.chat_id == chat_id)
    if user:
        if user.search_url:
            now = datetime.now()
            User.update(search_url=None, history=None, modified=now).where(User.chat_id == chat_id).execute()
            update.message.reply_text('Розсилка зупинена', reply_markup=markup)
        else:
            update.message.reply_text('У вас немає розсилки', reply_markup=markup)
    else:
        start(update, context)
    return CHOOSING


def answer(update, context):
    chat_id = update.message.chat_id
    search_url = str(update.message.text).replace(' ', '')
    page = get_page(add_url_params(search_url, {'size': 30}))
    href_list = parse_page(page)
    if not href_list:
        update.message.reply_text('Відповідь відхилена. Не вдалося знайти автомобілі по цьому посиланню', reply_markup=markup)
    else:
        now = datetime.now()
        User.update(search_url=search_url, history=','.join(href_list), modified=now).where(User.chat_id == chat_id).execute()
        update.message.reply_text('Відповідь прийнята.', reply_markup=markup)
    return CHOOSING


def wrong_answer(update, context):
    update.message.reply_text('Виберіть один з варіантів в меню.', reply_markup=markup)
    return CHOOSING


def done(update, context):
    user_data = context.user_data
    chat_id = update.message.chat_id
    if 'choice' in user_data:
        del user_data['choice']
    update.message.reply_text('Бот видалив усі дані про вас.')
    user_data.clear()
    User.delete().where(User.chat_id == chat_id).execute()
    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    # print('Update "%s" caused error "%s"', update, context.error)
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(BOT_ID, use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(Filters.regex('add'), add_url),
                      ],
        states={
            CHOOSING: [MessageHandler(Filters.regex('add'), add_url),
                       MessageHandler(Filters.regex('delete'), delete_url)
                       ],
            TYPING_CHOICE: [MessageHandler(Filters.text, answer)],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
        allow_reentry=True
    )
    dp.add_handler(conv_handler)
    dp.add_handler(MessageHandler(Filters.all, wrong_answer))
    dp.add_error_handler(error)
    # Start the Bot
    print('start bot')
    updater.start_polling()
    # Start the parser task
    start_task()
    logger.info('START')
    updater.idle()


if __name__ == '__main__':
    main()
