from Bot import handlers
from Bot.dispatcher import bot, dp
from Bot import middlewares


class Bot:
    def __init__(self):
        self.bot = bot
        self.dp = dp

    async def run(self):
        self.dp.include_router(handlers.router)
        self.dp.update.middleware.register(middlewares.ContextMsgDeleteMiddleware())
        self.dp.update.middleware.register(middlewares.EnsureMessageMiddleware())
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)
