from datetime import datetime

class Members():
    def __init__(self, guildId):
        self.dict = {}
        self.guildId = guildId

    async def fillMembers(self, client):
        guild = await client.fetch_guild(self.guildId)
        membersDict = {}
        members = await guild.fetch_members(limit=None).flatten()
        for member in members:
            membersDict[member.id] = {'name': member.name, 'tag': member.discriminator, 'lastMsg': datetime.now()}
        self.dict = membersDict

    def getMembers(self):
        return self.dict

    def getMember(self, id):
        return self.dict[id]

    def setClient(self, client):
        self.client = client

    def removeMember(self, member):
        self.dict.pop(member.id)

    def addMember(self, member):
        self.dict[member.id] = {'name': member.name, 'tag': member.discriminator, 'lastMsg': datetime.now()}

    def updateName(self, member):
        self.dict[member.id]['name'] = member.name

    def updateTag(self, member):
        self.dict[member.id]['tag'] = member.discriminator

    def findByName(self, name, tag):
        for key, member in self.dict.items():
            if member['name'] == name and member['tag'] == tag:
                return key
        return 0
