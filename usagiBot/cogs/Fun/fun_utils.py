import aiohttp
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)


async def get_exchange_rate_data() -> dict:
    """
    Get parsed exchange rates from tradingview
    :return: Rates Dict
    """
    base_url = "https://ru.tradingview.com/markets/currencies/"

    rates = {}
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        for path in ("rates-europe/", "rates-asia/"):
            async with session.get(base_url + path) as response:
                if response.status == 200:
                    rates.update(parse_exchange_rate(await response.text()))

    return rates


def parse_exchange_rate(html: str) -> dict:
    """
    Parse rates from web response body
    :param html: Response body
    :return: Parsed currencies dict
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find_all("tr")[1:]
    rates = {}

    for currency in table:
        name = currency.find("a").text
        value = currency.find_all("td")[1].text
        change = currency.find_all("td")[3].text
        rates[name] = {"value": value, "change": change}

    return rates
