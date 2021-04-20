from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


url = 'https://poocoin.app/tokens/0xcfefa64b0ddd611b125157c41cd3827f2e8e8615'
xpath = '/html/body/div[5]/div/div'
duration=10000
frequency=0.01

chrome_options = Options()
#chrome_options.add_argument("--headless")

driver = webdriver.Chrome(chrome_options=chrome_options)
#driver.get(url)
#WebDriverWait(driver, duration, frequency).until(EC.visibility_of_element_located((By.XPATH, xpath)))
#print(float(driver.title.split('$')[1]) > 1.6)
driver.close()
