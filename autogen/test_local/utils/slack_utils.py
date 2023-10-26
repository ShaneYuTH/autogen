import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi

FUNCTIONS = [
    {
        "name": "slack_post_message",
        "description": "Post a message to a specified Slack channel.",
        "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "The channel to post the message to."
                    },
                    "text": {
                        "type": "string",
                        "description": "The message text."
                    }
                }
        },
        "required": ["channel", "text"]
    }
]


def slack_auth():
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    client = WebClient(
        # TODO: Temperary, need to change token to a seperate file
        token="xoxp-5984641757943-5996253060773-5999338361490-e6005c577c904eef28b3763fba154ff2", ssl=ssl_context
    )

    return client


def slack_post_message(channel, text):
    """Post a message to a specified Slack channel.

    Args:
        channel (str): The channel to post the message to.
        text (str): The message text.

    Returns:
        dict: The API response data in case of success.
        None: In case of an error.
    """

    client = slack_auth()

    try:
        response = client.chat_postMessage(channel=channel, text=text)
        return response.data + " <SUCCESS>"
    except SlackApiError as e:
        logging.error(f"Error posting message: {e.response['error']}")
        return "<ERROR>"
