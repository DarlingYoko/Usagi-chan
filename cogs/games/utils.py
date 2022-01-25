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



def get_word(length):

    # try:
    url = 'https://lexicography.online/explanatory/ozhegov/'
    base_url = 'https://lexicography.online'

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'}

    page = requests.get(url, headers=headers)
    # print(page.status_code)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.find('nav')
    letters = table.find_all('li')
    letter_id = randint(0, len(letters))
    letter_url = letters[letter_id].find('a')['href']
    # print(letter_url)

    page = requests.get(base_url + letter_url, headers=headers)

    soup = BeautifulSoup(page.text, 'html.parser')

    words = soup.find('section', class_ = 'a-list').find_all('a')
    words = [i.text for i in words]
    words = list(filter(lambda x: x.isalpha(), words))
    words = list(filter(lambda x: len(x) == length, words))

    word_id = randint(0, len(words))
    word = words[word_id]
    word.replace('ё', 'е')

    # except:
    #     return None

    return word.upper()
