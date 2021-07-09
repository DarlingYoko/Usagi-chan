from datetime import datetime as dt


now = dt.now()
time = 1635653097.0
time = dt.fromtimestamp(float(time))
print(time)

d = time - now
hours = d.seconds // 3600
minutes = (d.seconds - (hours * 3600)) // 60
print(hours)
print(d)
print('{0} дней {1} часов {2} минуты'.format(d.days, hours, minutes))
