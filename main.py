import logging
import time
from pathlib import Path

import pyaimp
import yaml
import vk_api


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
        self.last_song = ""
        self.offline_status = config["vk"]["offline_status"]

    def auth_handler(self, remember_device=None):
        code = input("Введите код подтверждения\n> ")
        if remember_device is None:
            remember_device = True
        return code, remember_device

    def auth(self):
        vk_session = vk_api.VkApi(
            login=config["vk"]["login"],
            password=config["vk"]["password"],
            auth_handler=self.auth_handler
        )
        try:
            vk_session.auth()
        except Exception as e:
            logging.error("Не получилось авторизоваться, попробуйте снова.")
        logging.info('Вы успешно авторизовались.')
        self.vk = vk_session.get_api()

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
                song_title = client.get_current_track_info()["title"]
                if self.last_song != song_title:
                    status = f"AIMP | {song_title}"
                    self.last_song = song_title
                    self.vk.status.set(text=status)
                    logging.info(f"Статус изменён: {status}")

        except RuntimeError as re:  # AIMP instance not found
            logging.error("AIMP не запущен")
            self.set_offline_status()
        except Exception as e:
            logging.error(e)
            self.set_offline_status()

    def set_offline_status(self):
        self.vk.status.set(text=self.offline_status)

    def start_polling(self):
        while True:
            self.check()
            time.sleep(60)


if __name__ == "__main__":
    bot = Bot()
    bot.auth()
    try:
        bot.start_polling()
    except KeyboardInterrupt:
        logging.info("Выход")