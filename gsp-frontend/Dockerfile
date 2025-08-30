FROM node:18-alpine

WORKDIR /app

# Sistem bağımlılıklarını yükle
RUN apk add --no-cache libc6-compat

# package.json ve package-lock.json dosyalarını kopyala
COPY package*.json ./

# Tüm dependencies'leri yükle (dev dependencies dahil)
RUN npm install

# Uygulama kodunu kopyala
COPY . .

# Next.js uygulamasını build et
RUN npm run build

# Port 3000'i aç
EXPOSE 3000

# Uygulamayı başlat
CMD ["npm", "start"] 