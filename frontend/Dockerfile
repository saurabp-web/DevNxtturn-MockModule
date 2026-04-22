# ==========================================
# STAGE 1: The Base (Installation)
# ==========================================
FROM node:20-slim AS base
WORKDIR /app
COPY package*.json ./
RUN npm install

# ==========================================
# STAGE 2: The Developer (Local Dev)
# ==========================================
FROM base AS develop-stage
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# ==========================================
# STAGE 3: The Production (Nginx Storefront)
# ==========================================
FROM base AS production-stage
COPY . .

# --- FIX 1: Accept the Backend URL from Google Cloud ---
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Use Nginx for the final high-speed delivery
FROM nginx:stable-alpine
COPY --from=production-stage /app/dist /usr/share/nginx/html

# --- FIX 2: Change Nginx port from 80 to 8080 ---
RUN sed -i 's/listen\(.*\)80;/listen 8080;/' /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]