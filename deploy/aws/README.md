# Publicar o front do FloodGuard na AWS

O Terraform cria um bucket S3 privado, uma distribuição CloudFront com HTTPS e uma lista de IPs permitidos no AWS WAF. Este deploy hospeda os arquivos estáticos do front. A aplicação Python e a gravação no CSV continuam rodando localmente.

## Preparar

Instale Terraform e AWS CLI. Abra esta pasta no terminal e selecione o perfil AWS já configurado na sua máquina:

```sh
export AWS_PROFILE=meu-perfil
aws sts get-caller-identity
cp terraform.tfvars.example terraform.tfvars
```

Edite `terraform.tfvars` e substitua os exemplos pelos IPs públicos de quem pode acessar. Use `/32` para um IPv4 individual e `/128` para um IPv6 individual. Se a rede mudar de IP, atualize a lista e aplique novamente. O WAF bloqueia por padrão. S3, CloudFront e WAF podem gerar cobranças.

## Criar a infraestrutura e publicar

```sh
terraform init
terraform plan -out=deploy.tfplan
terraform apply deploy.tfplan
```

Aponte `FRONT_DIR` para a pasta que contém o `index.html` e os arquivos estáticos prontos do José:

```sh
FRONT_DIR="/caminho/para/o/front/dist"
./publicar.sh "$FRONT_DIR"
```

Teste o endereço exibido pelo script em uma rede permitida. Fora da lista, espere HTTP 403. Para publicar uma nova versão, rode o script novamente. Guarde o estado local do Terraform para futuras atualizações.

## Versão pyHTML do José

Para publicar a versão integrada na branch principal, atualize a referência
`origin/main` e empacote a aplicação antes de rodar o Terraform:

```sh
./empacotar-jose.sh
terraform init
terraform plan -var=jose_ativo=true -out=jose.tfplan
terraform apply jose.tfplan
```

O CloudFront envia as solicitações ao API Gateway e à Lambda. A Lambda usa as
telas, os formulários e as regras da pasta `pyhtml-beta`. O estado compartilhado
fica em um objeto no S3 privado e versionado. Ele contém o CSV de ocorrências e
o dia simulado. Os registros da demo anterior permanecem no armazenamento do
respectivo navegador. Os perfis comunidade e equipe continuam simulados, com
acesso público enquanto a lista de IPs estiver vazia. Use dados fictícios.

Para voltar à demo estática, planeje e aplique com `-var=jose_ativo=false`.

## Código da equipe

No site publicado a área da equipe pede um código. O Terraform gera o valor e a Lambda só sobe se ele existir. Para ler:

```sh
terraform output -raw codigo_equipe
```

A sessão da equipe dura 2 horas. Não coloque o código em arquivos do repositório.

## Custo e proteção

- O CloudFront deve ficar no plano Free, em Manage plan no console. Ele inclui o WAF, não cobra excedente e só reduz a velocidade do site se o tráfego passar muito da franquia. Para cancelar o plano ou destruir a distribuição, cancele o plano antes no console.
- O plano Free só aceita limite por IP no WAF. Regras com byte match ou filtro por cabeçalho exigem plano pago.
- A Lambda roda no máximo 5 execuções ao mesmo tempo e a API aceita 5 requisições por segundo.
- O CSS e a página de ajuda ficam 5 minutos em cache no CloudFront.
- O bucket de estado descarta versões antigas depois de um dia.

## Alertas de custo

Crie o arquivo `alertas.auto.tfvars`, que o Git ignora, com o seu e-mail:

```sh
email_alerta = "voce@exemplo.com"
```

Com ele o Terraform cria um orçamento mensal de 3 dólares só para CloudFront, Lambda, API Gateway e WAF, com aviso em 50% e 100% do gasto real e em 100% da previsão. Cria também a detecção de anomalia, que manda um resumo diário quando algum serviço gasta 2 dólares a mais que o normal. A AWS pode pedir a confirmação da inscrição por e-mail.

## Parar tudo em caso de emergência

Este comando zera a Lambda e o site dinâmico para na hora. Para religar, troque o 0 por 5.

```sh
aws lambda put-function-concurrency --region us-east-1 \
  --function-name NOME_DA_FUNCAO --reserved-concurrent-executions 0
```

O nome da função aparece com `terraform state show aws_lambda_function.jose`.
