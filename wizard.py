import os
import random
import re
import uuid
from collections import deque

import psycopg2
from telebot import types as teletypes


class WizardException(Exception):
    pass


class Wizard:
    steps = None

    def __init__(self, user_id, bot, **kwargs):
        if self.name is None:
            raise WizardException('The wizard must have a name')

        if self.steps is None:
            raise WizardException('The wizard must have steps')

        self.bot = bot
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


class LoopWizard(Wizard):
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
        self.bot.reply_to(
            msg,
            '[Шаг 1/3] Привет! Напиши мне фразу на английском',
            reply_markup=teletypes.ForceReply(selective=False)
        )

    def step_input_translate(self, msg):
        self.buffer.append(msg.text)
        self.bot.reply_to(
            msg,
            '[Шаг 2/3] Как это переводится?',
            reply_markup=teletypes.ForceReply(selective=False)
        )

    def step_bye(self, msg):
        self.buffer.append(msg.text)
        self._save_card()
        self.bot.reply_to(
            msg,
            '[Шаг 3/3] Я сохранил вашу карточку :)'
        )

    def _save_card(self):
        print(f'Buffer: {self.buffer}')
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        cur = conn.cursor()
        res = cur.execute(
            """
            INSERT INTO cards (user_id, phrase, translate) 
            VALUES (%s, %s, %s)
            """,
            self.buffer
        )
        print(f'{self.name}::save_card::insert::{res}')
        conn.commit()
        cur.close()
        conn.close()


class CheckMeWizard(LoopWizard):
    steps = (
        'show_card',
        # 'check_answer',
    )

    def step_show_card(self, msg):
        print(f'Buffer: {self.buffer}')
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'), sslmode='require')
        cur = conn.cursor()
        cur.execute(
            """
            select * 
            from cards c 
            where c.user_id = %s
            limit 1;
            """,
            msg.from_user.id
        )
        card = [cur.fetchone()]
        markup = teletypes.ReplyKeyboardMarkup(row_width=2)

        markup_options = [teletypes.KeyboardButton(str(uuid.uuid4()))]
        for i in range(3):
            markup_options.append(teletypes.KeyboardButton(str(uuid.uuid4())))

        random.shuffle(markup_options)
        markup.add(*markup_options)

        self.bot.reply_to(msg, card.phrase, reply_markup=markup)

        cur.close()
        conn.close()

    # def step_check_answer(self, msg):
    #     pass
