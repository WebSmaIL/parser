import json
import requests
from bs4 import BeautifulSoup as bs4
import base64
from progress.bar import IncrementalBar

# Вводим учетные данные из wordpress
wp_url = "https://newsdd.ru/wp-json/wp/v2"
wp_user = "smailadmin"
wp_password = "vBVl 1vcL mFV6 hnzD VsAV adDg"

# Подготавливаем все для будущей аутентификации в wordpress
credentials = wp_user + ':' + wp_password
token = base64.b64encode(credentials.encode())

# Подготавливаем хедер запроса
header = {'Authorization': 'Basic ' + token.decode('utf-8')}

# Записываем картинку в файл
with open(f'oldLinks.txt', 'r') as cacheTxt:
    cache = cacheTxt.read().split(';')

# Открываем файл с юрлами
with open("./json/urls.json", "r") as JSONurls:
    jsons = json.load(JSONurls)
    urls = jsons['urls']

# Запускаем перебор урлов из массива
for element in urls:
    hrefArr = []
    
    # Запускаем перебор страниц на сайте
    for pageNum in range(1, element['pages_len'] + 1):
        
        # Отправляем запросы на сервер
        try: 
            if element['page_bool']:
                response = requests.get(element['url'] + element['page'] + str(pageNum) + element['page_postf'])
            else:
                response = requests.get(element['url'] + element['page'])
                
            # Если ответ от сервера не 200 то пробрасываем ошибку
            if response.status_code != 200:
                raise ValueError('Error')
        
        except Exception as err:
            print("Не удалось подключиться!!!")
                    
        # Парсим весь html страницы
        html = bs4(response.content, "html.parser")
        
        links = []
        
        if element['article_bool']:
        
            # Находим статьи на странице
            articles = html.select(element['article'])
            
            # Находим ссылки в статьях (перебор статей)
            for i in articles:
                links.append(i.select(element['link'])[0])
                
                
        else:
            links = html.select(element['link'])
        
        
        # Добавляем ссылки массив
        for link in links:
            hrefArr.append(element['link_pref'] + link.get('href'))
        
    bar = IncrementalBar('Перебор', max = len(hrefArr))
    print('Массив ссылок сформирован,\nНа сайте - '
              + element['url']
              + " на "
              + str(element['pages_len'])
              + " страницах найдено "
              + str(len(hrefArr)) + " статей\n"
              + "Начинаю перебор статей...")
    
    # Делаем запросы на статьи
    for link in hrefArr:
        bar.next()
        
        if link in cache:
            print('\nСсылка уже была')
            break
        
        # Пробуем подключиться к статье
        try: 
            articleResponse = requests.get(link)
            
            # Если ответ от сервера не 200 то пробрасываем ошибку
            if articleResponse.status_code != 200:
                raise ValueError('Error')
        
        except Exception as err:
            print("\nНе удалось подключиться к " + link)
            
        # Парсим весь html страницы
        articleHtml = bs4(articleResponse.content, "html.parser")
        
        # Находим контент на странице
        articleText = articleHtml.select(element['text_in_post'])     
        
        articleTitle = articleHtml.select(element['title_in_post'])[0].text
        
        if element['date_canIuse']:
        
            if element['date_bool']:
                articleDate = articleHtml.select(element['date_in_post'])[0].get('content')
                articleDate += "T00:00:00"
                
            else:
                articleDate = articleHtml.select(element['date_in_post'])[0].text
                
                articleDate = articleDate.split(".")
                articleDate = "-".join(articleDate[::-1]).replace(' ', '')
                articleDate += "T00:00:00"
        
        if element['image_ready']:
            try:
                # Находим картинку статьи на странице
                articleImg = articleHtml.select(element['img_in_post'])[0]['src']
                
                # Преобразовываем картинку в байтовый вид
                image_bytes = requests.get(element['img_pref'] + articleImg).content
                
                # Записываем картинку в файл
                with open(f'image.jpg', 'wb') as img:
                    img.write(image_bytes)

                # Создаем media endpoint для отправки на wp
                media = {
                    'file' : open('image.jpg', 'rb'),
                    'caption' : 'post image',
                    'description' : 'post image'
                }

                # Отправка картинки на wp
                image = requests.post(wp_url + '/media', headers=header, files=media)
                
                # Получение ссылки на картинку для добавления в пост
                imageURL = str(json.loads(image.content)['source_url'])
                imgBool = True
            
            except Exception as err:
                imgBool = False
        else:
            imgBool = False
        
        # Обнуляем переменную для текстового контента от старых значений
        wp_article = ""
        
        # Вписываем в нее весь текстовый контент со страницы
        for text in articleText:
            wp_article += (text.text + "\n")   
        
        # Формируем пост в зависимости от того есть картинка или нет
        if imgBool:
            if element['date_canIuse']:
                wp_post = {
                    'date' : articleDate,
                    'title': articleTitle,
                    'status': 'publish',
                    'content': '<img src=' + imageURL + '>' + wp_article + '\n' + 'Источник: ' + link,
                    'categories': element['cat_id'],
                }
            else:
               wp_post = {
                    'title': articleTitle,
                    'status': 'publish',
                    'content': '<img src=' + imageURL + '>' + wp_article + '\n' + 'Источник: ' + link,
                    'categories': element['cat_id'],
                } 
        else:
            if element['date_canIuse']:
                wp_post = {
                    'date' : articleDate,
                    'title': articleTitle,
                    'status': 'publish',
                    'content': wp_article + '\n' + 'Источник: ' + link,
                    'categories': element['cat_id'],
                }
            else:
                wp_post = {
                    'title': articleTitle,
                    'status': 'publish',
                    'content': wp_article + '\n' + 'Источник: ' + link,
                    'categories': element['cat_id'],
                }
        
        # Отправляем сформерованный пост на сервер
        try: 
            wp_response = requests.post(wp_url + '/posts' , headers=header, json=wp_post)
        
        except Exception as err:
            print("\nНе удалось добавить статью")
        
        with open(f'oldLinks.txt', 'a') as cacheTxt:
            cacheTxt.write(link + ';')
    
    bar.finish()