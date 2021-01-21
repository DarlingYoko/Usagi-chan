import discord

def createEmbed(title, description, color, urlImage = None, thumbnail = None):
    embed = discord.Embed(title = title, description = description, color = color)
    if urlImage:
        embed.set_image(url = urlImage)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    return embed
