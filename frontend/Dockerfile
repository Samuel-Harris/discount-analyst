# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS development
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM node:22-bookworm-slim AS build
ARG ENV=PROD
ENV ENV=${ENV}
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.dashboard.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
