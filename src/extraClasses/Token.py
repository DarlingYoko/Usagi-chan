from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class Token():
    def __init__(self):
        self.xpath = '//*[@id="root"]/div/div[1]/div[2]/div/div[2]/div[1]/h1'
        self.url = 'https://poocoin.app/tokens/'
        self.duration = 10000
        self.frequency = 0.01

        chrome_options = Options()
        chrome_options.add_argument("--headless")


        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.get(self.url)

    def addToken(self, usagi, info):
        #!монета 1.6 вверх 0x3494u20395
        price, trend, token = info.split()
        self.driver.get(self.url + token)
        WebDriverWait(self.driver, self.duration, self.frequency).until(EC.visibility_of_element_located((By.XPATH, self.xpath)))
        name = self.driver.title.split()[0]
        print(token, trend, price, name)
        id = usagi.db.command("INSERT INTO tokens VALUES (DEFAULT, \'{0}\', \'{1}\', \'{2}\', \'{3}\') RETURNING id;".format(token, trend, price, name))
        return '{0} добавлен, id - {1}'.format(name, id[0][0])

    def removeToken(self, usagi, id):
        result = 'Не получилось удалить('
        if usagi.db.remove(tableName = 'tokens', selector = 'id', value = id):
            result = 'Удалила'
        return result

    def viewToken(self, usagi):
        tokensList = usagi.db.getAll(tableName = 'tokens')
        if len(tokensList) == 0:
            return 'У меня нет ни одного токена.'

        result = 'Вот список токенов, что у меня есть:\n'
        for (id, token, trend, price, name) in tokensList:
            result += 'id: {0}, название токена: {1}, тренд: {2}, цена: {3}, кошелёк: {4}\n'.format(id, name, trend, price, token)
        return result

    async def checkTokens(self, usagi):
        tokensList = usagi.db.getAll(tableName = 'tokens')
        channel = await usagi.client.fetch_channel(826485072705880127)
        for (id, token, trend, price, name) in tokensList:
            self.driver.get(self.url + token)
            WebDriverWait(self.driver, self.duration, self.frequency).until(EC.visibility_of_element_located((By.XPATH, self.xpath)))
            newPrice = float(self.driver.title.split('$')[1])
            if newPrice >= float(price) and trend == 'вверх':
                await channel.send('<@&833445461716107285>\nЦена {0} превысила {1}'.format(name, price))
                usagi.db.remove(tableName = 'tokens', selector = 'id', value = id)

            if newPrice <= float(price) and trend == 'вниз':
                await channel.send('<@&833445461716107285>\nЦена {0} упала ниже {1}'.format(name, price))
                usagi.db.remove(tableName = 'tokens', selector = 'id', value = id)
