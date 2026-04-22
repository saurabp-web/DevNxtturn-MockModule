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
# Copy the built files from the build-stage folder 'dist'
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Fix the port to 8080 and ensure Nginx serves the files
RUN sed -i 's/listen\(.*\)80;/listen 8080;/' /etc/nginx/conf.d/default.conf

# Add routing fix for Vue Router
RUN echo 'server { \
    listen 8080; \
    location / { \
    root /usr/share/nginx/html; \
    index index.html; \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]