from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time




chrome_options = Options()
chrome_options.add_argument("--headless")


driver = webdriver.Chrome(chrome_options = chrome_options)
driver.get('https://discord.com/channels/733631069542416384/734004322177646614')


login = 'zartem01@gmail.com'
pas = 'Baris0n01'
loginXpath = '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/div[1]/div/div[2]/input'
passXpath = '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/div[2]/div/input'
statusFromXpath = '//*[@id="app-mount"]/div[6]/div[2]/div/div/div[2]/div[1]/div/div/div[2]/input'

WebDriverWait(driver, 10, 0.01).until(EC.visibility_of_element_located((By.XPATH, loginXpath)))
loginForm = driver.find_element_by_xpath(loginXpath)
passForm = driver.find_element_by_xpath(passXpath)


loginForm.send_keys(login)
passForm.send_keys(pas)

driver.find_element_by_xpath('//*[@id="app-mount"]/div[2]/div/div[2]/div/div/form/div/div/div[1]/div[3]/button[2]').click()
WebDriverWait(driver, 10, 0.01).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[1]/section/div[2]')))

string = 'YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK YEP COCK '
num_chars = 9
i = 0
while True:
    time.sleep(2)

    driver.find_element_by_xpath('//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[1]/section/div[2]/div[1]/div').click()
    WebDriverWait(driver, 10, 0.01).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="status-picker-custom-status"]/div/div')))
    driver.find_element_by_xpath('//*[@id="status-picker-custom-status"]/div/div').click()
    WebDriverWait(driver, 10, 0.01).until(EC.visibility_of_element_located((By.XPATH, statusFromXpath)))
    form = driver.find_element_by_xpath(statusFromXpath)
    form.clear()
    form.send_keys(string[i:i+num_chars])
    i += 1
    if(i == len(string) - num_chars + 1):
        i = 0

    driver.find_element_by_xpath('//*[@id="app-mount"]/div[6]/div[2]/div/div/div[3]/button[1]').click()
    WebDriverWait(driver, 10, 0.01).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="app-mount"]/div[2]/div/div[2]/div/div/div/div/div[1]/section/div[2]/div[1]/div')))
