import requests
from datetime import datetime, timedelta
import json

# Calendly API credentials
CLIENT_ID = os.getenv('CALENDLY_CLIENT_ID')
CLIENT_SECRET = os.getenv('CALENDLY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('CALENDLY_REDIRECT_URI')
TOKEN_FILE = 'calendly_tokens.json'

def get_authorization_url():
    return f"https://auth.calendly.com/oauth/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"


def get_tokens(auth_code):
    token_url = "https://auth.calendly.com/oauth/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(token_url, data=token_data)
    return response.json()


def refresh_token(refresh_token):
    token_url = "https://auth.calendly.com/oauth/token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    response = requests.post(token_url, data=token_data)
    return response.json()


def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)


def load_tokens():
    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def get_user_uri(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.calendly.com/users/me", headers=headers)
    return response.json()["resource"]["uri"]


def get_appointments(access_token, user_uri):
    headers = {"Authorization": f"Bearer {access_token}"}
    events_url = "https://api.calendly.com/scheduled_events"
    params = {
        "user": user_uri,
        "min_start_time": datetime.utcnow().isoformat(),
        "max_start_time": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "status": "active"
    }
    response = requests.get(events_url, headers=headers, params=params)
    return response.json()["collection"]


def get_invitee_details(access_token, event_uri):
    headers = {"Authorization": f"Bearer {access_token}"}
    invitees_url = f"{event_uri}/invitees"
    response = requests.get(invitees_url, headers=headers)
    invitees = response.json()["collection"]
    return invitees[0] if invitees else None


def fetch_appointments():
    tokens = load_tokens()

    if not tokens:
        print("Please visit this URL to authorize the application:", get_authorization_url())
        auth_code = input("Enter the authorization code: ")
        tokens = get_tokens(auth_code)
        save_tokens(tokens)

    # Check if access token is expired
    if datetime.now().timestamp() > tokens['created_at'] + tokens['expires_in']:
        print("Access token expired, refreshing...")
        new_tokens = refresh_token(tokens['refresh_token'])
        tokens.update(new_tokens)
        save_tokens(tokens)

    user_uri = get_user_uri(tokens['access_token'])
    appointments = get_appointments(tokens['access_token'], user_uri)

    event_details_list = []

    if appointments:
        print("Your upcoming appointments:")
        for appointment in appointments:
            start_time = datetime.fromisoformat(appointment["start_time"].replace("Z", "+00:00"))
            invitee = get_invitee_details(tokens['access_token'], appointment["uri"])

            print(f"\n- Event: {appointment['name']}")
            print(f"  Date: {start_time.strftime('%Y-%m-%d at %H:%M')} UTC")
            print(f"  Description: {appointment.get('description', 'No description provided')}")

            if invitee:
                print(f"  Invitee Name: {invitee['name']}")
                print(f"  Invitee Email: {invitee['email']}")
            else:
                print("  Invitee details not available")

            event_details_list.append({
                'summary': appointment['name'],
                'description': appointment.get('description', 'No description provided'),
                'start_time': start_time,
                'invitee_email': invitee['email'] if invitee else None
            })
    else:
        print("You have no upcoming appointments in the next 30 days.")

    return event_details_list
