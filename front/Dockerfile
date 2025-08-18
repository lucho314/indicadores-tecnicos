# Usar una imagen base de Node.js para construir el frontend
FROM node:18-alpine AS build

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración primero para aprovechar cache de Docker
COPY package.json pnpm-lock.yaml ./

# Instalar dependencias
RUN npm install -g pnpm && pnpm install

# Copiar todos los archivos de configuración
COPY vite.config.ts tsconfig.json tsconfig.node.json ./
COPY tailwind.config.js postcss.config.mjs components.json ./
COPY index.html ./

# Copiar TODO el código fuente de una vez
COPY . .

# Definir variable de entorno para Vite durante la construcción
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Debug: Verificar que los archivos existen
RUN echo "=== Contenido del directorio actual ===" && ls -la
RUN echo "=== Contenido de src/ ===" && ls -la src/
RUN echo "=== Contenido de src/lib/ (si existe) ===" && ls -la src/lib/ || echo "src/lib/ no existe"
RUN echo "=== Buscar archivos utils.ts en todo el directorio ===" && find . -name "utils.ts" -type f
RUN echo "=== Estructura completa de src ===" && find src -type f | head -20

# Mostrar la variable para debug
RUN echo "Building with VITE_API_URL: $VITE_API_URL"

# Construir la aplicación
RUN pnpm run build

# Usar una imagen base de Nginx para servir el frontend
FROM nginx:stable-alpine

# Copiar los archivos construidos al directorio de Nginx
COPY --from=build /app/dist /usr/share/nginx/html
 
# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer el puerto 8001
EXPOSE 8001

# Comando por defecto para iniciar Nginx
CMD ["nginx", "-g", "daemon off;"]
