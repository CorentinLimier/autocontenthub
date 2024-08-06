# required for AWS
variable "region" {
  description = "Region of AWS VPC"
}

variable "openai_token" {
  description = "OpenAI token"
  type        = string
  sensitive   = true
}
