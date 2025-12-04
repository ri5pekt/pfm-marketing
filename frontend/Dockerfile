# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Build argument for API base URL
ARG VITE_API_BASE_URL=/api

COPY package.json ./
RUN npm install

COPY . .
# Set environment variable for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

