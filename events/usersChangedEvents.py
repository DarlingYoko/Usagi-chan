from datetime import datetime, timedelta

def setUsersChangedEvents(self):
    @self.client.event
    async def on_member_join(member):
        self.members.addMember(member)
        time = datetime.now()
        if time - member.created_at < timedelta(days = 7):
            self.spam += 1

    @self.client.event
    async def on_member_remove(member):
        self.members.removeMember(member)

    @self.client.event
    async def on_user_update(before, after):
        if before.name != after.name:
            self.members.updateName(after)

        if before.discriminator != after.discriminator:
            self.members.updateTag(after)


async def reportSpam(self):
    if self.spam >= 3:
        channel = await self.client.fetch_channel(770802979867328523)
        await channel.send('Алёрт! Зашло много акков зареганых меньше недели назад')
        self.spam = 0
    return
