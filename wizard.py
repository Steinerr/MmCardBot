import re
from collections import deque

import telebot


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
        self.bot.reply_to(
            msg,
            'Привет! Напиши мне фразу на английском',
            reply_markup=telebot.types.ForceReply(selective=False)
        )

    def step_input_translate(self, msg):
        self.buffer.append(msg.text)
        self.bot.reply_to(
            msg,
            'Как это переводится?',
            reply_markup=telebot.types.ForceReply(selective=False)
        )

    def step_bye(self, msg):
        self.buffer.append(msg.text)
        self.bot.reply_to(
            msg,
            'Я сохранил вашу карточку :)'
        )

    def get_next_step(self):
        print(f'Buffer: {self.buffer}')
        return super().get_next_step()