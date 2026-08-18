# 🚀 FADEC Telemetry Analyzer & Anomaly Diagnosis Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5-green.svg?logo=qt)](https://www.riverbankcomputing.com/software/pyqt/)
[![Graphics](https://img.shields.io/badge/Graphics-PyQtGraph%20%2B%20OpenGL-orange.svg)](https://pyqtgraph.readthedocs.io/)
[![Data](https://img.shields.io/badge/Data-NumPy%20%2B%20Pandas-blueviolet.svg)](https://pandas.pydata.org/)

Havacılık ve gaz türbinli uçak motorları (FADEC - *Full Authority Digital Engine Control*) için geliştirilmiş; **3.000.000+ satırlık yüksek frekanslı telemetri verilerini** donanım hızlandırmalı olarak gerçek zamanlı (150+ FPS) görselleştiren, anomali kök neden analizi (Z-Score) ve sensör korelasyon incelemesi sunan yeni nesil masaüstü analiz platformu.

---

## 📑 İçindekiler
- [Öne Çıkan Özellikler](#-öne-çıkan-özellikler)
- [Teknoloji ve Mimari](#-teknoloji-ve-mimari)
- [Ekranlar ve Modüller](#-ekranlar-ve-modüller)
  - [1. Zaman Serisi Telemetri Analizi (Tab 1)](#1-zaman-serisi-telemetri-analizi-tab-1)
  - [2. Hata Ayıklama ve Limit İnceleme (Tab 2)](#2-hata-ayıklama-ve-limit-inceleme-tab-2)
  - [3. Detaylı Arıza Blokları Analizi (Tab 3)](#3-detaylı-arıza-blokları-analizi-tab-3)
  - [4. Kök Neden Sapma Analizi (Z-Score Radar)](#4-kök-neden-sapma-analizi-z-score-radar)
  - [5. Sensörler Arası Korelasyon Analizi (HeatMap)](#5-sensörler-arası-korelasyon-analizi-heatmap)
- [Kurulum ve Başlatma](#-kurulum-ve-başlatma)
- [Proje Dosya Hiyerarşisi](#-proje-dosya-hiyerarşisi)
- [Lisans](#-lisans)

---

## 🌟 Öne Çıkan Özellikler

* ⚡ **150+ FPS Donanım Hızlandırmalı Görselleştirme:** OpenGL destekli PyQtGraph altyapısı ve vektörize **LTTB (*Largest Triangle Three Buckets*)** algoritması ile milyonlarca veri noktasını tepe/çukur kaybetmeden 0.01 saniyede indirger.
* 🚀 **Sanal Tablo Modeli (*Virtual Model*):** Milyonlarca satırlık telemetri veri çerçevelerini (DataFrame) Qt bellek havuzunu şişirmeden anında yükler; sadece ekranda görünen satırları işler.
* 🎯 **Akıllı Drag-Release Seviyelendirme (LOD):** Grafik kaydırılırken (Pan/Drag) ağır hesaplamalar dondurulur, fare bırakıldığı anda görünür aralık milisaniyeler içinde çizilir.
* 🔍 **Z-Score Polar Radar Analizi:** Kriz anında normal çalışma aralıklarından sapan sensörleri istatistiksel standart sapma skoruyla kutupsal grafikte modeller.
* 🌡️ **İnteraktif Korelasyon Isı Haritası (HeatMap):** Çoklu sensörlerin eşzamanlı çalışma korelasyonunu görselleştirir.
* 📊 **Anlık Değişim (+/- Delta) Bilgi Kartları:** Hata başlangıç ve bitiş anlarına tıklandığında anlık sensör değerlerini ve önceki adıma göre değişimini renkli olarak sunar.
* ⏱️ **Dinamik Zaman Ölçekleyicisi:** Eksen etiketlerini zoom derinliğine göre otomatik olarak Gün.Ay Saat:Dakika, Saat:Dakika:Saniye veya Milisaniye formatına dönüştürür.

---

## 🛠️ Teknoloji ve Mimari

| Katman | Teknoloji | Görevi |
| :--- | :--- | :--- |
| **Arayüz (UI)** | PyQt5, Qt Designer | Modern koyu tema (QSS), asenkron pencereler ve çoklu sekme yönetimi |
| **Grafik Motoru** | PyQtGraph + OpenGL | Donanım hızlandırmalı 150 FPS zaman serisi çizimi |
| **Büyük Veri & İstatistik** | NumPy, Pandas | Vektörize veri filtreleme, Z-Score ve LTTB algoritmaları |
| **Analiz & Görselleştirme** | Matplotlib | Polar Radar ve Korelasyon Heatmap hesaplamaları |
| **Asenkron İş Parçacığı** | QThread | GB seviyesindeki CSV/Excel dosyalarını arayüzü dondurmadan arka planda okuma |

---

## 🖥️ Ekranlar ve Modüller

### 1. Zaman Serisi Telemetri Analizi (Tab 1)
* Tüm telemetri verisini listeleyen sanal veri tablosu.
* Tablo sütun başlıklarına tıklayarak grafiğe anında sensör eğrisi ekleme/kaldırma (Toggle).
* Ortalama, Min, Max değerlerini hesaplayan anlık istatistik paneli.
* Crosshair (fare takip imleci) ve bölge seçimiyle dinamik Zoom-In (Odaklanma).

### 2. Hata Ayıklama ve Limit İnceleme (Tab 2)
* Otomatik ayrıştırılan hata durum blokları listesi.
* Kritik motor sensörleri için (örn. S4 Türbin Çıkış Sıcaklığı) aşım limit çizgileri ve tolerans uyarıları.

### 3. Detaylı Arıza Blokları Analizi (Tab 3)
* Çoklu hata kategorilerini ve 20+ sensörü aynı anda tek ekranda inceleme.
* Şeffaf kırmızı kriz bölgeleri ve dikey lazer çizgileri.
* Noktasal tıklama ile çoklu sensör anlık değer ve delta (+/-) inceleme kutuları.

### 4. Kök Neden Sapma Analizi (Z-Score Radar)
* Motorun normal rejimi ile arıza anı arasındaki ortalama ve standart sapma farkını (Z-Score standardı) hesaplar.
* Krizin kök nedenini oluşturan sensörleri görsel olarak öne çıkarır.

### 5. Sensörler Arası Korelasyon Analizi (HeatMap)
* Seçilen sensörlerin Pearson korelasyon katsayılarını renkli ısı matrisi üzerinde gösterir.
* PNG formatında yüksek çözünürlüklü rapor çıktısı alma imkanı.

---

## 📦 Kurulum ve Başlatma

### Gereksinimler
* Python 3.10 veya üzeri
* pip paket yöneticisi

### Adım Adım Kurulum

1. **Projeyi Klonlayın:**
```bash
git clone https://github.com/<kullanici-adi>/FadecDataVisualization.git
cd FadecDataVisualization
```

2. **Sanal Ortam Oluşturun ve Aktifleştirin:**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install -r requirements.txt
```

4. **Uygulamayı Başlatın:**
```bash
python main.py
```

---

## 📁 Proje Dosya Hiyerarşisi

```text
├── main.py                     # Ana uygulama, grafik motoru ve kontrolcü
├── arayuz_python.py            # Ana pencere PyQt5 arayüz tasarımı
├── fadec_arayuz.ui             # Qt Designer ana arayüz kaynak dosyası
├── dosya_secim_python.py       # Veri yükleme iletişim kutusu arayüzü
├── limit_ayarlari_python.py    # Limit çizgileri parametre arayüzü
├── minmax_python.py            # Min/Max sınır seçim arayüzü
├── radar_penceresi.py          # Z-Score Radar penceresi arayüzü
├── heatmap_penceresi.py        # Korelasyon Isı Haritası arayüzü
├── GenerateFadecData.py        # Test amaçlı sentetik telemetri veri üretici
├── requirements.txt            # Python bağımlılık listesi
├── .gitignore                  # Git dışlama kuralları
└── README.md                   # Proje tanıtım ve dokümantasyon dosyası
```
