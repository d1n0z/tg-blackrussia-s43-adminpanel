from typing import Type

from aiogram.filters import Filter
from aiogram.fsm.state import StatesGroup
from aiogram.types import Message

from Bot.dispatcher import dp


class StatesGroupHandle(Filter):
    def __init__(self, group: Type[StatesGroup]) -> None:
        self.group = group

    async def __call__(self, message: Message) -> bool:
        state = await dp.fsm.resolve_context(
            bot=message.bot, chat_id=message.chat.id, user_id=message.from_user.id
        ).get_state()
        return state in self.group.__state_names__
