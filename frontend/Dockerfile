# STAGE 1: Build
FROM node:20-slim AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Pass the Backend URL during build
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# STAGE 2: Nginx
FROM nginx:stable-alpine
# Copy the contents of the 'dist' folder to nginx html folder
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Create the Nginx config to support Vue Router (the 403 fix)
RUN echo 'server { \
    listen 8080; \
    server_name localhost; \
    location / { \
    root /usr/share/nginx/html; \
    index index.html; \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]