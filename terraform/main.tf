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
      version = ">= 4.40.0"
    }
    klayers = {
      version = "~> 1.0.1"
      source  = "ldcorentin/klayer"
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

data "klayers_package_latest_version" "pillow" {
  name   = "Pillow"
  region = "eu-west-1"
  python_version = "3.8"
}