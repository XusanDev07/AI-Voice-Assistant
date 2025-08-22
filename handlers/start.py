from aiogram import Router, types, F

router = Router()

@router.message(F.text == "/start")
async def start_cmd(message: types.Message):
    await message.answer("👋 Hello! Send me a voice message and I will reply in English.")
