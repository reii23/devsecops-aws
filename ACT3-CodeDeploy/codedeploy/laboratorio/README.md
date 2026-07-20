# Laboratorio: Despliegue continuo con AWS CodeDeploy

Guía completa paso a paso para desplegar una aplicación web en EC2 usando
AWS CodeDeploy, dentro del curso de Ciberseguridad y DevOps.

---

## 1. Introducción

**AWS CodeDeploy** es un servicio administrado que automatiza los despliegues
de aplicaciones hacia instancias EC2, servidores on-premise, funciones Lambda
o servicios de ECS. En lugar de conectarte por SSH a cada servidor y copiar
archivos manualmente, CodeDeploy se encarga de:

- Copiar la nueva versión de tu aplicación (la "revisión") hacia los
  servidores de destino.
- Ejecutar scripts en momentos específicos del despliegue (detener el
  servicio, instalar dependencias, iniciar el servicio, validar que todo
  funcione).
- Revertir automáticamente (rollback) si algo falla.

Esto es la base de cualquier pipeline de **entrega continua (CD)**: una vez
que el código pasa las pruebas, CodeDeploy lo lleva a producción de forma
consistente y repetible.

---

## 2. Objetivos

Al finalizar este laboratorio, el alumno será capaz de:

- Provisionar infraestructura en AWS usando CloudFormation (IaC).
- Entender el rol de una `appspec.yml` y los "lifecycle hooks" de CodeDeploy.
- Crear una aplicación y un Deployment Group en CodeDeploy.
- Empaquetar y subir una revisión a S3.
- Ejecutar un despliegue con la CLI de AWS y monitorear su progreso.
- Verificar el resultado del despliegue y entender el concepto de rollback.
- Limpiar todos los recursos creados para evitar costos innecesarios.

---

## 3. Arquitectura

```
 ┌───────────────────────────┐
 │  CloudFormation             │
 │  01-infrastructure.yaml     │
 │  → VPC, Subnet, SG, IAM,    │
 │    EC2 con nginx            │
 └─────────────┬────────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │  EC2 - Version 1             │
 │  "Implementado desde         │
 │   CloudFormation"             │
 └─────────────┬────────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │  CloudFormation              │
 │  02-codedeploy.yaml          │
 │  → CodeDeploy App +          │
 │    Deployment Group          │
 └─────────────┬────────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │  Revisión                   │
 │  (appspec.yml + scripts +   │
 │   config) empaquetada en    │
 │   .zip y subida a S3         │
 └─────────────┬────────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │  aws deploy create-deployment │
 │  → CodeDeploy ejecuta          │
 │    lifecycle hooks             │
 └─────────────┬────────────────┘
               │
               ▼
 ┌───────────────────────────┐
 │  EC2 - Version 2               │
 │  "Implementado con              │
 │   AWS CodeDeploy"               │
 └───────────────────────────┘
```

---

## 4. Requisitos previos

- Una cuenta de AWS con permisos para crear recursos de VPC, EC2, IAM,
  CodeDeploy y S3.
- **AWS CLI v2** instalado y configurado (`aws configure`) con credenciales
  válidas.
- Un **Key Pair** de EC2 ya creado en la región `us-east-1`. Si no tienes uno:

  ```bash
  aws ec2 create-key-pair \
    --key-name mi-llave-lab \
    --query "KeyMaterial" \
    --output text \
    --region us-east-1 > mi-llave-lab.pem

  chmod 400 mi-llave-lab.pem
  ```

- Conocimientos básicos de terminal/bash (no se requiere experiencia previa
  con AWS).

---

## 5. Parte 1: Provisionar infraestructura

Vamos a desplegar la VPC, la instancia EC2 y todo lo necesario para que la
Version 1 de la aplicación quede disponible.

