variable "region" {
  description = "Region of AWS VPC"
  type        = string
}

variable "openai_token" {
  description = "OpenAI token"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Name of the domain (ex: example.com)"
  type        = string
}
