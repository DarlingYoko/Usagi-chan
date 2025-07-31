import logging
from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
from usagiBot.env import VPN_USERNAME, VPN_PASSWORD, VPN_API_GET_LIST_URL, VPN_API_LOGIN_URL

import requests

if TYPE_CHECKING:
    from requests import Response


def get_exchange_rate_data() -> dict:
    """
    Get parsed exchange rates from tradingview
    :return: Rates Dict
    """
    base_url = 'https://ru.tradingview.com/markets/currencies/'

    response_europe = requests.get(base_url + "rates-europe/")
    currency_europe = {}
    if response_europe.status_code == 200:
        currency_europe = parse_exchange_rate(response_europe)

    response_asia = requests.get(base_url + "rates-asia/")
    currency_asia = {}
    if response_asia.status_code == 200:
        currency_asia = parse_exchange_rate(response_asia)

    rates = {**currency_europe, **currency_asia}

    return rates


def parse_exchange_rate(response: "Response") -> dict:
    """
    Parse rates from web response
    :param response:
    :return: Parsed currencies dict
    """
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find_all('tr')[1:]
    rates = {}

    for currency in table:
        name = currency.find('a').text
        value = currency.find_all('td')[1].text
        change = currency.find_all('td')[3].text
        rates[name] = {'value': value, 'change': change}

    return rates


def vpn_login():
    session = requests.Session()
    login_data = {"username": VPN_USERNAME, "password": VPN_PASSWORD}
    response = session.post(VPN_API_LOGIN_URL, data=login_data)

    if response.status_code != 200:
        return None

    return session

def get_vpn_list():
    session = vpn_login()
    if session is None:
        return None

    response = session.get(VPN_API_GET_LIST_URL)
    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except ValueError as e:
        logging.info("JSON decode error: " + str(e))
        logging.info("Raw response text: " + response.text)
        return None

    users_stats = {}

    if "obj" in data:
        for inbound in data["obj"]:
            for client in inbound["clientStats"]:
                users_stats[client["email"]] = round((client["down"] + client["up"]) / (1024 ** 3), 2)

    return dict(sorted(users_stats.items(), key=lambda x: x[1], reverse=True)[:10])

