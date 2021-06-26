
async def createNewRole(self, message):
    if message.channel.id != self.config['data'].getint('getRoleChannel'):
        await message.channel.send('Эта команда для канала <#{0}>'.format(self.config['data'].getint('getRoleChannel')), delete_after = 30)
        await message.delete()
        return


    guild = await self.client.fetch_guild(self.config['data']['guildId'])
    member = message.author
    content = message.content.split('!роль')[1].strip().split(' ')
    color = int(content[-1], 16)
    name = ' '.join(content[:-1])

    try:
        role = await guild.create_role(name = name, colour=color, hoist = True)
        await member.add_roles(role)
        await member.channel.send('Создала')
    except Exception as e:
        await member.channel.send('Не получилось создать(')
        print('При создании роли ошибка\n', e)
