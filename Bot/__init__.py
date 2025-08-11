from Bot import handlers, middlewares
from Bot.dispatcher import dp, bot


class Bot:
    def __init__(self):
        self.bot = bot
        self.dp = dp

    async def run(self):
        self.dp.include_router(handlers.router)
        self.dp.update.middleware.register(middlewares.ContextMsgDeleteMiddleware())
        # self.dp.message.middleware.register(middlewares.MediaGroupMiddleware())
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)
