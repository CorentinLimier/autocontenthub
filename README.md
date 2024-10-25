# [AutoContentHub.com](http://www.autocontenthub.com)

# Concept

This project creates lambda functions that runs periodically to ask ChatGPT to create new content and deploy it to a static website.

# Structure of the project 

```
autocontenthub/
├── frontend/
│   ├─ Lambda that creates the main static pages of the websites and deploy it to S3

├── generator/
│   ├─ Lambda that calls ChatGPT to generate new content

├── static/
│   ├─ Some static pages : default index.html, error.html and load.html to display ChatGPT generated content with the proper CSS theme

├── terraform/
│   ├─ Deploy infra to AWS 
```

# Infrastructure

This project uses (among other things): 
- AWS Lambda : to generate new content using ChatGPT
- EventBridge : to schedule lambdas
- DynamoDB : to store a description of generated content
- S3 : to store content generated
- Cloudfront / route 53 to serve the website

# Generate a new section of content

To generate a new type of content, adds an object in variable `contents` in `terraform/variables.tf` 

```
contents = {
    <new_section> = "<prompt>"
}
```

It will create a new EventBridge event that will trigger the lambda and send the prompt to ChatGPT to generate the content at the fixed schedule. 

New section will be available at route `/<new_section>` of the website. 

# Appendix

- [Create static webpage using terraform](https://dev.to/aws-builders/how-to-create-a-simple-static-amazon-s3-website-using-terraform-43hc)
- [Deploy a lambda](https://medium.com/@haissamhammoudfawaz/create-a-aws-lambda-function-using-terraform-and-python-4e0c2816753a)
- [Use secrets in Lambda](https://hackmd.io/@L6aUtVUHQ3ibkfiLD0maQw/BypjVHD8o)
- [OpenAI API reference](https://platform.openai.com/docs/api-reference)
- [Configuring a static website using a custom domain registered with Route 53](https://docs.aws.amazon.com/AmazonS3/latest/userguide/website-hosting-custom-domain-walkthrough.html#root-domain-walkthrough-create-buckets)
[Setup an S3-CloudFront Website with Terraform](https://blog.demir.io/setup-an-s3-cloudfront-website-with-terraform-268d5230f05)
[Use an Amazon CloudFront distribution to serve a static website](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/getting-started-cloudfront-overview.html#getting-started-cloudfront-distribution)
