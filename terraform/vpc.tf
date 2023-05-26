resource "aws_vpc" "media_vpc" {
  cidr_block = "172.31.0.0/16"
  tags       = {
    Name = "media-vpc"
  }
}

resource "aws_subnet" "media_subnet" {
  vpc_id            = aws_vpc.media_vpc.id
  availability_zone = "eu-west-1b"
  cidr_block        = "172.31.32.0/20"
  tags              = {
    Name = "media-subet"
  }
}

resource "aws_internet_gateway" "media_igw" {
  vpc_id = aws_vpc.media_vpc.id

  tags = {
    Name = "media-igw"
  }
}

resource "aws_route_table" "media_route_table" {
  vpc_id = aws_vpc.media_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.media_igw.id
  }

  tags = {
    Name = "media-route-table"
  }
}