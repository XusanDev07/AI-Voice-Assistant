import asyncio
from bot_init import bot, dp
from handlers import start, voice

# Routerlarni ulash
dp.include_router(start.router)
dp.include_router(voice.router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
