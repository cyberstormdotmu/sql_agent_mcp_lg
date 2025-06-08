# user_input.py
import asyncio
from Agents.test import main

async def get_user_input():
    user_input = input("Please enter your message: ")
    response = await main(user_input)
    print("Agent Response:", response)

if __name__ == "__main__":
    asyncio.run(get_user_input())
