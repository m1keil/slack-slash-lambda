import os
import hmac
from urllib.parse import parse_qs
from functools import partial
from itertools import groupby

import requests
from requests.exceptions import RequestException


def lambda_handler(event, context):
    """
    lambda entry point
    """
    print(f"event: {event}")

    # verify request is from slack (skip when local)
    if "AWS_SAM_LOCAL" not in os.environ and not verify(
        key=os.environ["SLACK_KEY"].encode(),
        version="v0",
        timestamp=event["params"]["header"]["X-Slack-Request-Timestamp"],
        payload=event["payload"],
        signature=event["params"]["header"]["X-Slack-Signature"].split("=")[1],
    ):
        print("failed to verify Slack's message signature")
        return

    # parse payload params (url query style)
    params = parse_qs(event["payload"])
    response_url = params["response_url"][0]
    command = params["command"][0]

    callback = partial(send, response_url)

    # handle commands
    if command == "/cfp":
        get_sessions(callback, secret=os.environ["SESSIONISE_KEY"])
    elif command == "/tickets":
        get_tickets(
            callback,
            secret=os.environ["TITO_KEY"],
            org=os.environ["TITO_ORG"],
            slug=os.environ["TITO_EVENT"],
        )
    else:
        print("no command found")


def get_sessions(callback, secret):
    """
    get total submissions number and last 10 submissions titles
    """
    try:
        r = requests.get(f"https://sessionize.com/api/v2/{secret}/view/sessions")
        r.raise_for_status()
    except RequestException as e:
        print("error: ", e)
        callback("error while attempting to reach sessionize.com")
        return

    sessions = r.json()[0]["sessions"]
    content = f":star2: Number of talk submissions: *{len(sessions)}*\n"
    content += "\n"
    content += "recent submissions:\n"

    sorted_sess = sorted(sessions, key=lambda i: i["id"], reverse=True)
    for i, s in enumerate(sorted_sess[:5]):
        content += f"{i+1}. {s['title']}\n"

    callback(content)


def get_tickets(callback, secret, org, slug):
    """
    get number of tickets sold
    """
    def paginate():
        tickets = []
        curr = 1

        while True:
            r = requests.get(
                f"https://api.tito.io/v3/{org}/{slug}/tickets?page={curr}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Token token={secret}",
                },
            )
            r.raise_for_status()

            resp = r.json()
            tickets.extend(resp["tickets"])

            total = resp["meta"]["total_pages"]
            if curr == total:
                break
            curr += 1

        return tickets


    try:
        tickets = paginate()
    except RequestException as e:
        print("error: ", e)
        callback("error while attempting to reach ti.to")
        return

    tickets = sorted(tickets, key=lambda x: x["release_title"])
    groups = groupby(tickets, lambda x: x["release_title"])

    stats = [f"{k}: {len(list(g))}" for k, g in groups]
    content = f"Total sold: {len(tickets)}"
    content += "\n"
    content += "\n".join(stats)

    callback(content)


def send(url, content):
    payload = {"text": content}
    if url == "local":
        print(payload)
        return

    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
    except RequestException as e:
        print("error while sending callback to slack")
        raise e


def verify(*, key, version, timestamp, payload, signature):
    """
    verify slack message. see more:
    https://api.slack.com/docs/verifying-requests-from-slack#a_recipe_for_security
    """
    msg = f"{version}:{timestamp}:{payload}".encode()
    h = hmac.new(key, msg, "sha256")

    return hmac.compare_digest(h.hexdigest(), signature)
