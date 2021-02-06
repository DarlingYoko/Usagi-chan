class Members():
    def __init__(self, guildId):
        self.dict = {}
        self.guildId = guildId

    async def fillMembers(self):
        guild = await self.client.fetch_guild(self.guildId)
        membersDict = {}
        members = await guild.fetch_members(limit=None).flatten()
        for member in members:
            membersDict[member.id] = {'name': member.name, 'tag': member.discriminator}
        self.dict = membersDict

    def getMembers(self):
        return self.dict

    def setClient(self, client):
        self.client = client

    def removeMember(self, member):
        self.dict.pop(member.id)

    def addMember(self, member):
        self.dict[member.id] = {'name': member.name, 'tag': member.discriminator}

    def updateName(self, name, id):
        self.dict[id]['name'] = name

    def updateTag(self, tag, id):
        self.dict[id]['tag'] = tag

    def findByName(self, name, tag):
        for key, member in self.dict.items():
            if member['name'] == name and member['tag'] == tag:
                return key
        return 0
