
from easy_pil import Editor, Canvas
import requests
from PIL import Image, ImageFont, ImageDraw






url = 'https://cdn.discordapp.com/attachments/877981304644304926/877982657634500628/Item_Lavawalker27s_Resolution.png'
image = Image.open(requests.get(url, stream=True).raw).resize((220, 220))

font_BIG = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 35)
font_big = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 25)
font_mid = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 20)
font_small = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 10)

#profile = Image.open(requests.get(member.avatar_url, stream=True).raw).resize((100, 100))

blank = Editor('./files/photo/clear_blank3.png')
usagi = Editor('./files/photo/iconUSAGIlook.png').resize((150, 150))




blank.paste(image, (260, 60))
#blank.paste(usagi, (350, 430))
#blank.paste(profile, (200, 200))
set = 'Эмблема рассечённой судьбы'
set = 'Рыцарь крови'
part = 'Цветок жизни'
part = 'Перо смерти'
main_stat = 'HP'
main_stat_count = '4 780'
lvl = '+20'
blank.text((246 - len(set) * 7.9, 15), set, font = font_big, color = "#ecd8e4")
blank.text((30, 70), part, font = font_mid, color = "#ecd8e4")
blank.text((30, 155), main_stat, font = font_mid, color = "#b0b0b0")
blank.text((30, 180), main_stat_count, font = font_BIG, color = "#ecd8e4")
blank.text((35, 310), lvl, font = font_mid, color = "#ecd8e4")
blank.text((35, 538), 'Usagi ID 00027', font = font_mid, color = "#ecd8e4")


for i in range(0, 8, 2):
    blank.text((54, 360 + i * 19.25), 'Crit rate 15.0%', font = font_big, color = "#39444f")
#blank.text((10, 70), 'LVL {artifact_data[3]}', font = font_small, color = "white")

#blank.show()

a = [1, 2, 3, 4]

print()

#blank.text((10, 120), '{artifact_data[4]} {artifact_data[5]}', font = font_big, color = "black")

'''
246 пиксель - середина

246 - длина/2 = начало

'''
