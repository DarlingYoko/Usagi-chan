from easy_pil import Editor, Canvas
from PIL import Image, ImageFont, ImageOps
from discord import File


def create_pic_from_word(blocks, try_word):


    yellow_block = Image.open('./files/photo/yellow_block.png')
    green_block = Image.open('./files/photo/green_block.png')
    black_block = Image.open('./files/photo/black_block.png')

    background = Editor(Image.new('RGBA', (1024*len(blocks), 1024), (255, 0, 0, 0)))

    font = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 600)

    for i in range(len(blocks)):
        background.paste(eval(blocks[i]), (1024 * i, 0))
        background.text((1024 * i + 250, 255), try_word[i], font = font, color = "#fff")


    file = File(fp = background.image_bytes, filename = "background.png")

    return file
