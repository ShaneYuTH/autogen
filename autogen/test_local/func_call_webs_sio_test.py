import asyncio
import autogen
import json

import socketio
import uvicorn

from slack_agents import process_slack_request
from gmail_agents import process_gmail_request

# Create a Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
# TODO: Change cors_allowed_origins for production
app = socketio.ASGIApp(sio)

session_store = {}
# human_input_event = asyncio.Event()
# human_input_data = None

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

def process_gmail_task(message):
    return process_gmail_request(message)


def process_slack_task(message):
    return process_slack_request(message)

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

#  Connection event
@sio.event
async def connect(sid, environ):
    human_input_event = asyncio.Event()
    human_input_data = None

    print(f"New connection: {sid}")

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
        When presenting email, always follow the following format and never assume anything that's not provided to you:
        1. Subject: <subject> (Priority: <priority>, Action required: <action required>) sent by <sender>
        Content: <summarization of content>
        When writing emails on user's behalf, make sure you have the recipients(email address only), subject, body, and/or attachment of the email in the message before you continue to next step.
        If you need more information to complete the task, ask for more information. Do not assume anything that is not provided to you. This includes but not limit to recipients, subject, body, and/or attachment of the email.
        When marking emails as read, make sure your output has following format: "mark email <email id> as read" before you continue to next step.
        
        For Slack tasks, never assume anything that's not provided to you. 
        When posting messages, make sure you have the channel name (label as channel) and the content (label as content) in the message before you continue to next step.
        If you need more information to complete the task, ask for more information. Do not assume anything that is not provided to you, this includes but not limit to channel, content, and/or attachments.
        ''',
        sid=sid,
        sio=sio,
        human_input_data=human_input_data,
        human_input_event=human_input_event,
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        is_termination_msg=lambda x: x.get("content", "") and x.get(
            "content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
        sid=sid,
        sio=sio,
        human_input_data=human_input_data,
        human_input_event=human_input_event,
    )

    user_proxy.register_function(
        function_map={
            "process_gmail_task": process_gmail_task,
            "process_slack_task": process_slack_task,
        }
    )

    session_store[sid] = {
        "user_proxy": user_proxy,
        "assistant": assistant,
        "agents" : [user_proxy, assistant],
        # TODO: Try to fix in seesion_store, put AsyncIOevent in session store
        # "human_input_event": human_input_event,
        # "human_input_data": human_input_data,
    }

    # user_proxy.session_store = session_store
    # writer.session_store = session_store
    # translator.session_store = session_store
    # manager.session_store = session_store

# Handle user input
@sio.on('user_input')
async def user_input(sid, data):
    print(f"Received user input: {data} on {sid}")

    session_data = session_store.get(sid)

    if not session_data:
        await sio.emit('system_output', {"system_output": "Session not found."}, room=sid)
        return

    user_proxy = session_data["user_proxy"]
    assistant = session_data["assistant"] 

    user_input = data.get("user_input")

    print("user_input: ", user_input)
    if user_input:
        try:
            await user_proxy.a_initiate_chat(assistant, message=user_input)
        except Exception as e:
            await sio.emit('system_output', {"system_output": f"An error occurred: {e}"}, room=sid)
        # type exit to terminate the chat
    else:
        await sio.emit('system_output', {"system_output": "Please input something."}, room=sid)

@sio.on("user_input_follow")
async def on_user_input_follow(sid, data):
    # print(f"DEBUG: on_user_input_follow: args: {args}, kwargs: {kwargs}")

    print(f"DEBUG: _on_user_input_follow: sid: {sid}, data: {data}")

    user_input = data.get("user_input")
    agents = session_store[sid]["agents"]

    for a in agents:
        a.setUserInput(user_input)


    # !!DEBUG LOGGING!! nuo dao init xia mian
    # # self.loop = asyncio.get_event_loop()
    # print(f"DEBUG: _on_user_input_follow: user_input: {self._human_input_data}")
    # # inside _on_user_input_follow
    # print("DEBUG: About to set _human_input_event")
    # self.loop.call_soon_threadsafe(self._human_input_event.set)
    # # self._human_input_event.set()
    # print("DEBUG: Set _human_input_event")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)

# Define a function to handle WebSocket connections
# async def handler(websocket, path):
#     print(f"New connection: {websocket}")

    # user_proxy = autogen.UserProxyAgent(
    #     name="User_proxy",
    #     system_message="A human admin.",
    #     max_consecutive_auto_reply=5,
    #     human_input_mode="TERMINATE",
    #     is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    #     websocket=websocket,
    # )

#     writer = autogen.AssistantAgent(
#         name="Script_writer",
#         system_message="You are a professional script writer. You do exactly what the user asks you to do. When you finish your task, add 'TERMINATE' to the end of your response.",
#         llm_config=llm_config,
#         websocket=websocket,
#     )

#     translator = autogen.AssistantAgent(
#         name="Chinese_translator",
#         system_message="You are a professional translator. Your only job is translate the content produced by Script Writer into Chinese. When you finish your task, add 'TERMINATE' to the end of your response.",
#         llm_config=llm_config,
#         websocket=websocket,
#     )

#     groupchat = autogen.GroupChat(
#         agents=[user_proxy, writer, translator], messages=[], max_round=10
#     )
#     manager = autogen.GroupChatManager(
#         groupchat=groupchat,
#         llm_config=llm_config,
#         websocket=websocket,
#     )
    
#     async for message in websocket:
#             print(f"Received message: {message} on {websocket}")

#             try:
#                 # Deserialize the received message
#                 message_data = json.loads(message)
#             except json.JSONDecodeError:
#                 await websocket.send(json.dumps({"system_output": "Invalid JSON format received."}))
#                 continue

#             user_input = message_data.get("user_input")

#             print("user_input: ", user_input)
#             if user_input:
#                 try:
#                     await user_proxy.a_initiate_chat(manager, message=user_input)
#                 except Exception as e:
#                     await websocket.send(json.dumps({"system_output": f"An error occurred: {e}"}))
#                 # type exit to terminate the chat
#             else:
#                 await websocket.send(json.dumps({"system_output": "Please input something."}))

# start_server = websockets.serve(handler, "localhost", 8765)

# asyncio.get_event_loop().run_until_complete(start_server)
# print("WebSocket server is running on ws://localhost:8765")
# asyncio.get_event_loop().run_forever()
