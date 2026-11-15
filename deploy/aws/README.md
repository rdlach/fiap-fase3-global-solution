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
