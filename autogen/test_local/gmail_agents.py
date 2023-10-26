import autogen

from utils.gmail_utils import fetch_unread_emails, send_email, mark_emails_as_read
from utils.gmail_utils import FUNCTIONS as GMAIL_FUNCTIONS


def process_gmail_request(message):
    config_list_gpt4 = autogen.config_list_from_json(
        "OAI_CONFIG_LIST",
        filter_dict={
            "model": ["gpt-4", "gpt-4-0314", "gpt4", "gpt-4-32k", "gpt-4-32k-0314", "gpt-4-32k-v0314"],
        },
    )

    gmail_llm_config = {
        "functions": GMAIL_FUNCTIONS,
        "config_list": config_list_gpt4,
        "request_timeout": 120,
    }

    gmail_assistant = autogen.AssistantAgent(
        name="gmail_assistant",
        system_message='''You are the Gmail Assistant. 
        Always check for <SUCCESS> or <ERROR> in the context, if you see either, you must also add <SUCCESS> or <ERROR> to the end of your response.
        For Gmail tasks, only use the functions you have been provided with. Do not assume any functions.
        
        If you receive content containg email id, you must keep it as part of your response. 
        When writing emails on user's behalf, do not assume anything that is not provided to you. This includes but not limit to recipients, subject, body, and attachment of the email.
        If you need more information to complete the task, reply "REQUIRE ADDITIONAL INFO".''',
        llm_config=gmail_llm_config,
    )

    gmail_user_proxy = autogen.UserProxyAgent(
        name="gmail_user_proxy",
        is_termination_msg=lambda x: x.get("content", "") and (
            x.get("content", "").rstrip().endswith("<SUCCESS>") or
            x.get("content", "").rstrip().endswith("<ERROR>") or
            x.get("content", "").rstrip().endswith("REQUIRE ADDITIONAL INFO")
        ),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
    )

    gmail_user_proxy.register_function(
        function_map={
            "fetch_unread_emails": fetch_unread_emails,
            "send_email": send_email,
            "mark_emails_as_read": mark_emails_as_read,
        }
    )

    gmail_user_proxy.initiate_chat(
        gmail_assistant, message=message)

    return gmail_user_proxy.last_message()["content"]
