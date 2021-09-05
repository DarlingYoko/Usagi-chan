from easy_pil import Editor, Canvas
from PIL import Image, ImageFont
from discord import File
from cogs.artifacts.extra import get_sets
import requests


def create_pic_artifact(name, artifact_data):
    sets = get_sets()
    url = sets[artifact_data[1]][artifact_data[2]]
    image = Image.open(requests.get(url, stream=True).raw).resize((100, 100))
    font_big = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 20)
    font_mid = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 15)
    font_small = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 10)




    blank = Editor(Canvas((300, 300), 'white'))
    art = Canvas((300, 100), 'orange')


    blank.paste(art.image, (0, 0))
    blank.paste(image, (200, 0))
    blank.text((10, 10), name, font = font_big, color = "white")
    blank.text((10, 30), artifact_data[2], font = font_mid, color = "white")
    blank.text((10, 50), artifact_data[1], font = font_small, color = "white")
    blank.text((10, 70), f'LVL {artifact_data[3]}', font = font_small, color = "white")

    blank.text((10, 120), f'Мейн стат {artifact_data[4]} {artifact_data[5]}', font = font_big, color = "black")
    for i in range(4):
        blank.text((10, 150 + i * 30), f'Саб стат {artifact_data[6 + i]} {artifact_data[7 + i]}', font = font_mid, color = "black")


    #blank.show()

    file = File(fp = blank.image_bytes, filename = "blank.png")
    return file
