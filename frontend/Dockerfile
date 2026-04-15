# ==========================================
# STAGE 1: The Base (Installation)
# ==========================================
FROM node:20-slim AS base
WORKDIR /app
# Copy only the shopping list first for faster builds
COPY package*.json ./
RUN npm install

# ==========================================
# STAGE 2: The Developer (Local Dev with Hot Reload)
# ==========================================
FROM base AS develop-stage
COPY . .
EXPOSE 5173
# This runs the Vite dev server with --host so Docker can see it
CMD ["npm", "run", "dev", "--", "--host"]

# ==========================================
# STAGE 3: The Production (Nginx Storefront)
# ==========================================
FROM base AS production-stage
COPY . .
# Turn the code into tiny HTML/JS files
RUN npm run build

# Use Nginx for the final high-speed delivery
FROM nginx:stable-alpine
COPY --from=production-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]