import aiogram
from aiogram.client.default import DefaultBotProperties

import config
from Bot import handlers, filters, middlewares
from Bot.dispatcher import dp


class Bot:
    def __init__(self):
        self.bot = aiogram.Bot(token=config.TOKEN, default=DefaultBotProperties(parse_mode='HTML',
                                                                                link_preview_is_disabled=True))
        self.dp = dp

    async def run(self):
        self.dp.include_router(handlers.router)
        self.dp.update.middleware.register(middlewares.ContextMsgDeleteMiddleware())
        # self.dp.message.middleware.register(middlewares.MediaGroupMiddleware())
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)
