import threading
import telegram
from apscheduler.schedulers.blocking import BlockingScheduler

from parserr import parse_auto_ria
from model import User


def parse_and_send_sms():
    from main import BOT_ID
    from main import logger
    try:
        bot = telegram.Bot(BOT_ID)
        users = User.select().where(User.history.is_null(False), User.is_active == True)
        parse_auto_ria(bot, users)
    except Exception as e:
        logger.warning('Task error: %s' % e)
    return True


def start_task():
    def start_task_():
        scheduler = BlockingScheduler()
        scheduler.add_job(parse_and_send_sms, 'interval', seconds=60)          #seconds=60
        scheduler.start()
    t1 = threading.Thread(target=start_task_)
    t1.start()
    return True
