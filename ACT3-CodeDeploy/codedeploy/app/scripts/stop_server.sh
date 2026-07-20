#!/bin/bash
# stop_server.sh
# Hook BeforeInstall: detiene la aplicacion (si esta corriendo) antes de
# instalar la nueva revision, sin fallar si nginx no esta activo.

# Detener el proceso de la aplicacion si esta corriendo.
# El '|| true' evita que el script falle si pkill no encuentra procesos.
pkill -f "codedeploy-app" || true

# Recargar nginx de forma segura, sin fallar el deployment si el servicio
# no esta activo en este momento.
if systemctl is-active --quiet nginx; then
  systemctl reload nginx || true
else
  echo "nginx no esta activo, se omite el reload."
fi

exit 0
