import os

import telebot

from wizard import AddCardWizard

bot = telebot.TeleBot(os.environ.get('TG_BOT_SECRET'))


storage = {
    # '<user_id>': '<wizard_obj>'
}


@bot.message_handler(content_types=['text'])
def wizard_dispatch(msg):
    print(f'======= Session begin =======')
    print(f'From:\t{msg.from_user.id}')
    print(f'Text:\t{msg.text}')
    print(f'Is cmd:\t{msg.text.startswith("/")}')

    user_id = msg.from_user.id

    if is_bot_command(msg) and msg.text == '/addcard':
        clear_storage_for_user(msg)
        wizard = AddCardWizard(msg.from_user.id, bot)
        add_wizard_to_storage(msg.from_user.id, wizard)
        wizard.run_continue(msg)
    elif user_id in storage:
        wizard = storage[user_id]
        try:
            wizard.run_continue(msg)
        except IndexError:
            storage.pop(msg.from_user.id)

    print(f'UStor: {storage.get(user_id, "empty")}')
    print(f'======= Session end =======\n')


def is_bot_command(msg):
    return msg.text.startswith("/")


def clear_storage_for_user(msg):
    storage.pop(msg.from_user.id, None)


def add_wizard_to_storage(user_id, wizard):
    storage[user_id] = wizard


bot.polling()
