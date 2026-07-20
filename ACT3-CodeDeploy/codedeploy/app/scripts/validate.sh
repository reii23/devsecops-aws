#!/bin/bash
# validate.sh
# Hook ApplicationStart: valida que la aplicacion responda correctamente
# despues del despliegue.

# Esperar a que nginx termine de recargar/iniciar por completo.
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)

if [ "$HTTP_STATUS" -eq 200 ]; then
  echo "Validacion exitosa: la aplicacion respondio HTTP 200."
  exit 0
else
  echo "Validacion fallida: la aplicacion respondio HTTP ${HTTP_STATUS}."
  exit 1
fi
