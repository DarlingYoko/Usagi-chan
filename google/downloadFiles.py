import pickle, shutil, io, datetime, sys
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io
from googleapiclient.http import MediaIoBaseDownload
from src.functions import newLog

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def downloadShedule():
    try:
        creds = None

        if os.path.exists('google/token.pickle'):
            with open('google/token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'googlecreds.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('google/token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('drive', 'v3', credentials=creds, cache_discovery=False)


        file_name = 'google/shedule.xlsx'
        file_id = '10c4NhBgVtJQfyKP6vQrpSoB7g0HhnbwVjP4AoX7C6XU'
        request = service.files().export_media(fileId=file_id,
                                                 mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        fh.seek(0)
        with open(file_name, 'wb') as f:
            shutil.copyfileobj(fh, f)


        return 1

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        newLog(exc_type, exc_obj, exc_tb, e)
        return 0
