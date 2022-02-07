import pickle, shutil, io, datetime, sys, os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

def downloadShedule():
    # try:
    creds = None

    if os.path.exists('cogs/birthday/token.pickle'):
        with open('cogs/birthday/token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        # if creds and creds.expired and creds.refresh_token:
        #     creds.refresh(Request())
        # else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'cogs/birthday/creds.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open('cogs/birthday/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('drive', 'v3', credentials=creds, cache_discovery=False)

    file_name = 'cogs/birthday/birthdays.xlsx'
    file_id = '1rZJTV4B98wbN5fWt0nu4-aKOjqn0CvvYgMDltpjx9UY'
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

    # except Exception as e:
    #     exc_type, exc_obj, exc_tb = sys.exc_info()
    #     print(exc_type, exc_obj, exc_tb, e)
        # return 0
