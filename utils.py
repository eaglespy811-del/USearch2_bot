import random
import string
import aiohttp
import secrets
from datetime import datetime

async def check_username(username: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://t.me/{username}") as resp:
                return resp.status == 404
    except:
        return False

def generate_username(length: int, with_digits: bool):
    chars = string.ascii_lowercase
    if with_digits:
        chars += string.digits
    first = random.choice(string.ascii_lowercase)
    rest = ''.join(random.choice(chars) for _ in range(length - 1))
    return first + rest

async def search_free(length: int, with_digits: bool):
    for _ in range(50):
        username = generate_username(length, with_digits)
        if await check_username(username):
            return username
    return None

def generate_payment_id(user_id: int) -> str:
    return f"pay_{user_id}_{int(datetime.now().timestamp())}"

def generate_premium_key() -> str:
    part1 = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    part2 = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
    part3 = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
    return f"{part1}-{part2}-{part3}"