
'''

weights = {'hp': 0, 'atk': 0.5, 'atk%': 1, 'er%': 0.5, 'em': 0.5,
			   'phys%': 1, 'cr%': 1, 'cd%': 1, 'elem%': 1,
			   'hp%': 0, 'df%': 0, 'df': 0, 'heal%': 0}


max_mains = {'hp': 4780, 'atk': 311.0, 'atk%': 46.6, 'er%': 51.8, 'em': 187.0,
				 'phys%': 58.3,  'cr%': 31.1, 'cd%': 62.2, 'elem%': 46.6,
				 'hp%': 46.6, 'df%': 58.3, 'heal%': 35.9}


max_subs = {'atk': 19.0, 'em': 23.0, 'er%': 6.5, 'atk%': 5.8,
				'cr%': 3.9, 'cd%': 7.8, 'df': 23.0, 'hp': 299.0, 'df%': 7.3, 'hp%': 5.8}



subs = {
    'cr%': 22.0,
    'cd%': 7.8,
    'atk%': 5.4,
    'er%': 6.5,
}

sub_score = 0
main = 'elem%'
level = 20
main_score = weights[main] * 100 * (3 + level / 4)


for key, value in subs.items():
    sub_score += value/max_subs[key] * weights[key] * 100

print(main_score, sub_score)
score = main_score + sub_score
max = 1650
print(f'Gear score: {int(score)} ({(score * 100 / max):.2f}%)')
'''

import cv2
import pytesseract

# Путь для подключения tesseract
pytesseract.pytesseract.tesseract_cmd = 'C:\\Users\\zarte\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'

# Подключение фото
img = cv2.imread('./files/photo/test1.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Будет выведен весь текст с картинки
config = r''#--oem 3 --psm 6'
print(pytesseract.image_to_string(img, config=config, lang="eng"))

# Делаем нечто более крутое!!!

data = pytesseract.image_to_data(img, config=config, lang="eng")

# Перебираем данные про текстовые надписи
for i, el in enumerate(data.splitlines()):
	if i == 0:
		continue

	el = el.split()
	try:
		# Создаем подписи на картинке
		x, y, w, h = int(el[6]), int(el[7]), int(el[8]), int(el[9])
		cv2.rectangle(img, (x, y), (w + x, h + y), (0, 0, 255), 1)
		cv2.putText(img, el[11], (x, y), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 1)
	except IndexError:
		print("Операция была пропущена")

# Отображаем фото
cv2.imshow('Result', img)
cv2.waitKey(0)
