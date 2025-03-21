terraform {

  required_version = ">= 1.3.0"

  backend "s3" {
    bucket         = "media-990658861879-terraform-state"
    key            = "media.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "media-990658861879-terraform-locktable"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.73.0"
    }
  }

}

provider "aws" {
  region = "eu-west-1"
}

provider "aws" {
  region = "us-east-1"
  alias  = "aws-global"
}