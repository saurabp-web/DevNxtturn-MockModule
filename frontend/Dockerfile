# STAGE 1: Build (Compiling Vue.js)
FROM node:20-slim AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# --- CRITICAL: VARIABLE SYNC ---
# We catch these from the --build-arg in cloudbuild.yaml
# We MUST use VITE_WS_BASE_URL because that is what your 
# notificationService.ts is looking for.
ARG VITE_GOOGLE_CLIENT_ID
ARG VITE_WS_BASE_URL

ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL

# Compile the app (Vite burns the /ws/ path into the JS files now)
RUN npm run build

# STAGE 2: Nginx (The Smart Gateway)
FROM nginx:stable-alpine

# Copy compiled files
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html

# Final Nginx Configuration including the WebSocket "Upgrade" Bridge
RUN echo 'server { \
    listen 8080; \
    \
    # 1. WEBSOCKET PROXY (Fixes the Feed and Real-time notifications) \
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
    # 3. AUTH REWRITE PROXY (Maps frontend /auth/ to backend /api/auth/) \
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