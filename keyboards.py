from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти юзернейм", callback_data="search")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
         InlineKeyboardButton(text="💎 Премиум", callback_data="premium")]
    ])

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

def lengths_kb(is_premium):
    buttons = []
    for length in ([5, 6, 7] if is_premium else [6, 7]):
        buttons.append([InlineKeyboardButton(text=f"{length} символов", callback_data=f"len_{length}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def digits_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ С цифрами", callback_data="digits_yes"),
         InlineKeyboardButton(text="❌ Без цифр", callback_data="digits_no")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

def payment_kb(payment_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data=f"check_{payment_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])