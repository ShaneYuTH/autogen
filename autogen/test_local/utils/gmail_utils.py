import os
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import base64
import os.path


# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.modify']

FUNCTIONS = [
    {
        "name": "fetch_unread_emails",
        "description": "Fetches unread emails from the user's Gmail account.",
        "parameters": {
                "type": "object",
                "properties": {}
        },
        "required": []
    },
    {
        "name": "send_email",
        "description": "Sends an email to specified recipients using the Gmail API.",
        "parameters": {
                "type": "object",
                "properties": {
                    "recipients": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "An email address of the recipient."
                        },
                        "description": "A list of email addresses of the recipients."
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the email."
                    },
                    "body": {
                        "type": "string",
                        "description": "The body of the email."
                    }
                }
        },
        "required": ["recipients", "subject", "body"]
    },
    {
        "name": "mark_emails_as_read",
        "description": "Marks emails as read in the user's Gmail account.",
        "parameters": {
                "type": "object",
                "properties": {
                    "email_ids": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "The ID of the email to be marked as read."
                        },
                        "description": "A list of email IDs to be marked as read."
                    }
                }
        },
        "required": ["email_ids"]
    },
]


def authenticate():
    """Authenticate and obtain credentials for the Gmail API.

    Args:
        token_path (str, optional): Path to the token.json file.
        credentials_path (str, optional): Path to the credentials.json file.

    Returns:
        google.oauth2.credentials.Credentials: The obtained credentials.
    """
    token_path = 'token.json'
    credentials_path = 'credentials.json'
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    return creds


def fetch_unread_emails():
    """Fetch all unread emails using the Gmail API.

    Args: None

    Returns:
        list: A list of dictionaries, each containing the following keys:
            - 'id': The unique identifier of the email.
            - 'data': The content of the email.
            - 'subject': The subject of the email.
            - 'sender': The sender's email address.
    """
    creds = authenticate()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])

        decoded_messages = []
        if not messages:
            print('No messages found.')
            return "No unread emails at this moment. <SUCCESS>"

        for message in messages:
            msg_id = message['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()

            # Extract subject and sender from headers
            headers = msg['payload']['headers']
            subject = next(
                (header['value'] for header in headers if header['name'] == 'Subject'), '')
            sender = next(
                (header['value'] for header in headers if header['name'] == 'From'), '')

            # Check if 'parts' field exists
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        decoded_data = base64.urlsafe_b64decode(
                            part['body']['data']).decode('utf-8')
                        decoded_messages.append(
                            {'id': msg_id, 'data': decoded_data, 'subject': subject, 'sender': sender})
            else:
                # Use 'snippet' field if 'parts' doesn't exist
                snippet = msg.get('snippet', '')
                decoded_messages.append(
                    {'id': msg_id, 'data': snippet, 'subject': subject, 'sender': sender})

        return str(decoded_messages) + " <SUCCESS>"

    except HttpError as error:
        # TODO(developer) - Handle errors from Gmail API.
        print(f'An error occurred: {error}')
        return "<ERROR>"  # Return an empty list in case of an error


def send_email(recipients, subject, body):
    """Sends an email using the Gmail API.

    Args:
        recipients (list): A list of email addresses of the recipients.
        subject (str): The subject of the email.
        body (str): The body of the email.

    Returns:
        dict: The sent message, in case of success.
        None: In case of an error.
    """
    creds = authenticate()

    try:
        # Create the email
        message = MIMEText(body)
        message['to'] = ', '.join(recipients)
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(
            message.as_string().encode('utf-8')).decode('utf-8')

        # Build the Gmail API service
        service = build('gmail', 'v1', credentials=creds)

        # Send the email
        sent_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()

        return sent_message + " <SUCCESS>"

    except HttpError as error:
        # TODO(developer) - Handle errors from Gmail API.
        print(f'An error occurred: {error}')
        return "<ERROR>"  # Return None in case of an error


def mark_emails_as_read(email_ids):
    """Mark emails as read in the user's Gmail account.

    Args:
        email_ids (list): A list of email IDs to be marked as read.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    creds = authenticate()

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)

        for email_id in email_ids:
            # Remove the 'UNREAD' label from the email
            service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

        return "<SUCCESS>"  # Operation was successful

    except HttpError as error:
        # TODO(developer) - Handle errors from Gmail API.
        print(f'An error occurred: {error}')
        return "<ERROR>"  # Operation failed
