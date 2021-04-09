import logging
import time
from pathlib import Path

import requests
import pyaimp
import yaml
import vk_api
from vk_api import audio
from vk_api.audio import VkAudio

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR.joinpath("config.yaml")

# Считываем данные с конфиг файла
with open(CONFIG_PATH, encoding="utf8") as ymlFile:
	config = yaml.load(ymlFile.read(), Loader=yaml.Loader)

logging.basicConfig(
	format='%(asctime)s - %(message)s', 
	datefmt='%d-%b-%y %H:%M:%S', 
	level=logging.INFO
)


class Bot:
	def __init__(self):
		self.last_track = ""
		self.offline_status = config["offline_status"]

	def auth(self):
		vk_session = vk_api.VkApi(
            login=config["login"],
            password=config["password"]
        )
		try:
			vk_session.auth()
		except Exception as e:
			logging.error("Не получилось авторизоваться, попробуйте снова.")
			exit()
		logging.info('Вы успешно авторизовались.')
		self.vk = vk_session.get_api()
		self.audio = audio.VkAudio(vk_session)
			
	def check(self):
		try:
			client = pyaimp.Client()
			state = client.get_playback_state()

			if state == pyaimp.PlayBackState.Stopped:
				logging.info("AIMP остановлен")
				self.set_offline_status()
			elif state == pyaimp.PlayBackState.Paused:
				logging.info("AIMP на паузе")
				self.set_offline_status()
			elif state == pyaimp.PlayBackState.Playing:
				track_title = client.get_current_track_info()["title"]

				logging.info(f"Сейчас играет: track_title")

				if self.last_track != track_title:
					try:
						response = self.audio.search(
							q=track_title,
							count=1
						)
						track = list(response)[0]
						track_id = f"{track['owner_id']}_{track['id']}"
						params = {
							"audio": track_id,
							"access_token": config["user_token"],
							"v": "5.130"
						}
						requests.get("https://api.vk.com/method/audio.setBroadcast", params=params)

					except Exception as e:
						status = f"🎧AIMP | {track_title}"
						self.vk.status.set(text=status)

					self.last_track = track_title
					logging.info(f"Статус изменён")

		except RuntimeError as re:  # AIMP instance not found
			print(re)
			logging.error("AIMP не запущен")
			self.set_offline_status()
		except Exception as e:
			logging.error(e)
			self.set_offline_status()

	def set_offline_status(self):
		logging.error("Статус изменён на оффлайн")
		self.vk.status.set(text=self.offline_status)

	def run(self):
		while True:
			logging.info("Проверка")
			self.check()
			time.sleep(60)


if __name__ == "__main__":
	bot = Bot()
	bot.auth()
	try:
		bot.run()
	except KeyboardInterrupt:
		logging.info("Выход")