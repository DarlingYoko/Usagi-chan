from typing import TYPE_CHECKING
from bs4 import BeautifulSoup
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
