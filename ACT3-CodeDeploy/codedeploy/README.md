# Laboratorio AWS CodeDeploy

Referencia rápida de arquitectura, archivos y comandos para desplegar y probar
este laboratorio. Para la guía paso a paso pensada para estudiantes, ver
[`laboratorio/README.md`](./laboratorio/README.md).

## Flujo completo

```
 ┌────────────────────────┐
 │   CloudFormation        │
 │   01-infrastructure.yaml│
 │  (VPC, EC2, nginx)      │
 └───────────┬──────────────┘
             │
             ▼
 ┌────────────────────────┐
 │   EC2 - Version 1        │
 │  "Implementado desde     │
 │   CloudFormation"        │
 └───────────┬──────────────┘
             │
             ▼
 ┌────────────────────────┐
 │   CloudFormation         │
 │   02-codedeploy.yaml     │
 │ (App + Deployment Group) │
 └───────────┬──────────────┘
             │
             ▼
 ┌────────────────────────┐
 │  Revision (appspec.yml   │
 │  + scripts + config) →   │
 │  S3 → CodeDeploy deploy   │
 └───────────┬──────────────┘
             │
             ▼
 ┌────────────────────────┐
 │   EC2 - Version 2         │
 │  "Implementado con        │
 │   AWS CodeDeploy"         │
 └────────────────────────┘
```

## Estructura de archivos

| Archivo | Descripción |
|---|---|
| `cloudformation/01-infrastructure.yaml` | Crea VPC, subnet pública, Internet Gateway, Security Group, IAM Role/Instance Profile y la instancia EC2 con nginx sirviendo la Version 1. |
| `cloudformation/02-codedeploy.yaml` | Crea el IAM Role de CodeDeploy, la Application y el Deployment Group apuntando a la instancia EC2 por tag `Name`. |
| `app/appspec.yml` | Instrucciones de despliegue: qué archivos copiar y qué scripts ejecutar en cada fase del lifecycle. |
| `app/scripts/stop_server.sh` | Hook `BeforeInstall`: detiene la app anterior y recarga nginx de forma segura. |
| `app/scripts/start_server.sh` | Hook `AfterInstall`: publica la Version 2 y recarga nginx. |
| `app/scripts/validate.sh` | Hook `ApplicationStart`: valida que `http://localhost` responda HTTP 200. |
| `app/config/nginx.conf` | Configuración de nginx para servir la aplicación en el puerto 80. |
| `laboratorio/README.md` | Guía completa paso a paso para estudiantes. |

## Comandos CLI

### 1. Desplegar Stack 1 (infraestructura)

```bash
aws cloudformation deploy \
  --template-file cloudformation/01-infrastructure.yaml \
  --stack-name codedeploy-demo-infra \
  --parameter-overrides ProjectName=codedeploy-demo KeyName=MI_KEY_PAIR \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Obtener outputs (IP pública, URL, InstanceId):

```bash
aws cloudformation describe-stacks \
  --stack-name codedeploy-demo-infra \
  --query "Stacks[0].Outputs" \
  --region us-east-1
```

### 2. Desplegar Stack 2 (CodeDeploy)

```bash
EC2_INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name codedeploy-demo-infra \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" \
  --output text \
  --region us-east-1)

aws cloudformation deploy \
  --template-file cloudformation/02-codedeploy.yaml \
  --stack-name codedeploy-demo-codedeploy \
  --parameter-overrides ProjectName=codedeploy-demo EC2InstanceId=$EC2_INSTANCE_ID \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### 3. Empaquetar la revisión

```bash
cd app
zip -r ../revision-v2.zip appspec.yml scripts config
cd ..
```

### 4. Crear el bucket S3 y subir la revisión

```bash
aws s3 mb s3://codedeploy-demo-revisions-<TU_CUENTA> --region us-east-1

aws s3 cp revision-v2.zip \
  s3://codedeploy-demo-revisions-<TU_CUENTA>/revision-v2.zip \
  --region us-east-1
```

### 5. Ejecutar el deploy

```bash
aws deploy create-deployment \
  --application-name codedeploy-demo-app \
  --deployment-group-name codedeploy-demo-dg \
  --s3-location bucket=codedeploy-demo-revisions-<TU_CUENTA>,key=revision-v2.zip,bundleType=zip \
  --region us-east-1
```

Monitorear:

```bash
aws deploy get-deployment --deployment-id <DEPLOYMENT_ID> --region us-east-1
```

## Limpieza

```bash
# Vaciar y eliminar el bucket S3
aws s3 rm s3://codedeploy-demo-revisions-<TU_CUENTA> --recursive --region us-east-1
aws s3 rb s3://codedeploy-demo-revisions-<TU_CUENTA> --region us-east-1

# Eliminar los stacks (orden inverso a la creación)
aws cloudformation delete-stack --stack-name codedeploy-demo-codedeploy --region us-east-1
aws cloudformation delete-stack --stack-name codedeploy-demo-infra --region us-east-1
```
