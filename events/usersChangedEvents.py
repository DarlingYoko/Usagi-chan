

def setUsersChangedEvents(self):
    @self.client.event
    async def on_member_join(member):
        self.members.addMember(member)

    @self.client.event
    async def on_member_remove(member):
        self.members.removeMember(member)

    @self.client.event
    async def on_user_update(before, after):
        if before.name != after.name:
            self.members.updateName(after)

        if before.discriminator != after.discriminator:
            self.members.updateTag(after)
