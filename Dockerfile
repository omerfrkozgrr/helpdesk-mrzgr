# Python'un resmi sürümünü temel al
FROM python:3.10-slim

# Çalışma klasörünü ayarla
WORKDIR /app

# Gereksinim dosyasını kopyala ve yükle
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . /app/