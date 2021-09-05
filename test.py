
from easy_pil import Editor, Canvas
import requests
from PIL import Image, ImageFont

url = 'https://cdn.discordapp.com/attachments/877981304644304926/877982951932063784/Item_Flower_of_Creviced_Cliff.png'
image = Image.open(requests.get(url, stream=True).raw).resize((100, 100))
font_big = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 20)
font_mid = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 15)
font_small = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 10)




blank = Editor(Canvas((300, 300), 'white'))
art = Canvas((300, 100), 'orange')


blank.paste(art.image, (0, 0))
blank.paste(image, (200, 0))
blank.text((10, 10), 'KYOKA', font = font_big, color = "white")
blank.text((10, 30), 'Цвяточек', font = font_mid, color = "white")
blank.text((10, 50), 'Архаичный кам', font = font_small, color = "white")

blank.text((10, 120), 'Мейн стат', font = font_big, color = "black")
blank.text((10, 150), 'Саб стат 1', font = font_mid, color = "black")
blank.text((10, 180), 'Саб стат 2', font = font_mid, color = "black")
blank.text((10, 210), 'Саб стат 3', font = font_mid, color = "black")
blank.text((10, 240), 'Саб стат 4', font = font_mid, color = "black")



blank.show()
