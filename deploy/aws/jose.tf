variable "jose_ativo" {
  type    = bool
  default = false
}

resource "random_password" "origem" {
  length  = 48
  special = false
}

resource "random_password" "equipe" {
  length  = 24
  special = false
}

resource "aws_s3_bucket" "estado" {
  bucket_prefix = "floodguard-estado-"
}

# o estado é regravado a cada alteração e as versões antigas só ocupam espaço
resource "aws_s3_bucket_lifecycle_configuration" "estado" {
  bucket = aws_s3_bucket.estado.id
  rule {
    id     = "descartar-versoes-antigas"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 1
    }
    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
  depends_on = [aws_s3_bucket_versioning.estado]
}

resource "aws_s3_bucket_public_access_block" "estado" {
  bucket                  = aws_s3_bucket.estado.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "estado" {
  bucket = aws_s3_bucket.estado.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "jose" {
  name_prefix = "floodguard-pyhtml-"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "jose" {
  name              = "/aws/lambda/${aws_s3_bucket.front.id}-pyhtml"
  retention_in_days = 7
}

resource "aws_iam_role_policy" "jose" {
  role = aws_iam_role.jose.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject", "s3:PutObject"], Resource = "${aws_s3_bucket.estado.arn}/simulacao.json" },
      { Effect = "Allow", Action = "s3:ListBucket", Resource = aws_s3_bucket.estado.arn },
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "${aws_cloudwatch_log_group.jose.arn}:*" }
    ]
  })
}

resource "aws_lambda_function" "jose" {
  function_name    = "${aws_s3_bucket.front.id}-pyhtml"
  role             = aws_iam_role.jose.arn
  runtime          = "python3.13"
  handler          = "adapter.handler"
  filename         = "${path.module}/jose.zip"
  source_code_hash = filebase64sha256("${path.module}/jose.zip")
  timeout          = 5
  memory_size      = 128

  # no máximo 5 execuções ao mesmo tempo, assim um ataque não dispara o custo
  reserved_concurrent_executions = 5

  environment {
    variables = {
      STATE_BUCKET  = aws_s3_bucket.estado.id
      ORIGIN_KEY    = random_password.origem.result
      CODIGO_EQUIPE = random_password.equipe.result
    }
  }

  depends_on = [aws_iam_role_policy.jose]
}

resource "aws_apigatewayv2_api" "jose" {
  name          = "floodguard-pyhtml"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "jose" {
  api_id                 = aws_apigatewayv2_api.jose.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.jose.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "jose" {
  api_id    = aws_apigatewayv2_api.jose.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.jose.id}"
}

resource "aws_apigatewayv2_stage" "jose" {
  api_id      = aws_apigatewayv2_api.jose.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }
}

resource "aws_lambda_permission" "jose" {
  statement_id  = "AllowFloodGuardApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.jose.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.jose.execution_arn}/*/*"
}

output "codigo_equipe" {
  value     = random_password.equipe.result
  sensitive = true
}
