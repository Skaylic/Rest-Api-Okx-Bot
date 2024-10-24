from dotenv import load_dotenv
from okx.exceptions import OkxAPIException
from skay.Logger import setup_logger
from skay.Bot import Bot

load_dotenv()
logger = setup_logger()

bot = Bot()


def run():
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received, shutting down...')
    except OkxAPIException as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(str(e))


if __name__ == '__main__':
    run()
