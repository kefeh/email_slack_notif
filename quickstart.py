from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from slack_notifications import kefeh_url, post_to_channel
import json
from pprint import pprint
import time
from time import sleep
from datetime import datetime, timedelta
import os
basedir = os.path.abspath(os.path.dirname(__file__))


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# user holds the current user
user = 'me'
LAST_ID_GMAIL = f'{basedir}/last_id_gmail.json'
# the token.pickel file holds the credentials and you need to deploy it to server to be able to
# access your email from the server
TOKEN_PICKLE = f"{basedir}/token.pickle"
CREDENTIALS = f"{basedir}/credentials.json"
#Edit the senders' email to get notifications from the particular email
SENDER = "somesender@email.com"


def get_last_saved_id():
    """
    This function opens the last_id_gmail, gets and returns the last email id
    return:
        str (string on integers)
    """
    prev_id= {}
    try:
        with open(LAST_ID_GMAIL, "r") as f:
            prev_id = json.load(f)
    except:
        pass

    return prev_id.get("prev_id", None)


def save_last_id(id):
    """
    This function gets an id and saves it to the last_id_gmail json file.
    params:
        str
    return:
        no return value
    """
    try:
        with open(LAST_ID_GMAIL, "w") as f:
            json.dump({"prev_id":id}, f, ensure_ascii=False, indent=4)
    except Exception as exp:
        print(exp)


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS, SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    # threads = service.users().threads().list(userId='me', labelIds=['CATEGORY_PROMOTIONS']).execute()
    # In this loop we continuesly querrying Gmail every 10secs to mail if there is a mail that specifies a email
    # we handle that new review and send a slack notification
    while True:
        messageId = get_last_saved_id()
        post_message = ''
        post_time = ''
        new_msg_id: list = []
        # all_mesages = service.users().messages().list(userId='me', labelIds=['CATEGORY_PROMOTIONS'], maxResults=1).execute()
        message_thread = service.users().threads().list(userId='me', labelIds=['CATEGORY_PROMOTIONS'],  maxResults=10).execute()
        length = len(message_thread['threads']) - 1
        message = message_thread.get('threads')
        for i in range(length + 1):
            text = message[i]
            thread_id = text['id']
            message_thread = service.users().threads().get(userId='me', id=thread_id, format='minimal').execute()
            check = False
            for msg in message_thread['messages']:
                if messageId == msg['id']:
                    check = True
                if check:
                    new_msg_id.append(msg['id'])
            if messageId in new_msg_id:
                print(new_msg_id)
                new_msg_id.remove(messageId)
                break
                # pprint(message_thread['messages'])
        last_msg_id = new_msg_id[-1] if new_msg_id else messageId
        if not new_msg_id:
            new_msg_id.append(messageId)
        for message_id in new_msg_id:
            mesages = service.users().messages().get(userId='me', id=message_id).execute()
            # using <@kefeh> where kefeh is my slack name,it enables mentions and notifications,even in a channel 
            post_message = "<@kefeh> you have a new email"
            count = 0
            for value in mesages['payload'].get('headers'):
                if value['name'] == 'X-Received' and count == 0:
                    post_time = f"Received at: {value['value'].split(';')[1].lstrip()} WAT-9"
                    print(post_time)
                    count = count + 1
            notify = f"Hello {post_message}\n{post_time}\n"
            # Notify user when project has been assigned to me
            post_status_result = post_to_channel(webhook_url=kefeh_url, message=notify)
            print(post_status_result)
            save_last_id(last_msg_id)
        # sleep for 10seconds and then restart the process all over
        sleep(10)
                


if __name__ == '__main__':
    main()
