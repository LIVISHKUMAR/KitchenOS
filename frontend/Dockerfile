# Stage 1: Build the React app
FROM node:18-alpine AS builder

# Build arg to select which app to build (pos, admin, kds, online-ordering)
ARG APP_NAME=pos

WORKDIR /app

# Copy workspace config files
COPY pnpm-workspace.yaml .
COPY package.json .

# Copy all apps and packages (needed for workspace resolution)
COPY apps/ apps/
COPY packages/ packages/

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Install dependencies
RUN pnpm install --frozen-lockfile

# Build the selected app
WORKDIR /app/apps/${APP_NAME}
RUN pnpm build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/apps/${APP_NAME}/dist /usr/share/nginx/html

# Copy nginx config (create default if not exists)
COPY --from=builder /app/apps/${APP_NAME}/nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || true

# Default nginx config for SPA routing
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
