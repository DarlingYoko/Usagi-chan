

from youtube_dl import YoutubeDL
from youtube_search import YoutubeSearch
from datetime import datetime, timedelta



def get_sec(time_str):
    time = [int(i) for i in time_str.split(':')]
    start = 1
    result = 0
    for per in time[::-1]:
        result += (per * start)
        start *= 60
    return result



track = 'Crystal Castles - Empathy'
results = YoutubeSearch(track, max_results=1).to_dict()

results[0]['duration'] = get_sec(results[0]['duration'])
print(results)
