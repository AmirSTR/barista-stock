# ==============================================================================
# Stage 1: Build Telegram WebApp frontend
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies using lockfile
COPY package*.json ./
RUN npm ci

# Copy source files
COPY . ./

ARG VITE_API_URL
ARG VITE_ENABLE_MOCKS=false
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_ENABLE_MOCKS=$VITE_ENABLE_MOCKS

# Build production assets (Vite -> dist)
RUN test -n "$VITE_API_URL" || (echo "VITE_API_URL is required for the standalone frontend image" && exit 1)
RUN npm run build

# ==============================================================================
# Stage 2: Serve static bundle via Nginx with automatic $PORT substitution
# ==============================================================================
FROM nginx:alpine

# Default PORT to 80 if not supplied by platform
ENV PORT=80

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy template for automatic envsubst by official Nginx image on startup
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
