FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
# Cypress não é usado no build da imagem.
ENV CYPRESS_INSTALL_BINARY=0
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
