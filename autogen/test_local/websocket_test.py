import autogen
import websockets
import asyncio
import json

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

llm_config = {"config_list": config_list_gpt4, "seed": 42}

# Define a function to handle WebSocket connections
async def handler(websocket, path):
    print(f"New connection: {websocket}")

    user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="A human admin.",
    max_consecutive_auto_reply=5,
    human_input_mode="TERMINATE",
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    websocket=websocket,
    )

    writer = autogen.AssistantAgent(
        name="Script Writer",
        system_message="You are a professional script writer. You do exactly what the user asks you to do. When you finish your task, add 'TERMINATE' to the end of your response.",
        llm_config=llm_config,
        websocket=websocket,
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
                await user_proxy.a_initiate_chat(writer, message=user_input)
            except Exception as e:
                await websocket.send(json.dumps({"system_output": f"An error occurred: {e}"}))
            # type exit to terminate the chat
        else:
            await websocket.send(json.dumps({"system_output": "Please input something."}))

start_server = websockets.serve(handler, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
print("WebSocket server is running on ws://localhost:8765")
asyncio.get_event_loop().run_forever()