import requests


kefeh_url = "https://hooks.slack.com/services/T2someCharactersForNotiff"


def post_to_channel(webhook_url: str, message: str):

    """
    Function sends a slack notification to a channel or user
    :param webhook_url: The web hook url of the user or the channel
    :param message:The message that should be sent to user
    :return:
    """

    try:
        response = requests.post(url=webhook_url, json={'text': message})
        if response.status_code != 200:
            return "Failed to send message. Status code:{}".format(response.status_code)

        else:
            return "Message successfully sent to channel"

    except Exception as ex:
        return "Failed to send message because of {}".format(ex)
