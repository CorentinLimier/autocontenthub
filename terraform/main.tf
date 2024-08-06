provider "aws" {
  shared_credentials_files = ["~/.aws/credentials"]
  region                   = var.region
}

resource "aws_servicecatalogappregistry_application" "onegameperday_app" {
  name        = "onegameperday"
  description = "One game per day generated by LLM"
}

# Bucket 

resource "random_string" "random" {
  length  = 6
  special = false
  upper   = false
}

resource "aws_s3_bucket" "bucket" {
  bucket = "revbucket-${random_string.random.result}"
  tags   = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_s3_bucket_website_configuration" "blog" {
  bucket = aws_s3_bucket.bucket.id
  index_document {
    suffix = "index.html"
  }
  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket                  = aws_s3_bucket.bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_object" "upload_object" {
  for_each     = fileset("../static/", "*")
  bucket       = aws_s3_bucket.bucket.id
  key          = each.value
  source       = "../static/${each.value}"
  etag         = filemd5("../static/${each.value}")
  content_type = "text/html"
  tags         = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_s3_bucket_policy" "allow_access_from_everywhere" {
  bucket = aws_s3_bucket.bucket.id
  policy = data.aws_iam_policy_document.allow_access_from_everywhere.json
}

data "aws_iam_policy_document" "allow_access_from_everywhere" {
  statement {
    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
    ]

    resources = [
      "${aws_s3_bucket.bucket.arn}/*",
    ]
  }
}

# OpenAI secret 

resource "aws_secretsmanager_secret" "openai" {
  name                    = "openai"
  description             = "OpenAI token"
  recovery_window_in_days = 0
  tags                    = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_secretsmanager_secret_version" "openai_secret" {
  secret_id     = aws_secretsmanager_secret.openai.id
  secret_string = var.openai_token
}

# Lambda 

resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com",
      },
    }],
  })
  tags = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_iam_policy" "lambda_secret_policy" {
  name = "lambda_sm_policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.openai.arn
      },
  ] })
  tags = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_iam_policy" "lambda_bucket_policy" {
  name = "lambda_bucket_policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:*",
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.bucket.arn}/*"
      },
  ] })
  tags = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_iam_role_policy_attachment" "lambda_sm" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_secret_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_bucket" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_bucket_policy.arn
}

data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_file = "../generator/lambda_function.py"
  output_path = "generator.zip"
}

resource "aws_lambda_function" "generate_lambda_function" {
  function_name    = "generate_game"
  filename         = "generator.zip"
  source_code_hash = data.archive_file.python_lambda_package.output_base64sha256
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.10"
  handler          = "lambda_function.lambda_handler"
  timeout          = 60
  environment {
    variables = {
      bucket_name = aws_s3_bucket.bucket.id
    }
  }
}

# EventBridge

resource "aws_cloudwatch_event_rule" "every_day" {
  name                = "every_day_rule"
  description         = "trigger generate_game every day"
  schedule_expression = "cron(0 1 * * ? *)"
  tags                = aws_servicecatalogappregistry_application.onegameperday_app.application_tag
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.every_day.name
  target_id = "lambda-function-target"
  arn       = aws_lambda_function.generate_lambda_function.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.generate_lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_day.arn
}
