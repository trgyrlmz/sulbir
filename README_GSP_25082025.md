# GSP_25082025 - Genel Su Projesi

## 🚀 Proje Hakkında
Bu proje, su kaynakları yönetimi için geliştirilmiş kapsamlı bir sistemdir. Frontend (React/Next.js) ve Backend (Django) teknolojileri kullanılarak oluşturulmuştur.

## 📅 Versiyon Bilgisi
- **Versiyon**: v1.0.0-stable
- **Tarih**: 25 Ağustos 2025
- **Durum**: Tamamen çalışır durumda

## 🏗️ Sistem Mimarisi
- **Frontend**: Next.js 15 + React
- **Backend**: Django 4.2
- **Veritabanı**: PostgreSQL
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx

## 📦 Kurulum

### 1. Repository Clone
```bash
git clone https://github.com/trgyrlmz/GSP_25082025.git
cd GSP_25082025
```

### 2. Docker Servisleri Başlatma
```bash
docker-compose up -d
```

### 3. Veritabanı Kurulumu
**⚠️ ÖNEMLİ**: Bu adım zorunludur! Veritabanı verileri olmadan sistem çalışmaz.

#### 3.1 Veritabanı Backup'ını Yükleme
```bash
# Backup dosyasını container'a kopyala
docker cp gsp_database_backup_25082025.sql gsp_yeni-db-1:/tmp/

# PostgreSQL'e yükle
docker-compose exec db psql -U postgres -d sulama_db -f /tmp/gsp_database_backup_25082025.sql
```

#### 3.2 Alternatif: SQL Script'ler ile Veri Yükleme
Eğer backup yükleme çalışmazsa, aşağıdaki script'leri sırayla çalıştırın:

```bash
# 1. Ürün verileri
docker cp load_production_data.sql gsp_yeni-db-1:/tmp/
docker-compose exec db psql -U postgres -d sulama_db -f /tmp/load_production_data.sql

# 2. Günlük depolama tesisleri su miktarları
docker cp load_all_gunluk_depolama_tesisi_su_miktari.sql gsp_yeni-db-1:/tmp/
docker-compose exec db psql -U postgres -d sulama_db -f /tmp/load_all_gunluk_depolama_tesisi_su_miktari.sql

# 3. 2022-2025 ek veriler
docker cp load_2022_2025_gunluk_depolama_tesisi_su_miktari.sql gsp_yeni-db-1:/tmp/
docker-compose exec db psql -U postgres -d sulama_db -f /tmp/load_2022_2025_gunluk_depolama_tesisi_su_miktari.sql

# 4. 2025 yılı veriler
docker cp load_2025_gunluk_depolama_tesisi_su_miktari.sql gsp_yeni-db-1:/tmp/
docker-compose exec db psql -U postgres -d sulama_db -f /tmp/load_2025_gunluk_depolama_tesisi_su_miktari.sql

# 5. Günlük şebeke su miktarları
docker cp load_gunluk_sebeke_su_miktari.sql gsp_yeni-db-1:/tmp/
docker-compose exec db psql -U postgres -d sulama_db -f /tmp/load_gunluk_sebeke_su_miktari.sql
```

### 4. Django Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 5. Frontend Build
```bash
cd gsp-frontend
npm install
npm run build
```

## 🗄️ Veritabanı İçeriği

### Mevcut Tablolar ve Veri Sayıları:
- **sulama_urun**: 30 ürün
- **sulama_yillikurundetay**: Yıllık ürün detayları
- **sulama_gunlukdepolamatesisisumiktari**: 366 kayıt (2017-2025)
- **sulama_gunluksebekeyealinansumiktari**: 57 kayıt (2020-2025)
- **sulama_depolamatesisi**: Depolama tesisleri
- **sulama_depolamatesisiabak**: Baraj abak verileri

### Veri Kapsamı:
- **Tarih Aralığı**: 2017-2025
- **Toplam Kayıt**: 800+ kayıt
- **Veri Türleri**: Ürünler, su miktarları, kot-hacim ilişkileri

## 🌐 Erişim Bilgileri

### Frontend
- **URL**: http://localhost:3000
- **Port**: 3000

### Backend API
- **URL**: http://localhost:8000
- **Port**: 8000

### Admin Panel
- **URL**: http://localhost:8000/admin
- **Port**: 8000

### PostgreSQL
- **Host**: localhost
- **Port**: 5432
- **Database**: sulama_db
- **User**: postgres

## 🔧 Performans Optimizasyonları

### Frontend
- React useCallback/useMemo optimizasyonları
- Next.js build optimizasyonları
- Bundle analyzer entegrasyonu

### Backend
- Database connection pooling
- API throttling
- Session optimizasyonları

## 📁 Önemli Dosyalar

### Veritabanı Backup
- `gsp_database_backup_25082025.sql` - Tam veritabanı backup'ı

### SQL Script'ler
- `load_production_data.sql` - Ürün verileri
- `load_all_gunluk_depolama_tesisi_su_miktari.sql` - Depolama tesisleri
- `load_gunluk_sebeke_su_miktari.sql` - Şebeke su miktarları

### Konfigürasyon
- `docker-compose.yml` - Docker servisleri
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies

## 🚨 Sorun Giderme

### Veritabanı Bağlantı Hatası
```bash
# Servisleri yeniden başlat
docker-compose down
docker-compose up -d

# Migrations çalıştır
docker-compose exec web python manage.py migrate
```

### Frontend Build Hatası
```bash
cd gsp-frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Docker Container Hatası
```bash
# Container loglarını kontrol et
docker-compose logs

# Container'ları yeniden başlat
docker-compose restart
```

## 📞 Destek

Herhangi bir sorun yaşarsanız:
1. Bu README dosyasını tekrar okuyun
2. Docker loglarını kontrol edin
3. Veritabanı bağlantısını doğrulayın

## 🎯 Sonraki Adımlar

1. **Veritabanı backup'ını yükleyin** (zorunlu)
2. **Docker servislerini başlatın**
3. **Frontend'i build edin**
4. **Sistemi test edin**

---

**Not**: Bu sistem tamamen çalışır durumda test edilmiştir. Tüm veriler production sunucusundan alınmıştır. 