```bash
aws cloudformation deploy \
  --template-file cloudformation/01-infrastructure.yaml \
  --stack-name codedeploy-demo-infra \
  --parameter-overrides ProjectName=codedeploy-demo KeyName=mi-llave-lab \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

El comando puede tardar 1-3 minutos. Cuando termine, obtén la URL pública:

```bash
aws cloudformation describe-stacks \
  --stack-name codedeploy-demo-infra \
  --query "Stacks[0].Outputs" \
  --region us-east-1
```

Copia el valor de `WebURL` y ábrelo en tu navegador. Debes ver una página con
el título **Bienvenido** y el subtítulo **Version 1** en color naranja.

> Si la página no carga de inmediato, espera 1-2 minutos: la instancia EC2
> necesita tiempo para terminar de ejecutar el `UserData` (instalar nginx,
> el agente de CodeDeploy, etc.).

---

## 6. Parte 2: Configurar CodeDeploy

Ahora creamos la Application y el Deployment Group que apuntan a la
instancia EC2 recién creada (identificada por el tag `Name`).

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

Verifica desde la consola de AWS:

1. Ve a **CodeDeploy → Applications**. Deberías ver `codedeploy-demo-app`.
2. Entra a la aplicación y luego a **Deployment groups**. Deberías ver
   `codedeploy-demo-dg` con el filtro de EC2 por tag configurado.

---

## 7. Parte 3: Preparar la revisión

Una **revisión** es el paquete de archivos que CodeDeploy va a copiar hacia
la instancia. Siempre debe incluir un archivo `appspec.yml` en la raíz, que
le dice a CodeDeploy:

- Qué archivos copiar y hacia dónde (sección `files`).
- Qué scripts ejecutar en cada fase del despliegue (sección `hooks`).

En este laboratorio, la revisión está en la carpeta `app/` y contiene:

```
app/
├── appspec.yml
├── scripts/
│   ├── stop_server.sh
│   ├── start_server.sh
│   └── validate.sh
└── config/
    └── nginx.conf
```

### Crear el bucket S3

```bash
aws s3 mb s3://codedeploy-demo-revisions-<TU_CUENTA> --region us-east-1
```

> Reemplaza `<TU_CUENTA>` por tu Account ID de AWS (o cualquier sufijo único),
> ya que los nombres de bucket S3 deben ser globalmente únicos.

### Empaquetar la revisión en un `.zip`

```bash
cd app
zip -r ../revision-v2.zip appspec.yml scripts config
cd ..
```

### Subir la revisión a S3

```bash
aws s3 cp revision-v2.zip \
  s3://codedeploy-demo-revisions-<TU_CUENTA>/revision-v2.zip \
  --region us-east-1
```

---

## 8. Parte 4: Ejecutar el despliegue

Con la revisión ya en S3, creamos el despliegue:

```bash
aws deploy create-deployment \
  --application-name codedeploy-demo-app \
  --deployment-group-name codedeploy-demo-dg \
  --s3-location bucket=codedeploy-demo-revisions-<TU_CUENTA>,key=revision-v2.zip,bundleType=zip \
  --region us-east-1
```

El comando devuelve un `deploymentId`. Guárdalo y monitorea el progreso:

```bash
aws deploy get-deployment \
  --deployment-id <DEPLOYMENT_ID> \
  --region us-east-1
