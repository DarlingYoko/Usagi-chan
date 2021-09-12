
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

a = [(20, 'Сердце глубин', 'Цветок жизни', 20, 'HP', '4780', 'HP%', '25.0', 'EM', '83', 'ATK%', '15.0', 'CRIT RATE', '23.0', 'https://cdn.discordapp.com/attachments/877981304644304926/877984345648951336/Item_Gilded_Corsage.png', 1650),
	(44, 'Ступающий по лаве', 'Кубок пространства', 20, 'PYRO DMG', '46.6', 'CRIT RATE', '22.0', 'CRIT DMG', '7.8', 'ATK%', '5.4', 'ER', '6.5', 'https://cdn.discordapp.com/attachments/877981304644304926/877982655759650856/Item_Lavawalker27s_Epiphany.png', 1607),
	(42, 'Конец гладиатора', 'Кубок пространства', 20, 'ANEMO DMG', '46.6', 'CRIT DMG', '21.6', 'CRIT RATE', '7.8', 'HP%', '3.0', 'ER', '25.0', 'https://cdn.discordapp.com/attachments/877981304644304926/877981486517747782/Item_Gladiator27s_Intoxication.png', 1520),
	(43, 'Эмблема рассечённой судьбы', 'Перо смерти', 20, 'ATK', '311', 'CRIT RATE', '22.0', 'CRIT DMG', '7.8', 'ATK%', '5.4', 'ER', '6.5', 'https://cdn.discordapp.com/attachments/877981304644304926/877983794911666256/Item_Sundered_Feather.png', 1207),
	(40, 'Рыцарь крови', 'Перо смерти', 20, 'ATK', '311', 'DEF%', '5.0', 'HP%', '4.0', 'EM', '7', 'DEF', '8', 'https://cdn.discordapp.com/attachments/877981304644304926/877982780796063864/Item_Bloodstained_Black_Plume.png', 7),
	(39, 'Заблудший в метели', 'Корона разума', 20, 'HP%', '46.6', 'CRIT DMG', '1.0', 'CRIT RATE', '5.0', 'DEF', '1', 'EM', '9', 'https://cdn.discordapp.com/attachments/877981304644304926/877984370550526032/Item_Broken_Rime27s_Echo.png', 6),
	(36, 'Рыцарь крови', 'Цветок жизни', 20, 'HP', '4 780', 'HP%', '8.0', 'DEF', '81', 'ER', '5.0', 'CRIT RATE', '9.0', 'https://cdn.discordapp.com/attachments/877981304644304926/877982786881998938/Item_Bloodstained_Flower_of_Iron.png', 2),
	(35, 'Заблудший в метели', 'Корона разума', 20, 'CRIT DMG', '62.2', 'ATK%', '10.0', 'CRIT RATE', '10.5', 'EM', '25', 'ER', '5.2', 'https://cdn.discordapp.com/attachments/877981304644304926/877984370550526032/Item_Broken_Rime27s_Echo.png', 1)]
print(a)
