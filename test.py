import spotipy
import spotipy.oauth2 as oauth2
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials



CLIENT_ID = '118b5bcd3192449282a6618c19f70d50'
CLIENT_SECRET = '6d3496fc16f54a1586036c06a813894a'

auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
                                        client_secret = CLIENT_SECRET)


sp = spotipy.Spotify(auth_manager = auth_manager)


track_info = sp.track('67CXgSwER3AaTU67HhxJCO')

print(track_info['album']['artists'][0]['name'])
print(track_info['album']['name'])
