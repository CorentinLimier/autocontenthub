import datetime
import json
import os
import re

import boto3
import urllib3
from boto3.dynamodb.conditions import Key


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


def put_dynamo_item(section: str, date: str, description: str) -> None:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("AutoContentHub")
    table.put_item(
        Item={
            "section": section,
            "date": date,
            "description": description,
        }
    )


def get_dynamo_last_items(folder: str) -> list[str]:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("AutoContentHub")
    response = table.query(
        KeyConditionExpression=Key("section").eq(folder),
        Limit=50,
        ScanIndexForward=False,
    )

    return [item["description"] for item in response["Items"]]


def get_secret(secret_name: str) -> str:
    region_name = "eu-west-3"

    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    return client.get_secret_value(SecretId=secret_name)["SecretString"]


def lambda_handler(event, context):
    openai_token = get_secret("openai")
    bucket = event["bucket"]
    folder = event["folder"]
    prompt = event["prompt"]

    last_assets = get_dynamo_last_items(folder)
    if last_assets:
        last_assets_str = "\n- ".join(last_assets)

        prompt += f"""
        The asset you generate should be different from the previous ideas that were : 
        - {last_assets_str}
        """

    prompt += """
    Your answer should be formatted like this and you need to respect this :
    - on the first line : provide a title and a brief description of what you generate
    - after, provide the html code of what you generate
    """

    print(prompt)

    openai_response = openai_prompt(prompt, openai_token)
    code = extract_html_code(openai_response)
    description = openai_response.split("\n")[0]

    today_str = datetime.datetime.today().strftime("%Y%m%d")

    filename = f"{today_str}.html"
    write_to_bucket(code, bucket, f"{folder}/{filename}")
    write_to_bucket(code, bucket, f"{folder}/index.html")
    put_dynamo_item(folder, today_str, description)

    return {"statusCode": 200, "body": "File uploaded successfully."}


def local_test():
    prompt = "Create a DataEngineering newsletter content in html. "
    openai_token = os.environ["OPENAI_API_KEY"]
    openai_response = openai_prompt(prompt, openai_token)
    print(openai_response)
    code = extract_html_code(openai_response)
    print(code)


if __name__ == "__main__":
    local_test()
