import shelve

data = shelve.open('db/emojiData')


for key in data.keys():
    print(key, data[key])
    print()

data = shelve.open('db/requestsData')

for key in data.keys():
    print(key, data[key])
    print()
