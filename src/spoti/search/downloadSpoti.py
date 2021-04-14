#! Basic necessities to get the CLI running
import argparse

# ! The actual download stuff
from src.spoti.download.downloader import DownloadManager
from src.spoti.search import spotifyClient
from src.spoti.search.songObj import SongObj
# ! Song Search from different start points
from src.spoti.search.utils import get_playlist_tracks, get_album_tracks, search_for_song


def downloadSpoti(url):
    '''
    This is where all the console processing magic happens.
    Its super simple, rudimentary even but, it's dead simple & it works.
    '''

    spotifyClient.initialize(
        clientId='118b5bcd3192449282a6618c19f70d50',
        clientSecret='6d3496fc16f54a1586036c06a813894a'
    )

    downloader = DownloadManager()


    if 'open.spotify.com' in url and 'track' in url:
        print('Fetching Song...')
        song = SongObj.from_url(url)

        if song.get_youtube_link() is not None:
            downloader.download_single_song(song)
        else:
            print('Skipping %s (%s) as no match could be found on youtube' % (
                song.get_song_name(), url
            ))

    elif 'open.spotify.com' in url and 'album' in url:
        print('Fetching Album...')
        songObjList = get_album_tracks(url)

        downloader.download_multiple_songs(songObjList)

    elif 'open.spotify.com' in url and 'playlist' in url:
        print('Fetching Playlist...')
        songObjList = get_playlist_tracks(url)

        downloader.download_multiple_songs(songObjList)

    elif url.endswith('.spotdlTrackingFile'):
        print('Preparing to resume download...')
        downloader.resume_download_from_tracking_file(url)

    else:
        print('Searching for song "%s"...' % url)
        try:
            song = search_for_song(url)
            downloader.download_single_song(song)

        except Exception:
            print('No song named "%s" could be found on spotify' % url)

    downloader.close()
