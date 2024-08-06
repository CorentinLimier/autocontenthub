import json
import os
import re

import boto3
import urllib3

PROMPT = """
Create an engaging and addictive game concept that can be played in about one minute. Game can end due to time limitation
or because character died.The game should be simple to understand and easy to play, encouraging players to retry to beat 
their high scores and climb the leaderboard. Players should use either the mouse to click or the keyboard to control 
the character (if applicable). The game must not rely on any images or audio, ensuring a purely text-based or minimalist visual experience.

Game Requirements:

Duration: Each game session should last around one minute.
Objective: Achieve the highest score possible within the time limit or before character dies.
Controls: Simple and intuitive controls using mouse clicks or keyboard inputs.
Replayability: The game should be highly replayable and addictive, motivating players to improve their scores.
Instructions: Clearly state the goal and basic instructions on the game page.
Leaderboard: At the end of each game, prompt the user to enter their nickname for the leaderboard.
State Management: Ensure the game state is reset properly when the player opts for a rematch.
Bug-Free: The game must be free of bugs to ensure a smooth user experience.

Provide the HTML/CSS/Javascript code to build the game. Basic instructions and controls should be added on top of the game, and
the score should be displayed.

Only return the code in your answer in one file that combines all.
"""


def openai_prompt(prompt: str, token: str) -> dict:
    # We use urllib3 to avoid installing openai or request package in AWS Lambda
    http = urllib3.PoolManager()
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": f"{prompt}"}],
        "temperature": 0.7,
    }

    encoded_data = json.dumps(data)

    response = http.request("POST", url, headers=headers, body=encoded_data)
    return json.loads(response.data)["choices"][0]["message"]["content"]


def extract_html_code(text: dict) -> str:
    code_regex = r"<html[\s\S]*</html>"
    html_code = re.findall(code_regex, text)[0]
    return html_code


def write_to_bucket(content: str, bucket: str, filename: str) -> None:
    s3 = boto3.client("s3")
    s3.put_object(Body=content, Bucket=bucket, Key=filename, ContentType="text/html")


def get_secret(secret_name: str) -> str:
    region_name = "eu-west-3"

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    return client.get_secret_value(SecretId=secret_name)["SecretString"]


def lambda_handler(event, context):
    openai_token = get_secret("openai")

    openai_response = openai_prompt(PROMPT, openai_token)
    code = extract_html_code(openai_response)

    bucket = os.environ["bucket_name"]
    filename = "index.html"
    write_to_bucket(code, bucket, filename)

    return {"statusCode": 200, "body": "File uploaded successfully."}


def local_test():
    openai_token = os.environ["OPENAI_API_KEY"]
    openai_response = openai_prompt(PROMPT, openai_token)
    print(openai_response)
    code = extract_html_code(openai_response)
    print(code)


if __name__ == "__main__":
    local_test()
