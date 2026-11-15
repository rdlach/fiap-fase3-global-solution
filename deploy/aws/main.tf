terraform {
  required_version = ">= 1.5"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

provider "aws" {
  alias   = "edge"
  region  = "us-east-1"
  profile = var.aws_profile
}

variable "aws_profile" {
  type    = string
  default = null
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "allowed_cidrs" {
  type    = set(string)
  default = []
  validation {
    condition = alltrue([
      for cidr in var.allowed_cidrs : can(cidrhost(cidr, 0)) && !endswith(cidr, "/0")
    ])
    error_message = "Informe CIDRs válidos, sem redes /0."
  }
}

locals {
  ip_sets = {
    for version in ["IPV4", "IPV6"] : version => [
      for cidr in sort(tolist(var.allowed_cidrs)) : cidr
      if strcontains(cidr, ":") == (version == "IPV6")
    ]
    if anytrue([for cidr in var.allowed_cidrs : strcontains(cidr, ":") == (version == "IPV6")])
  }
}

resource "aws_s3_bucket" "front" {
  bucket_prefix = "floodguard-front-"
}

resource "aws_s3_bucket_public_access_block" "front" {
  bucket                  = aws_s3_bucket.front.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "front" {
  name                              = aws_s3_bucket.front.id
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_wafv2_ip_set" "allowed" {
  provider           = aws.edge
  for_each           = local.ip_sets
  name               = "${aws_s3_bucket.front.id}-${lower(each.key)}"
  scope              = "CLOUDFRONT"
  ip_address_version = each.key
  addresses          = each.value
}

# O WAF barra IPs que mandam requisições demais antes de chegarem na Lambda.
# O plano Free do CloudFront só aceita limite por IP, regras como byte match pedem plano pago.
# Sem IPs na lista o site fica público, com IPs só eles entram.
variable "limite_requisicoes_5min" {
  type        = number
  default     = 300
  description = "Máximo de requisições por IP em 5 minutos."
}

resource "aws_wafv2_web_acl" "front" {
  provider = aws.edge
  name     = aws_s3_bucket.front.id
  scope    = "CLOUDFRONT"

  default_action {
    dynamic "allow" {
      for_each = length(var.allowed_cidrs) > 0 ? [] : [1]
      content {}
    }
    dynamic "block" {
      for_each = length(var.allowed_cidrs) > 0 ? [1] : []
      content {}
    }
  }

  rule {
    name     = "LimiteGeral"
    priority = 10
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit                 = var.limite_requisicoes_5min
        aggregate_key_type    = "IP"
        evaluation_window_sec = 300
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "LimiteGeral"
      sampled_requests_enabled   = false
    }
  }

  dynamic "rule" {
    for_each = aws_wafv2_ip_set.allowed
    content {
      name     = "Allow-${rule.key}"
      priority = rule.key == "IPV4" ? 0 : 1
      action {
        allow {}
      }
      statement {
        ip_set_reference_statement {
          arn = rule.value.arn
        }
      }
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "Allow-${rule.key}"
        sampled_requests_enabled   = false
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "FloodGuard"
    sampled_requests_enabled   = false
  }
}

variable "dominio_certificado_arn" {
  type    = string
  default = null
}

resource "aws_cloudfront_distribution" "front" {
  aliases             = var.dominio_certificado_arn == null ? [] : ["floodguard.com.br"]
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = var.jose_ativo ? null : "index.html"
  web_acl_id          = aws_wafv2_web_acl.front.arn

  origin {
    domain_name              = aws_s3_bucket.front.bucket_regional_domain_name
    origin_id                = "front"
    origin_access_control_id = aws_cloudfront_origin_access_control.front.id
  }

  origin {
    domain_name = trimprefix(aws_apigatewayv2_api.jose.api_endpoint, "https://")
    origin_id   = "pyhtml"
    custom_header {
      name  = "X-FloodGuard-Origin"
      value = random_password.origem.result
    }
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # páginas fixas ficam 5 minutos no CloudFront e não chamam a Lambda
  dynamic "ordered_cache_behavior" {
    for_each = var.jose_ativo ? ["/style.css", "/ajuda"] : []
    content {
      path_pattern           = ordered_cache_behavior.value
      target_origin_id       = "pyhtml"
      viewer_protocol_policy = "redirect-to-https"
      allowed_methods        = ["GET", "HEAD"]
      cached_methods         = ["GET", "HEAD"]
      cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"
    }
  }

  default_cache_behavior {
    target_origin_id         = var.jose_ativo ? "pyhtml" : "front"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = var.jose_ativo ? ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"] : ["GET", "HEAD"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = var.jose_ativo ? "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" : "658327ea-f89d-4fab-a63d-7e88639e58f6"
    origin_request_policy_id = var.jose_ativo ? "b689b0a8-53d0-40ab-baf2-68738e2966ac" : null
  }

  depends_on = [aws_lambda_permission.jose, aws_apigatewayv2_stage.jose]

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.dominio_certificado_arn == null
    acm_certificate_arn            = var.dominio_certificado_arn
    ssl_support_method             = var.dominio_certificado_arn == null ? null : "sni-only"
    minimum_protocol_version       = var.dominio_certificado_arn == null ? null : "TLSv1.2_2021"
  }
}

resource "aws_s3_bucket_policy" "front" {
  bucket     = aws_s3_bucket.front.id
  depends_on = [aws_s3_bucket_public_access_block.front]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.front.arn}/*"
      Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.front.arn } }
    }]
  })
}

output "bucket" {
  value = aws_s3_bucket.front.id
}

output "site_url" {
  value = "https://${aws_cloudfront_distribution.front.domain_name}"
}

output "distribution_id" {
  value = aws_cloudfront_distribution.front.id
}
