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
'''
from youtube_dl import YoutubeDL
a = ['https://www.youtube.com/watch?v=QTIkudYT3mg',
    'https://www.youtube.com/watch?v=iVj5nLZZVN0',
    'https://www.youtube.com/watch?v=ZZjnfWx0cvw',
    'https://www.youtube.com/watch?v=hcAyxsR8DcU',]
with YoutubeDL() as ydl:
    for track in a:
        info = ydl.extract_info(track, download=False)
        print(info)
