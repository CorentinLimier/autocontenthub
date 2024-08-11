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
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            width: 90%;
            max-width: 1000px;
            margin: 50px auto;
            background: linear-gradient(135deg, #ffffff, #f0f0f0);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease-in-out;
        }}

        .container:hover {{
            transform: scale(1.01);
        }}

        h1 {{
            text-align: center;
            color: #333;
            font-size: 3em;
            font-weight: 700;
            margin-bottom: 50px;
        }}

        h1 a {{
            text-decoration: none;
            color: #007BFF;
            transition: color 0.3s ease, text-shadow 0.3s ease;
        }}

        h1 a:hover {{
            color: #0056b3;
            text-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }}

        .article {{
            border-bottom: 2px solid rgba(0, 0, 0, 0.1);
            padding: 25px 0;
            transition: background-color 0.3s ease;
        }}

        .article:last-child {{
            border-bottom: none;
        }}

        .article:hover {{
            background-color: #f9f9f9;
            border-radius: 8px;
        }}

        .theme {{
            font-size: 1.2em;
            font-weight: 500;
            color: #007BFF;
            background-color: rgba(0, 123, 255, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            margin-right: 15px;
            text-decoration: none;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}

        .theme:hover {{
            background-color: #007BFF;
            color: #ffffff;
        }}

        .title {{
            font-size: 1.6em;
            font-weight: 700;
            color: #333;
            text-decoration: none;
            transition: color 0.3s ease;
            margin-left: 10px;
        }}

        .title:hover {{
            color: #007BFF;
            text-decoration: underline;
        }}

        .description {{
            font-size: 1.1em;
            margin: 15px 0 0 0;
            color: #666;
            line-height: 1.8;
        }}

        footer {{
            text-align: center;
            margin-top: 60px;
            font-size: 1em;
            color: #888;
        }}

        @media (max-width: 600px) {{
            h1 {{
                font-size: 2.2em;
            }}
            .container {{
                padding: 25px;
            }}
            .article {{
                padding: 20px 0;
            }}
            .theme, .title {{
                font-size: 1.4em;
            }}
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
                <a href="/{link}"><span class="title">{title}</span></a>
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
        section = asset["section"]
        date = data["date"].strftime("%Y%m%d")

        if section == "game":
            # ugly but load.html doesn't work for complex pages with javascript such as game section
            link = f"{section}/{date}.html"
        else:
            link = f"load.html?section={section}&date={date}"

        assets_str += asset_template.format(
            section=section,
            date=date,
            title=asset["title"],
            description=asset["description"],
            link=link,
        )

    result = html_template.format(
        subpage=f'[{data["date"].strftime("%Y-%m-%d")}]',
        assets=assets_str,
    )
    return result


def generate_section_html(data: dict) -> str:
    assets_str = ""
    for asset in data["assets"]:
        section = asset["section"]
        date = asset["date"]

        if section == "game":
            # ugly but load.html doesn't work for complex pages with javascript such as game section
            link = f"{section}/{date}.html"
        else:
            link = f"load.html?section={section}&date={date}"

        assets_str += asset_template.format(
            section=section,
            date=date,
            title=asset["title"],
            description=asset["description"],
            link=link,
        )

    result = html_template.format(subpage=f"[#{asset['section']}]", assets=assets_str)
    return result


def write_to_bucket(content: str, bucket: str, filename: str) -> None:
    s3 = boto3.client("s3")
    s3.put_object(Body=content, Bucket=bucket, Key=filename, ContentType="text/html")


def lambda_handler(event, context):
    bucket = event["bucket"]
    if "date" in event:
        date = datetime.datetime.strptime(event["date"], "%Y%m%d")
    else:
        date = datetime.datetime.today()

    data = get_assets_by_date(date)
    html = generate_main_html(data)

    write_to_bucket(html, bucket, f"index.html")
    write_to_bucket(html, bucket, f"{date.strftime('%Y%m%d')}.html")

    # Write index.html in every subfolder (one by section)
    for asset in data["assets"]:
        section = asset["section"]
        data = get_assets_by_section(section)
        html_section = generate_section_html(data)
        write_to_bucket(html_section, bucket, f"{section}/index.html")
        print(f"{section}/index.html")

    return {"statusCode": 200, "body": "File uploaded successfully."}
