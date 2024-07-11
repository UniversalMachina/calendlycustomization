import os
from datetime import timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Your provided credentials
CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')


def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            SCOPES
        )
        creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def book_calendar(event_details_list):
    creds = get_credentials()

    try:
        service = build('calendar', 'v3', credentials=creds)

        for event_details in event_details_list:
            event = {
                'summary': event_details['summary'],
                'description': event_details['description'],
                'start': {
                    'dateTime': event_details['start_time'].isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (event_details['start_time'] + timedelta(minutes=30)).isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [
                    {'email': event_details['invitee_email']},
                ],
            }

            event = service.events().insert(calendarId='primary', body=event).execute()
            print(f'Event created: {event.get("htmlLink")}')

    except HttpError as error:
        print(f'An error occurred: {error}')
