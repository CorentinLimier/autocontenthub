import datetime
import json
import os
import re

import boto3
import urllib3


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
    bucket = event["bucket"]
    folder = event["folder"]
    prompt = event["prompt"]

    openai_response = openai_prompt(prompt, openai_token)
    code = extract_html_code(openai_response)

    filename = f"{datetime.datetime.today().strftime('%Y%m%d')}.html"
    write_to_bucket(code, bucket, f"{folder}/{filename}")
    write_to_bucket(code, bucket, f"{folder}/index.html")

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
