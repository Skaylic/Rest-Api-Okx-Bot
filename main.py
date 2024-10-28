from time import sleep

from dotenv import load_dotenv
from okx.exceptions import OkxAPIException
from skay.Logger import setup_logger
from skay.Bot import Bot
from httpx import ReadTimeout, ConnectTimeout

load_dotenv()
logger = setup_logger()


def run():
    try:
        bot = Bot()
        bot.start()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received, shutting down...')
    except OkxAPIException as e:
        logger.error(str(e))
    except ConnectTimeout as e:
        logger.error(str(e))
        sleep(20)
        run()
    except ReadTimeout as e:
        logger.error(str(e))
        sleep(20)
        run()


if __name__ == '__main__':
    run()
