import datetime

import boto3
from boto3.dynamodb.conditions import Key

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoContentHub {subpage}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            width: 90%;
            max-width: 800px;
            margin: 20px auto;
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .article {{
            border-bottom: 1px solid #ddd;
            padding: 15px 0;
        }}
        .article:last-child {{
            border-bottom: none;
        }}
        .theme {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        .title {{
            font-size: 1.5em;
            font-weight: bold;
            color: #007BFF;
            margin-left: 10px;
        }}
        .title_sub {{
            font-weight: bold;
            white-space: nowrap;
        }}
        .title_main {{
            color: #007BFF;
            font-weight: bold;
        }}
        .description {{
            font-size: 1em;
            margin: 10px 0 0 0;
            color: #555;
        }}
        footer {{
            text-align: center;
            margin-top: 20px;
            font-size: 0.9em;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1><a href="/"><span class="title_main">AutoContentHub</soan></a><span class="title_sub"> {subpage}</span></h1>
        {assets}
    </div>
</body>
</html>
"""

asset_template = """
            <div class="article">
                <div>
                <a href="/{section}"><span class="theme">#{section}</a>
                <a href="/{section}/{date}.html"><span class="title">{title}</span></a>
                </div>
                <p class="description">{description}</p>
            </div>
"""


def get_assets_by_date(date: datetime.datetime) -> dict:
    date_str = date.strftime("%Y%m%d")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("AutoContentHub")
    response = table.query(
        IndexName="date-index",
        KeyConditionExpression=Key("date").eq(date_str),
    )
    return {"date": date, "assets": response["Items"]}


def get_assets_by_section(section: str) -> list[str]:
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("AutoContentHub")
    response = table.query(
        KeyConditionExpression=Key("section").eq(section),
        Limit=100,
        ScanIndexForward=False,
    )

    return {"section": section, "assets": response["Items"]}


def generate_main_html(data: dict) -> str:
    assets_str = ""
    for asset in data["assets"]:
        assets_str += asset_template.format(
            section=asset["section"],
            date=data["date"].strftime("%Y%m%d"),
            title=asset["title"],
            description=asset["description"],
        )

    result = html_template.format(
        subpage=f'[{data["date"].strftime("%Y-%m-%d")}]',
        assets=assets_str,
    )
    return result


def generate_section_html(data: dict) -> str:
    assets_str = ""
    for asset in data["assets"]:
        assets_str += asset_template.format(
            section=asset["section"],
            date=asset["date"],
            title=asset["title"],
            description=asset["description"],
        )
    result = html_template.format(subpage=f"[#{asset['section']}]", assets=assets_str)
    return result


def write_to_bucket(content: str, bucket: str, filename: str) -> None:
    s3 = boto3.client("s3")
    s3.put_object(Body=content, Bucket=bucket, Key=filename, ContentType="text/html")


def lambda_handler(event, context):
    bucket = event["bucket"]
    today = datetime.datetime.today()

    data = get_assets_by_date(today)
    html = generate_main_html(data)

    write_to_bucket(html, bucket, f"index.html")
    write_to_bucket(html, bucket, f"{today.strftime('%Y%m%d')}.html")

    # Write index.html in every subfolder (one by section)
    for asset in data["assets"]:
        section = asset["section"]
        data = get_assets_by_section(section)
        html_section = generate_section_html(data)
        write_to_bucket(html_section, bucket, f"{section}/index.html")
        print(f"{section}/index.html")

    return {"statusCode": 200, "body": "File uploaded successfully."}
