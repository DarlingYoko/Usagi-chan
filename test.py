
a = input()
nomer = int(input())

listUpper = 'АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ'
listLower = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'

dictUpperSymbols = {count:values for count, values in enumerate(listUpper)}
dictLowerSymbols = {count:values for count, values in enumerate(listLower)}

dictUpperValues = {values:count for count, values in enumerate(listUpper)}
dictLowerValues = {values:count for count, values in enumerate(listLower)}

string = ''

for i in a:
    if i in dictUpperSymbols.values():
        count = (dictUpperValues[i] + nomer) % len(dictUpperSymbols.values())
        string += dictUpperSymbols[count]

    elif i in dictLowerSymbols.values():
        count = (dictLowerValues[i] + nomer) % len(dictLowerSymbols.values())
        string += dictLowerSymbols[count]

    else:
        string += i

print(string)


# https://github.com/heroku/heroku-buildpack-chromedriver
# https://github.com/heroku/heroku-buildpack-google-chrome
