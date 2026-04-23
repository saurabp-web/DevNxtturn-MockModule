# STAGE 1: Build
FROM node:20-slim AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# --- KEPT: Your Google ID Logic ---
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
# ----------------------------------

RUN npm run build

# STAGE 2: Nginx (The Gateway)
FROM nginx:stable-alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html

RUN echo 'server { \
    listen 8080; \
    \
    # 1. KEPT: Your existing API Proxy \
    location /api/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/api/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    proxy_set_header X-Real-IP $remote_addr; \
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # 2. ADDED: Admin Proxy (The bridge for dev.nxtturn.com/admin/) \
    location /admin/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/admin/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    proxy_set_header X-Real-IP $remote_addr; \
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
    proxy_set_header X-Forwarded-Proto $scheme; \
    } \
    \
    # 3. ADDED: Admin Static Assets (So the admin looks pretty) \
    location /static/admin/ { \
    proxy_pass https://nxtturn-backend-dev-656842361738.us-central1.run.app/static/admin/; \
    proxy_set_header Host nxtturn-backend-dev-656842361738.us-central1.run.app; \
    } \
    \
    # 4. KEPT: Your Vue App routing \
    location / { \
    root /usr/share/nginx/html; \
    index index.html; \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]