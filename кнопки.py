import json
import os
import random
import urllib.request
import xml.etree.ElementTree as ET

import vk_api
from dotenv import load_dotenv
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

load_dotenv()
TOKEN = os.getenv("VK_GROUP_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"

def load_rates():
    with urllib.request.urlopen(CBR_URL, timeout=10) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    rates = {}
    for valute in root.findall("Valute"):
        code = valute.findtext("CharCode")
        name = valute.findtext("Name")
        nominal = valute.findtext("Nominal")
        value = valute.findtext("Value")
        rates[code] = f"{nominal} {name}: {value} руб."
    return rates

def make_keyboard():
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button("Профиль", color=VkKeyboardColor.PRIMARY, payload={"cmd": "profile"})
    keyboard.add_button("Курсы", color=VkKeyboardColor.POSITIVE, payload={"cmd": "rates"})
    keyboard.add_line()
    keyboard.add_button("Задания", color=VkKeyboardColor.SECONDARY, payload={"cmd": "tasks"})
    keyboard.add_button("Помощь", color=VkKeyboardColor.NEGATIVE, payload={"cmd": "help"})
    return keyboard.get_keyboard()

def send_message(vk, peer_id, text, keyboard=None):
    params = {"peer_id": peer_id, "message": text, "random_id": random.randint(1, 2_147_483_647)}
    if keyboard:
        params["keyboard"] = keyboard
    vk.messages.send(**params)

def get_command(message):
    payload = message.get("payload")
    if payload:
        return json.loads(payload).get("cmd", "")
    return message.get("text", "").strip().lower()

ANSWERS = {
    "profile": "Профиль появится позже. Сейчас вы тестировщик бота.",
    "rates": "Курс валют подключим на следующем занятии.",
    "tasks": "Задание: добавьте еще одну кнопку.",
    "help": "Нажимайте кнопки или пишите: помощь.",
}

def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            command = get_command(message)

            if command in ("rates", "usd", "eur", "cny"):
                try:
                    rates = load_rates()
                    if command == "rates":
                        answer = f"{rates['USD']}\n{rates['EUR']}\n{rates['CNY']}"
                    else:
                        answer = rates[command.upper()]
                except Exception as error:
                    answer = f"Не получилось загрузить курс: {error}"
            else:
                answer = ANSWERS.get(command, "Напишите USD, EUR или CNY.")

            send_message(vk, message["peer_id"], answer, keyboard=make_keyboard())

if __name__ == "__main__":
    main()