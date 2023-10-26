import autogen

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
    },
)

llm_config = {"config_list": config_list_gpt4, "seed": 42}

# create an AssistantAgent instance named "assistant"
user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="A human admin.",
    max_consecutive_auto_reply=5,
    human_input_mode="TERMINATE",
    is_termination_msg=lambda x: x.get(
        "content", "").rstrip().endswith("TERMINATE"),
)

writer = autogen.AssistantAgent(
    name="Script_writer",
    system_message="You are a professional script writer. You do exactly what the user asks you to do. When you finish your task, add 'TERMINATE' to the end of your response.",
    llm_config=llm_config,
)

translator = autogen.AssistantAgent(
    name="Chinese_translator",
    system_message="You are a professional translator. Your only job is translate the content produced by Script Writer into Chinese. When you finish your task, add 'TERMINATE' to the end of your response.",
    llm_config=llm_config
)

groupchat = autogen.GroupChat(
    agents=[user_proxy, writer, translator], messages=[], max_round=10
)
manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config
)

user_proxy.initiate_chat(
    manager, message="Tell me an one-liner scary story")
