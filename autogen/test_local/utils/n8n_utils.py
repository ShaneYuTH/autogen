import requests

FUNCTIONS = [
    {
        "name": "n8n_create_google_doc",
        "description": "Create a Google Document via N8N workflow automation",
        "parameters": {
            "type": "object",
            "properties": {
                "docName": {
                    "type": "string",
                    "description": "The name of the document to be created."
                },
                "docContent": {
                    "type": "string",
                    "description": "The content to be placed in the document."
                },
                "uid": {
                    "type": "string",
                    "description": "The unique identifier for the user."
                }
            }
        },
        "required": ["docName", "docContent", "uid"]
    }
]


def n8n_create_google_doc(docName: str, docContent: str, uid: str):
    """Create a Google Document via N8N workflow automation

    Args:
        docName (str): The name of the document to be created.
        docContent (str): The content to be placed in the document.
        uid (str): The unique identifier for the user.

    Returns:
        dict: The API response data in case of success.
        None: In case of an error.
    """

    # Prepare data for the request to the automation endpoint
    data = {
        "credentials": [
            {
                "authType": 'googleDocsOAuth2Api',
                "cred": {
                    "clientId": "225497506970-cfi30vgbt9ghi99ivht9scsf3onbjkpq.apps.googleusercontent.com",
                    "clientSecret": "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",
                    "oauthTokenData": {
                        "access_token": 'ya29.a0AfB_byBlAdh0715rKWuSBazVx3KQIcV1kRS4Uy7XfpdyiSp-dx86u-Ki-g5SaA9VEx3N0a2ng84-YCWul_AplFeO81e6yzaHh8YZNP7CVZX9_t19yNA5LB1921X1PpA1v7-SBcXaCButbv2Z8qv_asgCHVtufl1Qs0w1aCgYKAe8SARESFQGOcNnCpf_CC5hVZcK7EKlo0deOGQ0171',
                        "refresh_token": '1//0dbwIR84-qgTeCgYIARAAGA0SNwF-L9IrtTuulHP1wPQLrKA4ezF0HoS0-hNU2DPkRqTP3lQju3VxjOkUBbqCYqEXhEYEZ6xIDAM'
                    }
                }
            }
        ],
        "param": {
            "docName": docName,
            "docContent": docContent
        },
        "templateID": 'eEHRrRw1WRMoidup',
        "uid": uid
    }
    try:
        # Make the request to the automation endpoint
        response = requests.post(
            'https://automation.hivespark.io/webhook/full-integration',
            json=data,
            headers={'Authorization': 'hivespark hive'}
        )

        # Check for a successful response
        return str(response.json()) + " <SUCCESS>"

    except Exception as e:
        # Log the error
        print(e)
        return str(e) + "<ERROR>"


# Example usage:
# result = n8n_create_google_doc('Document Title', 'Document Content', 'user_id')
# print(result)
