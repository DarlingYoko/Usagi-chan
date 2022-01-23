import requests
from easy_pil import Editor, Canvas
from PIL import Image, ImageFont, ImageOps
from discord import File
from random import randint
from bs4 import BeautifulSoup


def create_pic_from_word(blocks, try_word):


    yellow_block = Image.open('./files/photo/yellow_block.png')
    green_block = Image.open('./files/photo/green_block.png')
    black_block = Image.open('./files/photo/black_block.png')

    background = Editor(Image.new('RGBA', (102*len(blocks), 102), (255, 0, 0, 0)))

    font = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 60)

    for i in range(len(blocks)):
        background.paste(eval(blocks[i]), (102 * i, 0))
        if try_word[i] in ['Й', 'Ё']:
            background.text((102 * i + 25, 20), try_word[i], font = font, color = "#fff")
        else:
            background.text((102 * i + 25, 30), try_word[i], font = font, color = "#fff")


    file = File(fp = background.image_bytes, filename = "background.png")

    return file


def get_words_keybord(ban_words, white_words, try_words, lang):
    font = ImageFont.truetype(font = './files/fonts/genshin.ttf', size = 60)
    green_block = Image.open('./files/photo/green_block.png')
    yellow_block = Image.open('./files/photo/yellow_block.png')
    black_block = Image.open('./files/photo/black_block.png')
    blank = Editor('./files/photo/clear_keyboard.png')

    ru_keyboard = 'й ц у к е н г ш щ з х ъ,ф ы в а п р о л д ж э,я ч с м и т ь б ю'
    en_keyboard = 'q w e r t y u i o p,a s d f g h j k l,z x c v b n m'

    if lang == 'ru':
        keyboard = ru_keyboard.upper()
        blank = Editor('./files/photo/clear_keyboard.png')
    else:
        keyboard = en_keyboard.upper()
        blank = Editor('./files/photo/clear_keyboard_en.png')

    layer_counter = 0
    layer_counter_place = {0: 0, 1:1, 2:3}
    for layer in keyboard.split(','):
        place_counter = 0
        for word in layer.split(' '):
            block = None
            color = '#fff'
            if word in white_words:
                block = green_block
            elif word in try_words:
                block = yellow_block
            elif word in ban_words:
                block = black_block
                color = '#818384'
            if block:
                blank.paste(block, (113 * place_counter + 57 * layer_counter_place[layer_counter], 118 * layer_counter))
            up = 30
            if word in ['Й', 'Ё']:
                up = 20
            blank.text((113 * place_counter + 25 + 57 * layer_counter_place[layer_counter], 118 * layer_counter + up), word, font = font, color = color)
            place_counter += 1
        layer_counter += 1

    file = File(fp = blank.image_bytes, filename = "background.png")
    return file



def get_word(count_of_letters):

    url = f'https://vfrsute.ru/сканворд/слово-из-{count_of_letters}-букв/'
    base_url = f'https://vfrsute.ru/сканворд/{count_of_letters}-букв-первая-'


    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        words = soup.find_all('div', class_='words_group')
        letter = randint(1, len(words))
        word = words[letter]

        link = word.find('a').text[1]

        page = requests.get(base_url + link)

        soup = BeautifulSoup(page.text, 'html.parser')

        words = soup.find_all('li', class_='words_group-item')
        letter = randint(1, len(words))
        word = words[letter]
        word = word.find('a').text

    except:
        word = get_word(count_of_letters)

    return word.upper()
