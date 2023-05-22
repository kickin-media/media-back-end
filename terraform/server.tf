resource "aws_instance" "media_server" {
  ami                    = "ami-0a8dc52684ee2fee2"
  instance_type          = "t3.micro"
  iam_instance_profile   = "SessionManagerEC2Role"
  vpc_security_group_ids = [aws_security_group.media_server_sg.id]

  tags = {
    Name = "kickin-media-server"
  }
}

resource "aws_security_group" "media_server_sg" {
  name        = "media-server-sg"
  description = "Allow inbound traffic for media server."
  vpc_id      = aws_vpc.media_vpc.id

  ingress {
    description      = "Public HTTPS"
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Public HTTP"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Public SSH"
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Proxy Manager"
    from_port        = 8080
    to_port          = 8080
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "media-server-sg"
  }
}

resource "aws_eip" "media_server_external_ip" {
  instance = aws_instance.media_server.id
  vpc      = true

  tags = {
    Name = "media-api-ip"
  }
}