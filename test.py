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

async def ytSearch(loop):
    session = aiohttp.ClientSession()

    client = YoutubeClient(session)

    response = await client.search('A$AP Rocky Fukk Sleep (feat. FKA twigs)')
    print(response)

    await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(ytSearch(loop))
'''
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
