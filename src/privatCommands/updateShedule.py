from openpyxl import load_workbook
from google.downloadFiles import downloadShedule
from src.functions import createEmbed


def getRussainDay(day):
    days = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник',
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
            }
    if day in days.keys():
        return days[day]
    return 0

def getRussainMonth(month):
    months = {
                'January':'Января',
                'February': 'Февраля',
                'March': 'Марта',
                'April': 'Апреля',
                'May': 'Мая',
                'June': 'Июня',
                'July': 'Июля',
                'August': 'Августа',
                'September': 'Сентября',
                'October': 'Октября',
                'November': 'Ноября',
                'December': 'Декабря'
    }
    if month in months.keys():
        return months[month]
    return 0

def updateShedule():

    if not downloadShedule():
        return 0

    wb = load_workbook('google/shedule.xlsx')
    embed = createEmbed(title = '> :film_frames: Действующее расписание сеансов :film_frames:', description = '> :timer: Всё время указано в Мск :timer:\n_ _\n_ _')

    sheet = wb['sheduleList']

    countCell = 5

    day = sheet.cell(row = countCell, column = 1).value

    while day:
        streamerCell = countCell
        streamer = sheet.cell(row = streamerCell, column = 4).value
        dayNumber = sheet.cell(row = countCell, column = 2).value.strftime('%A %d %B').split(' ')

        dayName, dayCount, monthName = getRussainDay(dayNumber[0]), int(dayNumber[1]), getRussainMonth(dayNumber[2])

        print(dayName, dayCount, monthName)

        fieldName = '<:Primogem:773640937196486658> {0} - *{1} {2}*'.format(dayName, dayCount, monthName)
        fieldValue = ''
        while streamer:
            titleName = sheet.cell(row = streamerCell, column = 5).value
            series = sheet.cell(row = streamerCell, column = 6).value
            time = sheet.cell(row = streamerCell, column = 7).value
            hall = sheet.cell(row = streamerCell, column = 8).value
            sound = sheet.cell(row = streamerCell, column = 9).value
            fieldValue += '<:Keqing:771095540456489020> Стримит: <@{0}> **{1}** ({2}) - {3} - **Зал {4}** - {5}'.format(int(streamer), titleName, series, time.strftime('%H:%M'), int(hall), sound)
            streamerCell += 1
            streamer = sheet.cell(row = streamerCell, column = 4).value

        fieldValue += '\n_ _\n_ _'
        embed.add_field(name = fieldName, value = fieldValue, inline = False)

        countCell = 2 + streamerCell
        day = sheet.cell(row = countCell, column = 1).value


    return embed
