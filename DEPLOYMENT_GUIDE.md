# 🚀 Production Deployment Guide

Kapsamlı production deployment rehberi.

## 📋 Ön Hazırlık

### Sistem Gereksinimleri

- **OS:** Ubuntu 20.04 LTS veya üzeri
- **RAM:** Minimum 2GB (4GB+ önerilir)
- **Disk:** Minimum 20GB
- **CPU:** 2 core+

### Software Stack

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx 1.18+
- Gunicorn 21+

## 🔧 Adım 1: Sunucu Hazırlığı

### 1.1. Sunucu Güncellemesi

```bash
sudo apt update
sudo apt upgrade -y
```

### 1.2. Gerekli Paketlerin Kurulumu

```bash
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib \
    redis-server nginx git curl build-essential libpq-dev
```

### 1.3. Firewall Ayarları

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

## 🗄️ Adım 2: Database Kurulumu

### 2.1. PostgreSQL Yapılandırması

```bash
sudo -u postgres psql
```

PostgreSQL içinde:

```sql
CREATE DATABASE uzaktanogrenme;
CREATE USER dbuser WITH PASSWORD 'güçlü_şifre_buraya';
ALTER ROLE dbuser SET client_encoding TO 'utf8';
ALTER ROLE dbuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE dbuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE uzaktanogrenme TO dbuser;
\q
```

### 2.2. Redis Yapılandırması

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server
```

## 📦 Adım 3: Proje Deployment

### 3.1. Kullanıcı Oluşturma

```bash
sudo adduser uzaktanogrenme
sudo usermod -aG sudo uzaktanogrenme
su - uzaktanogrenme
```

### 3.2. Proje Klonlama

```bash
cd ~
git clone <repository-url> OKULPROJE
cd OKULPROJE
```

### 3.3. Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4. Environment Variables

```bash
nano .env
```

`.env` içeriği:

```env
DJANGO_SECRET_KEY=<python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=uzaktanogrenme
DB_USER=dbuser
DB_PASSWORD=güçlü_şifre_buraya
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/1

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 3.5. Django Setup

```bash
# Migrations
python manage.py migrate

# Static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

## 🔐 Adım 4: SSL Sertifikası

### 4.1. Certbot Kurulumu

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 4.2. SSL Sertifikası Alımı

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🌐 Adım 5: Gunicorn Yapılandırması

### 5.1. Gunicorn Test

```bash
cd ~/OKULPROJE
source venv/bin/activate
gunicorn --bind 0.0.0.0:8000 config.wsgi:application
```

### 5.2. Systemd Service Oluşturma

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

İçerik:

```ini
[Unit]
Description=Gunicorn daemon for Uzaktan Ogrenme
After=network.target

[Service]
User=uzaktanogrenme
Group=www-data
WorkingDirectory=/home/uzaktanogrenme/OKULPROJE
EnvironmentFile=/home/uzaktanogrenme/OKULPROJE/.env
ExecStart=/home/uzaktanogrenme/OKULPROJE/venv/bin/gunicorn \
          --workers 4 \
          --bind unix:/home/uzaktanogrenme/OKULPROJE/gunicorn.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5.3. Service Başlatma

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

## 🚦 Adım 6: Nginx Yapılandırması

### 6.1. Nginx Config

```bash
sudo nano /etc/nginx/sites-available/uzaktanogrenme
```

İçerik:

```nginx
upstream uzaktanogrenme {
    server unix:/home/uzaktanogrenme/OKULPROJE/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    client_max_body_size 10M;
    
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias /home/uzaktanogrenme/OKULPROJE/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /home/uzaktanogrenme/OKULPROJE/media/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://uzaktanogrenme;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### 6.2. Nginx Aktifleştirme

```bash
sudo ln -s /etc/nginx/sites-available/uzaktanogrenme /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 📊 Adım 7: Monitoring & Logging

### 7.1. Log Dizini Oluşturma

```bash
sudo mkdir -p /var/log/uzaktanogrenme
sudo chown uzaktanogrenme:www-data /var/log/uzaktanogrenme
```

### 7.2. Logrotate Yapılandırması

```bash
sudo nano /etc/logrotate.d/uzaktanogrenme
```

İçerik:

```
/var/log/uzaktanogrenme/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 uzaktanogrenme www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn
    endscript
}
```

## 🔄 Adım 8: Backup Stratejisi

### 8.1. Database Backup Script

```bash
nano ~/backup_db.sh
```

İçerik:

```bash
#!/bin/bash
BACKUP_DIR="/home/uzaktanogrenme/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="uzaktanogrenme"

mkdir -p $BACKUP_DIR

# Database backup
PGPASSWORD="güçlü_şifre_buraya" pg_dump -U dbuser -h localhost $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/uzaktanogrenme/OKULPROJE/media/

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x ~/backup_db.sh
```

### 8.2. Cron Job Ekleme

```bash
crontab -e
```

Ekle:

```
0 2 * * * /home/uzaktanogrenme/backup_db.sh >> /var/log/uzaktanogrenme/backup.log 2>&1
```

## 🔍 Adım 9: Health Checks

### 9.1. Django Check

```bash
cd ~/OKULPROJE
source venv/bin/activate
python manage.py check --deploy
```

### 9.2. Service Status

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
sudo systemctl status redis-server
sudo systemctl status postgresql
```

## 🚀 Adım 10: Deployment Sonrası

### 10.1. Test

```bash
# Domain erişim testi
curl -I https://yourdomain.com

# Admin panel testi
curl -I https://yourdomain.com/admin/
```

### 10.2. Performance Tuning

**Gunicorn workers hesaplama:**
```
workers = (2 * CPU_CORES) + 1
```

**Nginx cache ayarları:**
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;
```

## 📝 Adım 11: Maintenance

### 11.1. Güncelleme Prosedürü

```bash
cd ~/OKULPROJE
source venv/bin/activate

# Yedek al
~/backup_db.sh

# Güncellemeleri çek
git pull origin main

# Bağımlılıkları güncelle
pip install -r requirements.txt --upgrade

# Migrations
python manage.py migrate

# Static files
python manage.py collectstatic --noinput

# Servisleri yeniden başlat
sudo systemctl restart gunicorn
sudo systemctl reload nginx
```

### 11.2. Monitoring Commands

```bash
# Django logs
tail -f /var/log/uzaktanogrenme/django.log

# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Redis monitoring
redis-cli monitor
```

## ⚠️ Troubleshooting

### Static files görünmüyor

```bash
python manage.py collectstatic --noinput
sudo chown -R uzaktanogrenme:www-data staticfiles/
sudo chmod -R 755 staticfiles/
```

### Gunicorn başlamıyor

```bash
sudo journalctl -u gunicorn --no-pager
sudo systemctl restart gunicorn
```

### Database bağlantı hatası

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"
```

## 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin
2. Service statuslarını kontrol edin
3. GitHub Issues'a ticket açın

---

**✅ Deployment tamamlandı! Sisteminiz production'da!**
