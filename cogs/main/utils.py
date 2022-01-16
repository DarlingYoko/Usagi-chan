from easy_pil import Editor, Canvas
from PIL import Image, ImageFont, ImageOps
from discord import File
import requests

def gen_pic(user, twitch):

    name = user['user_name']
    game = user['game_name']
    link = f'<https://www.twitch.tv/{user["user_login"]}>'
    text = f'**{name}** start stream!\n{link}'
    stream_name = user['title'].split(' ')
    title = []
    string = []
    for word in stream_name:
        if len(' '.join(string) + word) < 40:
            string.append(word)
        else:
            title.append(' '.join(string))
            string = [word]
    title.append(' '.join(string))

    viewer_count = str(user['viewer_count'])

    user_info = twitch.get_users(logins=[name])
    url = user_info['data'][0]['profile_image_url']

    blank = Image.open('./files/photo/stream.png')
    mask = Image.open('./files/photo/mask2.png').convert('L')
    image = Image.open(requests.get(url, stream=True).raw)

    background = Editor(Image.new('RGBA', (1050, 301), (255, 0, 0, 0)))

    font_bold = ImageFont.truetype(font = './files/fonts/Inter-Bold.ttf', size = 30)
    font_bold_big = ImageFont.truetype(font = './files/fonts/Inter-Bold.ttf', size = 40)
    font_light = ImageFont.truetype(font = './files/fonts/Inter-Light.ttf', size = 38)
    font_regular = ImageFont.truetype(font = './files/fonts/Inter-Regular.ttf', size = 38)



    output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)

    background.paste(blank, ((0, 0)))
    background.paste(output.resize((160, 160)), (42, 55))

    background.text((245, 60), name, font = font_bold_big, color = "white")
    for i in range(len(title)):
        background.text((245, 120 + i * 40), title[i], font = font_bold, color = "white")
    background.text((245, 170 + i * 40), game, font = font_regular, color = "#bf94ff")
    background.text((90, 255), viewer_count, font = font_bold_big, color = "#ff8280")


    file = File(fp = background.image_bytes, filename = "background.png")

    return text, file
