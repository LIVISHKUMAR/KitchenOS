# Stage 1: Build the React app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy workspace config files
COPY pnpm-workspace.yaml .
COPY turbo.json .
COPY package.json .

# Copy the app
COPY apps/pos apps/pos

# Install pnpm
RUN npm install -g pnpm

# Install dependencies
WORKDIR /app/apps/pos
RUN pnpm install

# Build the app
RUN pnpm build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/apps/pos/dist /usr/share/nginx/html

# Copy custom nginx config
COPY apps/pos/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]