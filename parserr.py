import random
import time

import urllib3
from bs4 import BeautifulSoup   #https://pypi.org/project/beautifulsoup4/
import requests
from user_agent import generate_user_agent
from model import User

from json import dumps

try:
    from urllib import urlencode, unquote
    from urlparse import urlparse, parse_qsl, ParseResult
except ImportError:
    # Python 3 fallback
    from urllib.parse import (
        urlencode, unquote, urlparse, parse_qsl, ParseResult
    )

TIMEOUT = 10

SLEEP_DELAY_LIST = [2, 3, 5, 6]

headers = {
    'User-Agent': '',
    'Host': 'auto.ria.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'uk,ru;q=0.9,en;q=0.8,en-US;q=0.7,pl;q=0.6,ru-RU;q=0.5',
    'Connection': 'keep-alive',
    'cache-control': 'max-age=0'
}

urllib3.disable_warnings()


def get_page(url):
    try:
        session = requests.Session()
        headers['User-Agent'] = generate_user_agent()
        session.headers = headers
        resp = session.get(url, timeout=TIMEOUT, verify=False, stream=True)
        print(url, resp.status_code)
        if resp.status_code != 200:
            from main import logger
            logger.info('request status %s' % resp.status_code)
            return ''
    except requests.ConnectionError as exception:
        return ''
    return resp.text


def parse_page(page_text):
    soup = BeautifulSoup(page_text, 'html.parser')
    # print(soup.prettify())
    a_tags = soup.select('a.m-link-ticket')
    href = []
    for a in a_tags:
        href.append(a['href'])
    return href


def parse_auto_ria(bot, users):
    for user in users:
        # url = "https://auto.ria.com/uk/legkovie/hyundai/?page=1"

        page = get_page(add_url_params(user.search_url, {'size': random.randint(5, 25)}))
        # page = get_page(user.search_url)
        href_list = parse_page(page)
        if href_list:
            # print('>', href_list)
            user_history = user.history.split(',')
            # print('user history urls> ', user_history)
            if user_history:
                result_list = diff(href_list, user_history)
                # print('>>>> result ', result_list)
                if result_list:
                    for a in result_list[:5]:
                        bot.send_message(user.chat_id, a)
                    user_history.extend(result_list)
                    # print('>> user new history>> ', user_history)
                    User.update(history=','.join(user_history[:100])).where(User.chat_id == user.chat_id).execute()
        time.sleep(random.choice(SLEEP_DELAY_LIST))


def diff(items, user_history):
    return [i for i in items if i not in user_history]


def add_url_params(url, params):
    url = unquote(url)
    parsed_url = urlparse(url)
    get_args = parsed_url.query
    parsed_get_args = dict(parse_qsl(get_args))
    parsed_get_args.update(params)
    parsed_get_args.update(
        {k: dumps(v) for k, v in parsed_get_args.items()
         if isinstance(v, (bool, dict))}
    )
    encoded_get_args = urlencode(parsed_get_args, doseq=True)
    new_url = ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()
    return new_url
