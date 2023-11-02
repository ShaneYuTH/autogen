import asyncio
import autogen
import json

import socketio
import uvicorn

# Create a Socket.IO server
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", ping_timeout=240)
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

llm_config = {"config_list": config_list_gpt4, "seed": 42}

#  Connection event
@sio.event
async def connect(sid, environ):
    human_input_event = asyncio.Event()
    human_input_data = None

    print(f"New connection: {sid}")

    user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        system_message="A human admin.",
        max_consecutive_auto_reply=5,
        human_input_mode="TERMINATE",
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
        sid=sid,
        sio=sio,
        human_input_data=human_input_data,
        human_input_event=human_input_event,
    )

    writer = autogen.AssistantAgent(
        name="Script_writer",
        system_message="You are a professional script writer. You do exactly what the user asks you to do. When you finish your task, add 'TERMINATE' to the end of your response.",
        llm_config=llm_config,
        sid=sid,
        sio=sio,
        human_input_data=human_input_data,
        human_input_event=human_input_event,
    )

    translator = autogen.AssistantAgent(
        name="Chinese_translator",
        system_message="You are a professional translator. Your only job is translate the content produced by Script Writer into Chinese. When you finish your task, add 'TERMINATE' to the end of your response.",
        llm_config=llm_config,
        sid=sid,
        sio=sio,
        human_input_data=human_input_data,
        human_input_event=human_input_event,
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, writer, translator], messages=[], max_round=10
    )
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config=llm_config,
        sid=sid,
        sio=sio,
        human_input_data=human_input_data,
        human_input_event=human_input_event,
    )



    session_store[sid] = {
        "user_proxy": user_proxy,
        "writer": writer,
        "translator": translator,
        "manager": manager,
        "agents" : [user_proxy, writer, translator, manager],
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
    manager = session_data["manager"]

    user_input = data.get("user_input")

    print("user_input: ", user_input)
    if user_input:
        try:
            await user_proxy.a_initiate_chat(manager, message=user_input)
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
