import datetime

import boto3
from boto3.dynamodb.conditions import Key

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>AutoContentHub {subpage}</title>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --card-bg: rgba(255, 255, 255, 0.08);
      --text-main: #ffffff;
      --text-muted: #bbbbbb;
      --radius: 18px;
    }}

    body.home {{
      --bg-gradient: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      --primary: #61dafb;
    }}

    body.section {{
      --bg-gradient: linear-gradient(
        180deg,
        #0d2329 0%,
        #122f35 30%,
        #173b42 60%,
        #1c474f 100%
      );
      --primary: #fbc02d;
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    body {{
      font-family: 'Outfit', sans-serif;
      background: var(--bg-gradient);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding: 40px 20px;
    }}

    h1 {{
      text-align: center;
      font-size: 3rem;
      font-weight: 800;
      margin-bottom: 40px;
      color: var(--primary);
      letter-spacing: -1px;
    }}

    .article {{
      display: grid;
      gap: 30px;
      max-width: 1200px;
      margin: 0 auto;
    }}

    .single-column {{
      grid-template-columns: 1fr !important;
    }}

    .card {{
      background: var(--card-bg);
      border-radius: var(--radius);
      backdrop-filter: blur(12px);
      padding: 25px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}

    .card:hover {{
      transform: translateY(-5px);
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.4);
    }}

    .theme {{
      display: inline-block;
      font-size: 0.85em;
      background-color: rgba(255, 255, 255, 0.15);
      color: var(--primary);
      padding: 5px 10px;
      border-radius: 6px;
      text-transform: uppercase;
      font-weight: 600;
      margin-bottom: 10px;
      letter-spacing: 0.5px;
    }}

    .title {{
      font-size: 1.4rem;
      font-weight: 700;
      margin: 10px 0;
      text-decoration: none;
      color: var(--text-main);
      display: block;
    }}

    .title:hover {{
      color: var(--primary);
    }}

    .description {{
      font-size: 1rem;
      color: var(--text-muted);
      line-height: 1.6;
    }}

    footer {{
      text-align: center;
      margin-top: 60px;
      font-size: 0.9rem;
      color: #888;
    }}

    .site-title {{
      text-decoration: none;
      color: var(--primary);
      transition: color 0.3s ease;
    }}

    .site-title:hover {{
      color: #ffffff;
    }}

    .site-title:visited {{
      color: var(--primary);
    }}

    .title-sub {{
      font-weight: 400;
      color: var(--text-muted);
      margin-left: 10px;
      font-size: 1.4rem;
    }}

    @media (min-width: 600px) {{
      .article:not(.single-column) {{
        grid-template-columns: repeat(2, 1fr);
      }}
    }}

    @media (min-width: 900px) {{
      .article:not(.single-column) {{
        grid-template-columns: repeat(3, 1fr);
      }}
    }}
  </style>
</head>
<body class="{page_type}">

  <h1>
    <a class="site-title" href="/">AutoContentHub</a>
    <span class="title-sub">{subpage}</span>
  </h1>  
  <div class="article {page_class}">
    {assets}
  </div>
  
  <footer>© 2025 AutoContentHub — Curated Tech, Reimagined</footer>
</body>
</html>
"""

asset_template = """
  <div class="card">
    <a href="/{section}"><span class="theme">#{section}</span></a>
    <a href="/{link}"><span class="title">{title}</span></a>
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


def get_assets_by_section(section: str) -> dict:
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

    return html_template.format(
        subpage=f"[{data['date'].strftime('%Y-%m-%d')}]",
        assets=assets_str,
        page_class="",  # enables responsive columns
        page_type="home",  # blue-themed homepage
    )


def generate_section_html(data: dict) -> str:
    assets_str = ""
    for asset in data["assets"]:
        section = asset["section"]
        date = asset["date"]

        if section == "game":
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

    return html_template.format(
        subpage=f"[#{data['section']}]",
        assets=assets_str,
        page_class="single-column",  # force one-column layout
        page_type="section",  # green-themed section page
    )


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

    write_to_bucket(html, bucket, "index.html")
    write_to_bucket(html, bucket, f"{date.strftime('%Y%m%d')}.html")

    for asset in data["assets"]:
        section = asset["section"]
        section_data = get_assets_by_section(section)
        html_section = generate_section_html(section_data)
        write_to_bucket(html_section, bucket, f"{section}/index.html")
        print(f"{section}/index.html")

    return {"statusCode": 200, "body": "File uploaded successfully."}
