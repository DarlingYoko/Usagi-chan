import shelve

data = shelve.open('db/valentineData')

for key in data.keys():
    print(key, data[key])
    print()
