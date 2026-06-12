import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, PRICES, CARD_NUMBER, FREE_LIMIT, PREMIUM_LIMIT
from database import db
from keyboards import main_kb, back_kb, lengths_kb, digits_kb, payment_kb
from utils import search_free, generate_payment_id, generate_premium_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class SearchState(StatesGroup):
    waiting_length = State()
    waiting_digits = State()

class PaymentState(StatesGroup):
    waiting_payment = State()

pending_payments = {}

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    db.register(user_id, message.from_user.username or str(user_id))
    await message.answer(
        "🌟 *USearch Bot* 🌟\n\n"
        "🔍 Поиск свободных username в Telegram\n"
        f"📊 Бесплатно: {FREE_LIMIT} поисков в день\n"
        f"💎 Премиум: {PREMIUM_LIMIT} поисков + 5 символов\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_kb())
    await callback.answer()

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Оплата отменена", reply_markup=main_kb())
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = db.get_user(user_id)
    is_prem = db.is_premium(user_id)
    can, remaining = db.can_search(user_id)
    
    today = datetime.now().date().isoformat()
    today_count = user[4] if user and user[5] == today else 0
    
    text = f"👤 *Профиль*\n\n🆔 ID: {user_id}\n"
    if is_prem and user and user[2]:
        until = datetime.fromisoformat(user[2])
        days = (until - datetime.now()).days
        text += f"💎 Премиум до: {until.strftime('%d.%m.%Y')}\n⏰ Осталось: {days} дней\n"
    else:
        text += "💎 Статус: Бесплатный\n"
    text += f"\n📊 Сегодня: {today_count}/{remaining + today_count}\n📈 Всего: {user[6] if user else 0}"
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_kb())
    await callback.answer()

@dp.callback_query(F.data == "premium")
async def show_premium(callback: types.CallbackQuery):
    text = f"""
💎 *Премиум USearch* 💎

🔥 *Возможности:*
• {PREMIUM_LIMIT} поисков в день
• Поиск 5-символьных username
• Поиск с цифрами и без

💰 *Тарифы:*

• 1 день   — 49₽
• 7 дней   — 149₽
• 30 дней  — 599₽
• 365 дней — 1299₽

💳 *Оплата переводом на карту:*
`{CARD_NUMBER}`

👇 Выбери тариф
"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 день (49₽)", callback_data="tariff_day"),
         InlineKeyboardButton(text="7 дней (149₽)", callback_data="tariff_week")],
        [InlineKeyboardButton(text="30 дней (599₽)", callback_data="tariff_month"),
         InlineKeyboardButton(text="365 дней (1299₽)", callback_data="tariff_year")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data.startswith("tariff_"))
async def select_tariff(callback: types.CallbackQuery, state: FSMContext):
    tariff = callback.data.split("_")[1]
    price = PRICES[tariff]["price"]
    days = PRICES[tariff]["days"]
    name = PRICES[tariff]["name"]
    user_id = callback.from_user.id
    
    payment_id = generate_payment_id(user_id)
    pending_payments[user_id] = {"tariff": tariff, "days": days, "price": price, "payment_id": payment_id}
    
    await state.update_data(payment_id=payment_id, tariff=tariff, days=days, user_id=user_id)
    await state.set_state(PaymentState.waiting_payment)
    
    text = f"""
💳 *Оплата {name} — {price}₽*

*Реквизиты для перевода:*
Карта: `{CARD_NUMBER}`

*В комментарии к переводу ОБЯЗАТЕЛЬНО укажи:*
`{payment_id}`

⚠️ *Без этого кода мы не сможем активировать премиум!*

✅ После перевода нажми кнопку «Я оплатил(а)»
"""
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=payment_kb(payment_id))
    await callback.answer()

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data:
        await callback.answer("❌ Нет активного платежа", show_alert=True)
        return
    
    user_id = data.get("user_id")
    tariff = data.get("tariff")
    days = data.get("days")
    
    if user_id != callback.from_user.id:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    db.activate_premium(user_id, days, tariff)
    key = generate_premium_key()
    
    if user_id in pending_payments:
        del pending_payments[user_id]
    
    await callback.message.edit_text(
        f"✅ *Премиум активирован!*\n\n"
        f"📅 {PRICES[tariff]['name']}\n"
        f"🔑 Ключ: `{key}`\n\n"
        f"🎉 Теперь доступно {PREMIUM_LIMIT} поисков в день и 5-символьные юзернеймы!",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )
    await state.clear()
    await callback.answer("✅ Премиум активирован!")

@dp.callback_query(F.data == "search")
async def search_start(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    can, remaining = db.can_search(user_id)
    
    if not can:
        await callback.answer(f"❌ Лимит исчерпан! Завтра будет {remaining} новых попыток", show_alert=True)
        return
    
    is_prem = db.is_premium(user_id)
    await callback.message.edit_text(
        f"🔍 *Поиск*\nОсталось сегодня: {remaining}\n\nВыбери длину username:",
        parse_mode="Markdown",
        reply_markup=lengths_kb(is_prem)
    )
    await state.set_state(SearchState.waiting_length)
    await callback.answer()

@dp.callback_query(SearchState.waiting_length, F.data.startswith("len_"))
async def search_length(callback: types.CallbackQuery, state: FSMContext):
    length = int(callback.data.split("_")[1])
    await state.update_data(length=length)
    await callback.message.edit_text("Теперь выбери: можно ли использовать цифры?", reply_markup=digits_kb())
    await state.set_state(SearchState.waiting_digits)
    await callback.answer()

@dp.callback_query(SearchState.waiting_digits, F.data.startswith("digits_"))
async def search_digits(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    with_digits = callback.data == "digits_yes"
    data = await state.get_data()
    length = data.get("length")
    
    can, _ = db.can_search(user_id)
    if not can:
        await callback.answer("❌ Лимит исчерпан!", show_alert=True)
        await state.clear()
        return
    
    is_prem = db.is_premium(user_id)
    if length == 5 and not is_prem:
        await callback.answer("❌ 5-символьные username только для премиума!", show_alert=True)
        await state.clear()
        return
    
    await callback.message.edit_text("⏳ Ищу свободный username...")
    
    found = await search_free(length, with_digits)
    db.use_search(user_id)
    
    if found:
        text = f"✅ *Найден свободный username!*\n\n🎯 `{found}`\n\n🔗 https://t.me/{found}\n\n⚠️ Забери его скорее!"
    else:
        text = f"❌ *Не найден* username длиной {length} {'с цифрами' if with_digits else 'без цифр'}\n\nПопробуй другие параметры."
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=main_kb())
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Поиск отменён", reply_markup=main_kb())
    await callback.answer()

# ========== ЗАПУСК ==========
async def main():
    logger.info("🤖 Бот USearch запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())