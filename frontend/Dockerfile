# STAGE 1: Build (Compiling Vue.js)
FROM node:20-slim AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# --- CRITICAL: Injecting Environment Variables for the Build ---
# These ARGs must be passed from cloudbuild.yaml. 
# Vite "bakes" these into the JS files at this exact moment.
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_API_URL
ARG VITE_WS_URL

ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL

# Compile the Vue app
RUN npm run build

# STAGE 2: Nginx (The Smart Gateway)
FROM nginx:stable-alpine

# Copy the compiled static files
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html

# Write the Nginx Configuration
RUN echo 'server { \
    listen 8080; \
    \
    # 1. WEBSOCKET PROXY (Fixes the Feed/Notifications) \
    # This block allows "Upgrading" the connection from HTTP to WS. \
    location /ws/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/ws/; \
    proxy_http_version 1.1; \
    proxy_set_header Upgrade $http_upgrade; \
    proxy_set_header Connection "upgrade"; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    proxy_set_header X-Real-IP $remote_addr; \
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # 2. API PROXY \
    location /api/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/api/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    proxy_set_header X-Real-IP $remote_addr; \
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # 3. AUTH REWRITE PROXY (Maps /auth/ to /api/auth/) \
    location /auth/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/api/auth/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    proxy_set_header X-Real-IP $remote_addr; \
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # 4. DJANGO ADMIN PROXY \
    location /admin/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/admin/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    } \
    \
    # 5. ADMIN STATIC ASSETS \
    location /static/admin/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/static/admin/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    } \
    \
    # 6. FRONTEND VUE APP (SPA Routing) \
    location / { \
    root /usr/share/nginx/html; \
    index index.html; \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]