```

También puedes monitorear desde la consola: **CodeDeploy → Applications →
codedeploy-demo-app → Deployments**.

### Fases del lifecycle que vas a ver

1. **ApplicationStop** (implícita, no configurada aquí).
2. **DownloadBundle**: CodeDeploy descarga la revisión desde S3.
3. **BeforeInstall**: ejecuta `stop_server.sh` (detiene la app anterior).
4. **Install**: copia los archivos definidos en `appspec.yml`.
5. **AfterInstall**: ejecuta `start_server.sh` (publica la Version 2).
6. **ApplicationStart**: ejecuta `validate.sh` (verifica HTTP 200).
7. **ValidateService**: fase final de validación de CodeDeploy.

---

## 9. Parte 5: Verificar el resultado

Abre nuevamente la `WebURL` obtenida en la Parte 1. Ahora deberías ver:

- Título: **Bienvenido**
- Subtítulo: **Version 2** en color verde
- Texto: **Implementado con AWS CodeDeploy**
- La fecha y hora del despliegue

En la consola de CodeDeploy, entra al despliegue y revisa la pestaña de
**eventos del lifecycle** (Lifecycle events). Cada hook (`BeforeInstall`,
`AfterInstall`, `ApplicationStart`) debe aparecer en estado `Succeeded`.

---

## 10. Parte 6: Despliegue de Version 3 (opcional)

Para practicar un segundo despliegue:

1. Edita `app/scripts/start_server.sh` y cambia `VERSION="2"` por
   `VERSION="3"`. Si quieres, cambia también el texto o el color.
2. Vuelve a empaquetar y subir la revisión (usa un nombre distinto, por
   ejemplo `revision-v3.zip`).
3. Ejecuta `aws deploy create-deployment` apuntando al nuevo objeto S3.
4. Verifica en el navegador que ahora se muestra la Version 3.

Este ejercicio ayuda a interiorizar que un despliegue con CodeDeploy es un
proceso repetible: cambias el código, empaquetas, subes y despliegas.

---

## 11. Parte 7: Limpieza

Es importante eliminar todos los recursos al finalizar para evitar cargos.

```bash
# 1. Vaciar el bucket S3 (no se puede eliminar un bucket con objetos dentro)
aws s3 rm s3://codedeploy-demo-revisions-<TU_CUENTA> --recursive --region us-east-1

# 2. Eliminar el bucket
aws s3 rb s3://codedeploy-demo-revisions-<TU_CUENTA> --region us-east-1

# 3. Eliminar el stack de CodeDeploy (primero, porque depende de la EC2)
aws cloudformation delete-stack \
  --stack-name codedeploy-demo-codedeploy \
  --region us-east-1

# 4. Esperar a que se elimine por completo antes de continuar
aws cloudformation wait stack-delete-complete \
  --stack-name codedeploy-demo-codedeploy \
  --region us-east-1

# 5. Eliminar el stack de infraestructura
aws cloudformation delete-stack \
  --stack-name codedeploy-demo-infra \
  --region us-east-1
```

---

## 12. Conceptos clave

| Concepto | Descripción |
|---|---|
| **Revision** | El conjunto de archivos (código, scripts, `appspec.yml`) que se despliega en cada ejecución. Se identifica por su ubicación en S3 (o GitHub). |
| **appspec.yml** | Archivo de especificación que le indica a CodeDeploy qué archivos copiar y qué scripts ejecutar en cada fase del despliegue. |
| **Deployment Group** | Conjunto de instancias (identificadas por tags, Auto Scaling Group, etc.) sobre las cuales se aplica un despliegue. |
| **Lifecycle Hooks** | Puntos del proceso de despliegue (`BeforeInstall`, `AfterInstall`, `ApplicationStart`, etc.) donde se pueden ejecutar scripts personalizados. |
| **Rollback** | Reversión automática a la última revisión estable cuando un despliegue falla (configurado con `AutoRollbackConfiguration`). |

---

## 13. Conclusión

En este laboratorio provisionaste infraestructura como código con
CloudFormation, configuraste AWS CodeDeploy y ejecutaste un despliegue real
que reemplazó el contenido de un servidor web sin necesidad de conectarte
manualmente por SSH. También viste cómo los lifecycle hooks permiten
controlar cada fase del proceso y cómo el rollback automático protege contra
despliegues fallidos.

Este es exactamente el tipo de paso que se automatiza en un **pipeline de
CI/CD completo**: en lugar de ejecutar `aws deploy create-deployment`
manualmente, ese comando se dispara automáticamente desde una herramienta
como AWS CodePipeline, Jenkins o GitHub Actions cada vez que el código pasa
las pruebas de integración continua (CI). Entender CodeDeploy de forma
aislada, como hiciste aquí, es la base para comprender cómo se conecta con
el resto del pipeline.
