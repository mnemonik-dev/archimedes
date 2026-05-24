# Stage 1: build the React app
FROM node:22-alpine AS ui-build
WORKDIR /app
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ .
RUN npm run build

# Stage 2: serve with non-root nginx (listens on 8080, no CAP_NET_BIND_SERVICE needed)
FROM nginxinc/nginx-unprivileged:alpine
COPY --from=ui-build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
