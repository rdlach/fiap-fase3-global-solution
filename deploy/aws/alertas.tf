# Alertas de custo só do FloodGuard. O e-mail fica em alertas.auto.tfvars e o Git ignora esse arquivo.
variable "email_alerta" {
  type    = string
  default = null
}

variable "orcamento_mensal_usd" {
  type    = number
  default = 3
}

locals {
  alertas_ativos = var.email_alerta != null
}

resource "aws_budgets_budget" "floodguard" {
  count        = local.alertas_ativos ? 1 : 0
  name         = "floodguard-mensal"
  budget_type  = "COST"
  limit_amount = tostring(var.orcamento_mensal_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "Service"
    values = ["Amazon CloudFront", "AWS Lambda", "Amazon API Gateway", "AWS WAF"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.email_alerta]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.email_alerta]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.email_alerta]
  }
}

resource "aws_ce_anomaly_monitor" "servicos" {
  count             = local.alertas_ativos ? 1 : 0
  name              = "floodguard-servicos"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "aviso" {
  count            = local.alertas_ativos ? 1 : 0
  name             = "floodguard-anomalias"
  frequency        = "DAILY"
  monitor_arn_list = [aws_ce_anomaly_monitor.servicos[0].arn]

  subscriber {
    type    = "EMAIL"
    address = var.email_alerta
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = ["2"]
    }
  }
}
