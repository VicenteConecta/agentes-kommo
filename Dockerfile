# Usar imagen base oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Copiar script de entrada
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Cloud Run requiere que la aplicación escuche en la variable PORT
# Por defecto es 8080
ENV PORT=8080

# Exponer puerto (informativo)
EXPOSE 8080

# Usar el script de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
