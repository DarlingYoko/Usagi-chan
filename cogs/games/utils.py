from easy_pil import Editor, Canvas
from PIL import Image, ImageFont, ImageOps
from discord import File


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


def get_ban_words_keybord(ban_words, white_words, lang):
    ru_keyboard = '''> й ц у к е н г ш щ з х ъ
> ф ы в а п р о л д ж э
> я ч с м и т ь б ю'''
    en_keyboard = '''> q w e r t y u i o p
> a s d f g h j k l
> z x c v b n m'''

    keyboard = ru_keyboard.upper() if lang == 'ru' else en_keyboard.upper()

    for word in ban_words:
        if word in white_words:
            continue
        keyboard = keyboard.replace(word, f'||{word}||')

    for word in white_words:
        keyboard = keyboard.replace(word, f'**{word}**')

    return keyboard
