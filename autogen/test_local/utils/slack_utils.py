import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import ssl
import certifi
import json

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
                    "content": {
                        "type": "string",
                        "description": "The message content."
                    }
                }
        },
        "required": ["channel", "content"]
    }
]


def slack_auth():
    with open("slack_token.json") as f:
        data = json.load(f)

    token = data["user_oauth_token"]
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    client = WebClient(
        token=token, ssl=ssl_context
    )

    return client


def slack_post_message(channel, content):
    """Post a message to a specified Slack channel.

    Args:
        channel (str): The channel to post the message to.
        content (str): The message content.

    Returns:
        dict: The API response data in case of success.
        None: In case of an error.
    """

    client = slack_auth()

    try:
        response = client.chat_postMessage(channel=channel, text=content)
        return str(response.data) + " <SUCCESS>"
    except SlackApiError as e:
        logging.error(f"Error posting message: {e.response['error']}")
        return "<ERROR>"
