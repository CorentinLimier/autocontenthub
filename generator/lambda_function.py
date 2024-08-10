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


def write_to_bucket(content: str, bucket: str, filename: str) -> None:
    s3 = boto3.client("s3")
    s3.put_object(Body=content, Bucket=bucket, Key=filename, ContentType="text/html")


def put_dynamo_item(section: str, date: str, title: str, description: str) -> None:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("AutoContentHub")
    table.put_item(
        Item={
            "section": section,
            "date": date,
            "title": title,
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

    return [f'{item["title"]}: {item["description"]}' for item in response["Items"]]


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
    Your answer should be ONLY a json with following structure : 
    {
        "title": "title of the asset generated",
        "description": "A catchy description of the asset in 2 or 3 sentences",
        "html": "html code of the generated asset"
    }
    Don't wrap the json by "```"
    """

    openai_response = json.loads(openai_prompt(prompt, openai_token))
    code = openai_response["html"]
    title = openai_response["title"]
    description = openai_response["description"]

    today_str = datetime.datetime.today().strftime("%Y%m%d")
    today_str = "20240811"

    filename = f"{today_str}.html"
    write_to_bucket(code, bucket, f"{folder}/{filename}")
    write_to_bucket(code, bucket, f"{folder}/index.html")
    put_dynamo_item(folder, today_str, title, description)

    return {"statusCode": 200, "body": "File uploaded successfully."}


def local_test():
    prompt = """
      Create an article for developers. 
      Find a topic/ a technology that is specific and develop it. 
      Article should rely on concrete examples and codes snippets if applicable.
      I want a definitive verison that I can directly publish on my website. 
      The output should be in one html file. Make to escape html characters 
      inside code blocks if applicable.
    """
    prompt += """
    Your answer should be ONLY a json with following structure : 
    {
        "title": "title of the asset generated",
        "description": "A catchy description of the asset in 2 or 3 sentences",
        "html": "html code of the generated asset"
    }
    Don't wrap the json by "```"
    """
    openai_token = os.environ["OPENAI_API_KEY"]
    openai_response = openai_prompt(prompt, openai_token)
    print(openai_response)
    print(json.loads(openai_response)["html"])


if __name__ == "__main__":
    local_test()
