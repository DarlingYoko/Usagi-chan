import discord

def createEmbed(title, description, color, urlImage = None, thumbnail = None):
    embed = discord.Embed(title = title, description = description, color = color)
    if urlImage:
        embed.set_image(url = urlImage)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    return embed


async def delMsg(client, channelID, msgID):
    channel = client.get_channel(733631069542416387)
    msg = await channel.fetch_message(801580586636279840)
    await msg.delete()
