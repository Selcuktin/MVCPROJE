# OKULPROJE - Production Deployment Rehberi

## 🚀 Deployment Hazırlanması

### 1. Environment Setup

```bash
# Production sunucusunda sanal ortam oluştur
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Environment Değişkenleri

`.env` dosyası oluştur (production değerleriyle):

```bash
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-minimum-50-chars
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=okulproje_prod
DB_USER=okulproje_user
DB_PASSWORD=very-secure-password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-specific-password

# Redis
REDIS_URL=redis://localhost:6379/1

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 3. Database Kurulumu (PostgreSQL)

```bash
# PostgreSQL yükle
sudo apt install postgresql postgresql-contrib

# Database ve user oluştur
sudo -u postgres psql
CREATE DATABASE okulproje_prod;
CREATE USER okulproje_user WITH PASSWORD 'very-secure-password';
ALTER ROLE okulproje_user SET client_encoding TO 'utf8';
ALTER ROLE okulproje_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE okulproje_user SET default_transaction_deferrable TO on;
ALTER ROLE okulproje_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE okulproje_prod TO okulproje_user;
\q
```

### 4. Static & Media Dosyaları

```bash
# Static dosyaları topla
python manage.py collectstatic --noinput --clear

# Media dizini oluştur
mkdir -p media
chmod 755 media
```

### 5. Database Migration

```bash
# Production settings kullanarak migrate yap
python manage.py migrate --settings=config.settings_production
```

### 6. Gunicorn Kurulumu

```bash
pip install gunicorn

# Test et
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --settings=config.settings_production
```

### 7. Systemd Service Oluştur

`/etc/systemd/system/okulproje.service`:

```ini
[Unit]
Description=OKULPROJE Django Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/okulproje
Environment="PATH=/var/www/okulproje/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings_production"
ExecStart=/var/www/okulproje/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/okulproje.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Service başlat
sudo systemctl enable okulproje
sudo systemctl start okulproje
```

### 8. Nginx Konfigürasyonu

`/etc/nginx/sites-available/okulproje`:

```nginx
upstream okulproje {
    server unix:/run/okulproje.sock;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Logging
    access_log /var/log/nginx/okulproje_access.log;
    error_log /var/log/nginx/okulproje_error.log;
    
    # Client max body size (for file uploads)
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://okulproje;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/okulproje/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/okulproje/media/;
        expires 7d;
    }
}
```

```bash
# Nginx sitesini etkinleştir
sudo ln -s /etc/nginx/sites-available/okulproje /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL Sertifikası (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

### 10. Redis Kurulumu

```bash
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 11. Logging & Monitoring

```bash
# Log dosyaları
mkdir -p /var/www/okulproje/logs
chmod 755 /var/www/okulproje/logs

# Logrotate ayarla
sudo nano /etc/logrotate.d/okulproje
```

## 📊 API Erişim

Production'da API endpoints:

- **Swagger Docs**: `https://yourdomain.com/api/docs/`
- **ReDoc**: `https://yourdomain.com/api/redoc/`
- **Token Obtain**: `POST /api/token/`
- **Token Refresh**: `POST /api/token/refresh/`
- **API Schema**: `GET /api/schema/`

## 🔒 Security Checklist

- [ ] SECRET_KEY değiştirildi
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS ayarlandı
- [ ] SSL/HTTPS etkin
- [ ] CSRF koruması etkin
- [ ] Güvenli şifre politikası
- [ ] Rate limiting aktif
- [ ] Logging konfigürasyonu
- [ ] Backups planlandı
- [ ] Firewall kuralları ayarlandı

## 📈 Performance Optimization

```python
# settings_production.py'de
DATABASES['default']['CONN_MAX_AGE'] = 600
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
    }
}
```

## 🔄 Backup Stratejisi

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/okulproje"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump okulproje_prod > $BACKUP_DIR/db_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/okulproje/media/

# Eski backupları sil (30 gün üzerinde)
find $BACKUP_DIR -mtime +30 -delete
```

Crontab'a ekle:
```bash
0 2 * * * /var/www/okulproje/backup.sh
```

## 🚨 Troubleshooting

### Gunicorn bağlantısı hatası
```bash
sudo systemctl restart okulproje
sudo journalctl -u okulproje -f
```

### Nginx 502 Bad Gateway
```bash
sudo systemctl restart nginx
sudo tail -f /var/log/nginx/error.log
```

### Database bağlantı hatası
```bash
python manage.py dbshell --settings=config.settings_production
```
