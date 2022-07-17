import random
import requests
from bs4 import BeautifulSoup as bs4
from selenium import webdriver

with open(f'./genConfig/names.txt', 'r', encoding='utf-8') as namesStr:
    names = namesStr.read().split(',')
with open(f'./genConfig/emails.txt', 'r', encoding='utf-8') as emailsStr:
    emails = emailsStr.read().split(',')
with open(f'./genConfig/messages.txt', 'r', encoding='utf-8') as messagesStr:
    messages = messagesStr.read().split(';;;')

name = random.choice(names)
email = random.choice(emails)
message = random.choice(messages)

url = "https://newsdd.ru/"

try: 
    response = requests.get(url)
    # Если ответ от сервера не 200 то пробрасываем ошибку
    if response.status_code != 200:
        raise ValueError('Error')  
except Exception as err:
    print("Не удалось подключиться!!!")
    
html = bs4(response.content, "html.parser")
links = html.select(".articleTitle")
urlArr = []

for i in links:
    urlArr.append(i.get('href'))

urlForComment = random.choice(urlArr)

# Настраиваем чтобы не запускалось окно браузера
option = webdriver.FirefoxOptions()
option.headless = True

browser = webdriver.Firefox()
browser.get(urlForComment)

messageInput = browser.find_element("id", "comment")
authorInput = browser.find_element("id", "author")
emailInput = browser.find_element("id", "email")
submitBtn = browser.find_element("id", "submit")

messageInput.send_keys(message)
authorInput.send_keys(name)
emailInput.send_keys(email)
submitBtn.click()