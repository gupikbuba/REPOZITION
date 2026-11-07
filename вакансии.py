import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request

import vk_api
from dotenv import load_dotenv
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

load_dotenv()
TOKEN = os.getenv("VK_GROUP_TOKEN")
GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
JOBS_URL = "https://jobicy.com/api/v2/remote-jobs"
JOBS_CACHE = {}

def find_jobs(text):
    text = text.strip()
    if len(text) < 2:
        return "После команды напиши поисковую фразу из двух или более символов."

    cache_key = text.lower()
    if cache_key in JOBS_CACHE:
        return JOBS_CACHE[cache_key]

    query = urllib.parse.urlencode({"count": 3, "tag": text})
    with urllib.request.urlopen(f"{JOBS_URL}?{query}", timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))

    jobs = data.get("jobs", [])
    if not jobs:
        answer = "Вакансии не найдены. Попробуй более короткий запрос."
    else:
        lines = []
        for job in jobs:
            location = job.get("jobGeo") or "местоположение не указано"
            level = job.get("jobLevel") or "уровень не указан"
            lines.append(
                f"{job['jobTitle']} — {job['companyName']}\n"
                f"{location}\n{level}\n{job['url']}\nИсточник: Jobicy"
            )
        answer = "\n\n".join(lines)

    JOBS_CACHE[cache_key] = answer
    return answer

def send_message(vk, peer_id, text):
    vk.messages.send(peer_id=peer_id, message=text[:3500], random_id=random.randint(1, 2_147_483_647))

def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message = event.object.message
            text = message.get("text", "").strip()
            if text.lower().startswith("вакансии "):
                try:
                    answer = find_jobs(text[9:])
                except urllib.error.HTTPError as error:
                    answer = f"API вакансий вернул HTTP {error.code}. Попробуй еще раз позже."
                except urllib.error.URLError:
                    answer = "Не получилось подключиться к API вакансий. Проверь интернет."
            else:
                answer = "Напиши: вакансии python junior"
            send_message(vk, message["peer_id"], answer)

if __name__ == "__main__":
    main()