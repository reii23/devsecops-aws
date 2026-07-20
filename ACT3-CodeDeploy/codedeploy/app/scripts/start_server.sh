#!/bin/bash
# start_server.sh
# Hook AfterInstall: publica la Version 2 de la aplicacion y recarga nginx.
set -e

VERSION="2"
DEPLOY_DATE="$(date)"

cat > /usr/share/nginx/html/index.html << EOF
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Bienvenido</title>
  <style>
    body {
      background-color: #f0f4f8;
      font-family: Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .box {
      background-color: #ffffff;
      padding: 40px 60px;
      border-radius: 10px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      text-align: center;
    }
    h1 {
      color: #333333;
    }
    h2 {
      color: #28a745;
    }
    p {
      color: #555555;
    }
    .deploy-date {
      color: #888888;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <div class="box">
    <h1>Bienvenido</h1>
    <h2>Version ${VERSION}</h2>
    <p>Implementado con AWS CodeDeploy</p>
    <p class="deploy-date">Desplegado el: ${DEPLOY_DATE}</p>
  </div>
</body>
</html>
EOF

systemctl reload nginx

exit 0
