
async def createNewRole(self, message):
    if message.channel.id != self.config['data'].getint('getRoleChannel'):
        await message.channel.send('Эта команда для канала <#{0}>'.format(self.config['data'].getint('getRoleChannel')), delete_after = 30)
        await message.delete()
        return



    guild = await self.client.fetch_guild(self.config['data']['guildId'])
    member = message.author
    content = list(filter(None, message.content.split('!роль')[1].strip().split(' ')))


    if content[0] == 'добавить':
        color = content[-1]
        if '#' in color:
            color = color[1:]
        name = ' '.join(content[1:-1])
        try:
            role = await guild.create_role(name = name, colour=color, hoist = True, mentionable = True)
            await member.add_roles(role)
            await message.channel.send('Создала')
            return
        except Exception as e:
            await message.channel.send('Не получилось создать(')
            print('При создании роли ошибка\n', e)
            return

    if content[0] == 'удалить' or content[0] == 'изменить':
        try:
            role = guild.get_role(int(content[1][3:-1]))
        except Exception as e:
            await message.channel.send('Неверная роль')
            print(e)
            return


        if role in member.roles:
            if content[0] == 'удалить':
                await role.delete()
                await message.channel.send('Удалила')
                return

            if content[0] == 'изменить':
                if content[2] == 'название':
                    try:
                        await role.edit(name = ' '.join(content[3:]))
                        await message.channel.send('Изменила название')
                        return

                    except Exception as e:
                        await message.channel.send('Не получилось изменить название')
                        print(e)
                        return

                if content[2] == 'цвет':
                    try:
                        color = content[3]
                        if '#' in color:
                            color = color[1:]
                        await role.edit(colour = int(color, 16))
                        await message.channel.send('Изменила цвет')
                        return

                    except Exception as e:
                        await message.channel.send('Не получилось изменить цвет')
                        print(e)
                        return

        else:
            await message.channel.send('Это не твоя роль, бака!')
            return

    await message.channel.send('Не получилось(')

'''
!роль добавить "название" "цвет"
!роль удалить "ID роли"
!роль изменить "ID роли" "что надо изменить название/цвет" "новое название/цвет"
'''
