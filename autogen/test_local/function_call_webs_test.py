import json
import websockets
import asyncio

import autogen
from utils.slack_utils import slack_post_message
from gmail_agents import process_gmail_request

async def handler(websocket, path):
    print(f"New connection: {websocket}")

    config_list_gpt4 = autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={
            "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
        },
    )

    def process_gmail_task(message):
        return process_gmail_request(message)


    def process_slack_task(message):
        return slack_post_message(message)


    llm_config = {
        "functions": [
            {
                "name": "process_gmail_task",
                "description": "Process a Gmail task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message describing the Gmail task, such as fetching unread emails, sending an email, or marking emails as read."
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "process_slack_task",
                "description": "Process a Slack task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message describing the Slack task, such as posting a message to a specified channel."
                        }
                    },
                    "required": ["message"]
                }
            }
        ],
        "config_list": config_list_gpt4,
        "request_timeout": 120,
    }

    assistant = autogen.AssistantAgent(
        name="assistant",
        llm_config=llm_config,
        system_message='''
        You are a helpful AI assistant. 
        You suggest solutions for processing Gmail tasks such as fetching unread emails, sending emails, and marking emails as read, as well as Slack tasks like posting messages to specified channels.
        
        For Gmail tasks, never assume anything that's not provided to you.
        When reading emails on user's behalf (including presenting email content/summary to user),
        always ask users if they want to mark certain emails or all emails as read. Do not mark emails as read without user's permission
        When reading emails on user's behalf (including presenting email content/summary to user),
        always label emails with priority (Priority: High/Medium/Low) and action required (Action required: Something/None) based on the content of the email.
        When presenting email, always follow the following format ang never assume anything that's not provided to you:
        1. Subject: <subject> (Priority: <priority>, Action required: <action required>) sent by <sender>
        Content: <summarization of content>
        When writing emails on user's behalf, make sure you have the recipients(email address only), subject, body, and/or attachment of the email before you continue to next step.
        If you need more information to complete the task, ask for more information. Do not assume anything that is not provided to you. This includes but not limit to recipients, subject, body, and/or attachment of the email.
        
        For Slack tasks, never assume anything that's not provided to you. 
        When posting messages, make sure you have the channel name and the content of the message before you continue to next step.
        If you need more information to complete the task, ask for more information. Do not assume anything that is not provided to you, this includes but not limit to channel, text, and/or attachments.
        ''',
        websocket=websocket,
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
        websocket=websocket,
    )

    user_proxy.register_function(
        function_map={
            "process_gmail_task": process_gmail_task,
            "process_slack_task": process_slack_task,
        }
    )

    async for message in websocket:
        print(f"Received message: {message} on {websocket}")

        try:
            # Deserialize the received message
            message_data = json.loads(message)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"system_output": "Invalid JSON format received."}))
            continue

        user_input = message_data.get("user_input")

        print("user_input: ", user_input)
        if user_input:
            try:
                await user_proxy.a_initiate_chat(assistant, message=user_input)
            except Exception as e:
                await websocket.send(json.dumps({"system_output": f"An error occurred: {e}"}))
            # type exit to terminate the chat
        else:
            await websocket.send(json.dumps({"system_output": "Please input something."}))

start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
print("WebSocket server is running on ws://localhost:8765")
asyncio.get_event_loop().run_forever()
