from src.functions import newLog

async def boostPot(self, message):
    try:
        answer = 'Ускорьте чайничек у <@{0}> <a:lady:842748707522871326>'.format(message.author.id)
        await message.channel.send(answer, delete_after = 60 * 10)
        await message.delete()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
