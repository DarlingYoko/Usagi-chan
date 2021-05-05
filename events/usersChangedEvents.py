from datetime import datetime, timedelta

def setUsersChangedEvents(self):
    @self.client.event
    async def on_member_join(member):
        self.members.addMember(member)
        if self.lastTimeJoin - member.created_at < timedelta(minutes = 1):
            self.spam += 1
        self.lastTimeJoin = member.created_at

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
        await channel.send('Алёрт! Зашло много акков зареганых в одно время')
        self.spam = 0
    return
