# import sqlite3
import os
import re
from collections import deque

import telebot

bot = telebot.TeleBot(os.environ.get('TG_BOT_SECRET'))

# conn = sqlite3.connect("cards.db")


storage = {
    # '<user_id>': '<wizard_obj>'
}


class WizardException(Exception):
    pass


class Wizard:
    steps = None

    def __init__(self, user_id, **kwargs):
        if self.name is None:
            raise WizardException('The wizard must have a name')

        if self.steps is None:
            raise WizardException('The wizard must have steps')

        self.user_id = user_id
        self.current_state = deque(self.steps)
        self.current_state.reverse()

    def get_next_step(self):
        raise NotImplementedError

    def run_continue(self, msg):
        next_step = self.get_next_step()
        self.__getattribute__(f'step_{next_step}')(msg)

    def __str__(self):
        return f'<Wizard {self.name}: {self.current_state}>'

    def __repr__(self):
        return self.__str__()

    @property
    def name(self):
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', self.__class__.__name__).lower()


class LoopQueueWizard(Wizard):
    def get_next_step(self):
        step = self.current_state.pop()
        self.current_state.appendleft(step)
        return step


class SimpleQueueWizard(Wizard):
    def get_next_step(self):
        return self.current_state.pop()


class AddCardWizard(SimpleQueueWizard):
    steps = ('input_phrase', 'input_translate', 'bye')
    buffer = []

    def step_input_phrase(self, msg):
        self.buffer.append(msg.from_user.id)
        bot.reply_to(
            msg,
            'Привет! Напиши мне фразу на английском',
            reply_markup=telebot.types.ForceReply(selective=False)
        )

    def step_input_translate(self, msg):
        self.buffer.append(msg.text)
        bot.reply_to(
            msg,
            'Как это переводится?',
            reply_markup=telebot.types.ForceReply(selective=False)
        )

    def step_bye(self, msg):
        self.buffer.append(msg.text)
        bot.reply_to(
            msg,
            'Я сохранил вашу карточку :)',
            reply_markup=telebot.types.ForceReply(selective=False)
        )

    def get_next_step(self):
        print(f'Buffer: {self.buffer}')
        return super().get_next_step()


class ExampleWizard(SimpleQueueWizard):
    steps = ('start', 'second', 'third', 'end')

    def step_start(self, msg):
        bot.reply_to(
            msg,
            f'You sent me: {msg.text}. '
            f'Hello, {msg.from_user.last_name} {msg.from_user.first_name}. '
            f'How are you?'
        )

    def step_second(self, msg):
        bot.reply_to(
            msg,
            f'You sent me: {msg.text}. '
            f'Well. Me too. '
            f'{msg.from_user.first_name}, how do you do?'
        )

    def step_third(self, msg):
        bot.reply_to(
            msg,
            f'You sent me: {msg.text}. '
            f'Amazing! Пожелай мне удачи в бою.'
        )

    def step_end(self, msg):
        storage.pop(msg.from_user.id)
        bot.reply_to(
            msg,
            f'You sent me: {msg.text}. '
            f'Thanks & Bye'
        )


@bot.message_handler(content_types=['text'])
def wizard_dispatch(msg):
    print(f'======= Session begin =======')
    print(f'From:\t{msg.from_user.id}')
    print(f'Text:\t{msg.text}')
    print(f'Is cmd:\t{msg.text.startswith("/")}')

    user_id = msg.from_user.id

    if is_bot_command(msg) and msg.text == '/addcard':
        clear_storage_for_user(msg)
        wizard = AddCardWizard(msg.from_user.id)
        add_wizard_to_storage(msg.from_user.id, wizard)
        wizard.run_continue(msg)
    elif user_id in storage:
        wizard = storage[user_id]
        wizard.run_continue(msg)

    print(f'UStor: {storage.get(user_id, "empty")}')
    print(f'======= Session end =======\n')


def is_bot_command(msg):
    return msg.text.startswith("/")


def clear_storage_for_user(msg):
    storage.pop(msg.from_user.id, None)


def add_wizard_to_storage(user_id, wizard):
    storage[user_id] = wizard


bot.polling()