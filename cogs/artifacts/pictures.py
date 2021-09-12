from easy_pil import Editor, Canvas
from PIL import Image, ImageFont
from discord import File
from cogs.artifacts.extra import get_sets, list_check_entry
import requests


def create_pic_artifact(artifact, initial):
    blank = Editor('./files/photo/clear_blank.png')
    usagi = Editor(f'./files/photo/{initial}.png').resize((150, 150))
    image = Image.open(requests.get(artifact.part_url, stream=True).raw).resize((220, 220))

    font_BIG = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 35)
    font_big = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 25)
    font_mid = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 20)
    font_small = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 17)
    percent = ['CRIT', '%', 'DMG', 'BONUS', 'ER']

    blank.paste(usagi, (350, 430))
    blank.paste(image, (265, 60))

    set = artifact.set or 'Сет не выбран'
    blank.text((246 - len(set) * 7.9, 15), set, font = font_big, color = "white")

    if artifact.part:
        blank.text((30, 70), artifact.part, font = font_mid, color = "white")

    if artifact.main:
        count = f'{artifact.main[1]}%' if list_check_entry(artifact.main[0], percent) else f'{artifact.main[1]}'
        blank.text((30, 155), artifact.main[0], font = font_mid, color = "#FFF1E6")
        blank.text((30, 180), count, font = font_BIG, color = "white")

    blank.text((35, 310), f'+{artifact.lvl}', font = font_mid, color = "white")


    for i in range(4):
        if artifact.subs[i]:
            stat = artifact.subs[i][0]
            count = artifact.subs[i][1] or '-'

            count = f'{count}%' if list_check_entry(stat, percent) else count
            stat = stat[:-1] if '%' in stat else stat

            blank.text((54, 360 + i * 38.5), f'{stat} +{count}', font = font_big, color = "#39444f")

    if artifact.id:
        zero = '0' * (5 - len(f'{artifact.id}'))
        blank.text((35, 538), f'Usagi ID {zero}{artifact.id}', font = font_mid, color = "white")

    if 'gs' in dir(artifact):
        blank.text((481, 310), f'GS: {artifact.gs} ({(artifact.gs * 100 / 1650):.2f}%)', font = font_small, color = "#39444f", align = 'right')
        blank.text((435, 355), f'{artifact.rate}', font = font_small, color = "#39444f", align = 'right')




    return blank
    file = File(fp = blank.image_bytes, filename = "blank.png")
    return file
