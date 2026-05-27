# ── Application Load Balancer ─────────────────────────────────────────
#
# The ALB is the ONLY public-facing resource once EC2 moves to the
# private subnet. Terminates TLS via ACM certificate, forwards to
# the EC2 target group.
#
# Key config per the locked spec:
#   - idle_timeout = 300s (SSE /api/generate/stream/ survival)
#   - Access logs → S3
#   - HTTP → HTTPS redirect (listener rule)

# ── S3 bucket for ALB access logs ────────────────────────────

resource "aws_s3_bucket" "alb_logs" {
  bucket = "${var.project_name}-alb-logs-159903201072"

  tags = {
    Project = var.project_name
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }
  }
}

# ALB requires a specific bucket policy for log delivery
data "aws_elb_service_account" "main" {}

resource "aws_s3_bucket_policy" "alb_logs" {
  bucket = aws_s3_bucket.alb_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "ALBLogDelivery"
        Effect    = "Allow"
        Principal = { AWS = data.aws_elb_service_account.main.arn }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.alb_logs.arn}/*"
      }
    ]
  })
}

# ── ACM Certificate ──────────────────────────────────────────
# Use the existing Let's Encrypt cert on the EC2 for now.
# For ALB, we need an ACM certificate. Import or create one.
# Using DNS validation via Route 53.

resource "aws_acm_certificate" "main" {
  domain_name       = "archimedes-arc.app"
  validation_method = "DNS"

  tags = {
    Project = var.project_name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── Security Group ───────────────────────────────────────────

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "ALB — public HTTPS only"
  vpc_id      = aws_vpc.main.id

  # HTTPS from internet
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP (for redirect to HTTPS)
  ingress {
    description = "HTTP redirect"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound to targets
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-alb-sg"
    Project = var.project_name
  }
}

# ── ALB ──────────────────────────────────────────────────────

resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  idle_timeout = 300 # SSE /api/generate/stream/ needs long-lived connections

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    enabled = true
  }

  tags = {
    Project = var.project_name
  }
}

# ── Target Group ─────────────────────────────────────────────
# Points at the EC2 instance. Health check on /health (not /api/generate/stream/).

resource "aws_lb_target_group" "backend" {
  name     = "${var.project_name}-backend-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id # EC2 is still in default VPC

  health_check {
    enabled             = true
    path                = "/health"
    port                = "8080" # nginx listens on 8080 inside the container
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    matcher             = "200,301"
  }

  tags = {
    Project = var.project_name
  }
}

resource "aws_lb_target_group_attachment" "backend" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.archimedes.id
  port             = 80
}

# ── Listeners ────────────────────────────────────────────────

# HTTPS listener (main)
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# HTTP → HTTPS redirect
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
