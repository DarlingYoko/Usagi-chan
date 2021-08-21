'''

import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials



CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                        client_secret = CLIENT_SECRET)


sp = spotipy.Spotify(auth_manager = auth_manager)


track_info = sp.playlist_tracks('435ZB2D4FILQ0drT1V6aPG')

#print(track_info['album']['artists'][0]['name'])
#print(track_info['name'])

for track in track_info['items']:
    if track['track']['id']:
        trackInfo = sp.track(track['track']['id'])
        track = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
        print(track)
    else:
        print(track['track']['name'])

    print()

from youtube_dl import YoutubeDL
a = 'https://www.youtube.com/watch_videos?video_ids=QTIkudYT3mg,ZZjnfWx0cvw'
with YoutubeDL() as ydl:
    info = ydl.extract_info(a, download=False)
    print(info['entries'])
'''

from ytpy import YoutubeClient
import asyncio
import aiohttp
'''
async def ytSearch(loop):
    session = aiohttp.ClientSession()

    client = YoutubeClient(session)

    response = await client.search('A$AP Rocky Fukk Sleep (feat. FKA twigs)')
    print(response)

    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(ytSearch(loop))

def construct_youtube_get_video_info_url(video_id):
    """
    Construct a YouTube API url for the get_video_id endpoint from a video ID.
    """
    base_parsed_api_url = urlparse("https://www.youtube.com/get_video_info")
    new_query = urlencode({"video_id": video_id})

    # As documented in the core Python docs, ._replace() is not internal, the
    # leading underscore is just to prevent name collisions with field names.
    new_parsed_api_url = base_parsed_api_url._replace(query=new_query)
    new_api_url = urlunparse(new_parsed_api_url)

    return new_api_url


print(construct_youtube_get_video_info_url('QTIkudYT3mg'))
'''
from youtube_search import YoutubeSearch
import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from threading import Thread
from time import sleep
import concurrent.futures
from multiprocessing import Process, freeze_support

CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                        client_secret = CLIENT_SECRET)


sp = spotipy.Spotify(auth_manager = auth_manager)

def search():

    playlistID = '4HlAmB7VZFZW5iPYapiqiz'
    offset = 0
    playlist_info = sp.album_tracks(playlistID, offset=offset, limit = 10)
    print(playlist_info['items'][0]['artists'][0]['name'] + ' ' + playlist_info['items'][0]['name'])
    return
    while playlist_info['items']:
        print(playlist_info['items'])
        offset += 100
        playlist_info = sp.playlist_tracks(playlistID, offset=offset)
    return
    res = []
    for track in playlist_info['items']:
        trackName = ''
        if track['track']['id']:
            trackInfo = sp.track(track['track']['id'])
            trackName = trackInfo['album']['artists'][0]['name'] + ' ' + trackInfo['name']
        else:
            trackName = track['track']['name']

        results = YoutubeSearch(trackName, max_results=1).to_dict()
        print(results)
        res.append(results[0]['url_suffix'].split('/watch?v=')[1])

    return res

async def cpu_bound():
    #await asyncio.sleep(5)
    return 2222222222222222222222222222


'''
async def main():
    loop = asyncio.get_running_loop()

    ## Options:

    # 1. Run in the default loop's executor:
    #result = await loop.run_in_executor(
    #    None, search)
    #print('default thread pool', result)
    #Thread(target = search, args=()).start()
    #Thread(target=cpu_bound, args=()).start()
    #executor = concurrent.futures.ProcessPoolExecutor(max_workers=3)
    #task1 = executor.submit(search)
    res = asyncio.run_coroutine_threadsafe(cpu_bound(), loop)
    await asyncio.sleep(1)
    print(res.result())




asyncio.run(main())

while True:
    sleep(1)
    print(1111111111111111111)
'''
#search()
'''
from youtube_dl import YoutubeDL
with YoutubeDL() as ydl:
    info = ydl.extract_info('https://youtu.be/meD4fFX9jKQ', download=False)
    print(info)
'''



import psycopg2

con = psycopg2.connect(
                            database = 'yoko_bot_test',
                            user = 'yoko_bot',
                            password = 'yoko_password',
                            host = '62.109.11.88',
                            port = '5432',
                            )

cur = con.cursor()

title = 'asd'
part = 'ljkghmghjk'
lvl = 100
main = ["12", "345"]
sub1 = ["2"]
sub2 = ["1"]
sub3 = ["34"]
sub4 = ["457"]



id = 5
cur.execute(f'SELECT * from artifacts where id = {id};')
con.commit()
print(cur.fetchall()[0])

range(0, 6, 2)

'''
with YoutubeDL(ydl_opts) as ydl:
    if type(URL) == list:
        links = []
        for urlik in URL:
            info = ydl.extract_info(urlik, download=False)
            for track in info['entries']:
                links.append(track)
'''
