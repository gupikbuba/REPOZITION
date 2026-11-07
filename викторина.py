import os
import random

import vk_api
from dotenv import load_dotenv
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll


load_dotenv()
TOKEN = os.getenv("VK_GROUP_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))

QUESTIONS = [
    ("Какой тип данных хранит пары ключ-значение?", "словарь"),
    ("Как называется файл для секретных переменных?", ".env"),
    ("Куда отвечаем в VK: peer_id или from_id?", "peer_id"),
]
GAMES = {}


def send_message(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text, random_id=random.randint(1, 2_147_483_647))


def start_game(user_id):
    GAMES[user_id] = {"step": 0, "score": 0}
    return QUESTIONS[0][0]


def answer_quiz(user_id, text):
    game = GAMES.get(user_id)
    if game is None:
        return "Напиши: старт"

    question, right_answer = QUESTIONS[game["step"]]
    if text.strip().lower() == right_answer:
        game["score"] += 1

    game["step"] += 1
    if game["step"] >= len(QUESTIONS):
        score = game["score"]
        del GAMES[user_id]
        return f"Игра окончена. Счет: {score}/{len(QUESTIONS)}"

    return QUESTIONS[game["step"]][0]


def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            text = message.get("text", "").strip().lower()
            if text == "старт":
                answer = start_game(message["from_id"])
            else:
                answer = answer_quiz(message["from_id"], text)
            send_message(vk, message["peer_id"], answer)


if __name__ == "__main__":
    main()