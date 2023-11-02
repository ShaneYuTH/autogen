import autogen

from utils.slack_utils import slack_post_message
from utils.slack_utils import FUNCTIONS as SLACK_FUNCTIONS


def process_slack_request(message):
    config_list_gpt4 = autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={
            "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
        },
    )

    slack_llm_config = {
        "functions": SLACK_FUNCTIONS,
        "config_list": config_list_gpt4,
        "request_timeout": 120,
    }

    slack_assistant = autogen.AssistantAgent(
        name="slack_assistant",
        system_message='''You are the Slack Assistant. You are responsible for processing Slack tasks.
        Always check for <SUCCESS> or <ERROR> in the context, your response must ends with <SUCCESS> or <ERROR> if you see <SUCCESS> or <ERROR> in the context.
        For Slack tasks, only use the functions you have been provided with. Do not assume any functions.

        When post content on user's behalf, do not assume anything that is not provided to you. This includes but not limit to channel and content.
        If you need more information to complete the task, reply "REQUIRE ADDITIONAL INFO".''',
        llm_config=slack_llm_config,
    )

    slack_user_proxy = autogen.UserProxyAgent(
        name="slack_user_proxy",
        is_termination_msg=lambda x: x.get("content", "") and (
            x.get("content", "").rstrip().endswith("<SUCCESS>") or
            x.get("content", "").rstrip().endswith("<ERROR>") or
            x.get("content", "").rstrip().endswith("REQUIRE ADDITIONAL INFO")
        ),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
    )

    slack_user_proxy.register_function(
        function_map={
            "slack_post_message": slack_post_message,
        }
    )

    slack_user_proxy.initiate_chat(
        slack_assistant, message=message)

    return slack_user_proxy.last_message()["content"]
