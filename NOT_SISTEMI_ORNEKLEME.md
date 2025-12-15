# 📊 Not Sistemi Örnek Kullanım

## ✅ Yenilenen Not Sistemi

Artık **kategori bazlı ağırlıklı not sistemi** çalışıyor!

### 🎯 Örnek Senaryo:

#### Ders: Web Programlama (BIL304)

**Not Kategorileri ve Ağırlıkları:**
- 📝 **Vize Sınavı**: %40 ağırlık
- 📝 **Final Sınavı**: %60 ağırlık

#### Öğrenci: Ahmet Yılmaz

**Aldığı Notlar:**
- Vize: 60/100
- Final: 60/100

**Hesaplama:**
```
Vize Katkısı  = 60 × 0.40 = 24 puan
Final Katkısı = 60 × 0.60 = 36 puan
─────────────────────────────────
TOPLAM        = 24 + 36  = 60 puan → CC (Yeterli)
```

---

## 🔧 Admin Panelde Kurulum

### 1. Not Kategorisi Oluşturma

**Admin Panel → Gradebook → Grade Categories → Add**

```
Kurs Grubu: Web Programlama - Grup A
Kategori Adı: Vize Sınavı
Kategori Tipi: Exam (Sınav)
Ağırlık: 40
Aktif: ✓
```

```
Kurs Grubu: Web Programlama - Grup A
Kategori Adı: Final Sınavı
Kategori Tipi: Exam (Sınav)
Ağırlık: 60
Aktif: ✓
```

### 2. Not Kalemi Oluşturma

**Admin Panel → Gradebook → Grade Items → Add**

```
Kategori: Vize Sınavı
Ad: Vize Sınavı
Maksimum Puan: 100
Kategori İçi Ağırlık: 100
Durum: Published
```

```
Kategori: Final Sınavı
Ad: Final Sınavı
Maksimum Puan: 100
Kategori İçi Ağırlık: 100
Durum: Published
```

### 3. Not Girişi

**Admin Panel → Gradebook → Grades → Add**

```
Öğrenci: Ahmet Yılmaz
Not Kalemi: Vize Sınavı
Puan: 60
```

```
Öğrenci: Ahmet Yılmaz
Not Kalemi: Final Sınavı
Puan: 60
```

---

## 📱 Öğrenci Görünümü

Öğrenci `http://127.0.0.1:8000/gradebook/my-grades/` sayfasında şunu görür:

```
┌──────────────────────────────────────────┐
│ Web Programlama (BIL304)                 │
├──────────────────────────────────────────┤
│                                          │
│ NOT DAĞILIMI                             │
│                                          │
│ ┌─────────────┐  ┌─────────────┐       │
│ │ Vize Sınavı │  │Final Sınavı │       │
│ │   60.0      │  │   60.0      │       │
│ │ Ağırlık:40% │  │ Ağırlık:60% │       │
│ │ Katkı: 24.00│  │ Katkı: 36.00│       │
│ └─────────────┘  └─────────────┘       │
│                                          │
│ GENEL ORTALAMA                           │
│ ┌────────────────────────────────────┐  │
│ │         60.0  →  CC                │  │
│ │      Yeterli (2.00)                │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ℹ️ Not Durumu:                           │
│ Yeterli (2.00) - Dersten CC ile geçti   │
│                                          │
│ 🧮 Not Hesaplama Detayı:                 │
│ • Vize: 60.0 × %40 = 24.00 katkı        │
│ • Final: 60.0 × %60 = 36.00 katkı       │
│ • TOPLAM: 60.0 → CC                     │
└──────────────────────────────────────────┘
```

---

## 🎓 Farklı Senaryolar

### Senaryo 1: Yüksek Başarı
```
Vize:  88/100 × 40% = 35.2 katkı
Final: 92/100 × 60% = 55.2 katkı
───────────────────────────────
TOPLAM: 90.4 → AA (Mükemmel)
```

### Senaryo 2: Ortalama
```
Vize:  70/100 × 40% = 28.0 katkı
Final: 75/100 × 60% = 45.0 katkı
───────────────────────────────
TOPLAM: 73.0 → BB (İyi)
```

### Senaryo 3: Başarısız
```
Vize:  40/100 × 40% = 16.0 katkı
Final: 45/100 × 60% = 27.0 katkı
───────────────────────────────
TOPLAM: 43.0 → FF (Başarısız)
```

---

## 🔢 Karmaşık Örnek (4 Kategori)

```
Ödev (%20):     80/100 × 20% = 16.0
Quiz (%10):     90/100 × 10% =  9.0
Vize (%30):     75/100 × 30% = 22.5
Final (%40):    85/100 × 40% = 34.0
────────────────────────────────────
TOPLAM:                        81.5 → BA (Çok İyi)
```

---

## 📋 Not Skalası (Selçuk Üni)

| Puan     | Harf | Katsayı | Durum           |
|----------|------|---------|-----------------|
| 88-100   | AA   | 4.00    | Mükemmel        |
| 80-87    | BA   | 3.50    | Çok İyi         |
| 73-79    | BB   | 3.00    | İyi             |
| 66-72    | CB   | 2.50    | Orta            |
| 60-65    | CC   | 2.00    | Yeterli         |
| 55-59    | DC   | 1.50    | Şartlı Geçer    |
| 50-54    | DD   | 1.00    | Şartlı Geçer    |
| 0-49     | FF   | 0.00    | Başarısız       |

---

## ✅ Avantajlar

1. **Esnek Yapı**: İstediğiniz kadar kategori ekleyebilirsiniz
2. **Ağırlıklı Hesaplama**: Her kategorinin farklı etkisi
3. **Detaylı Görünüm**: Öğrenci her notun katkısını görebilir
4. **Otomatik Harf Notu**: Sistem otomatik CC, AA gibi harfleri atar
5. **Selçuk Üni Uyumlu**: Resmi yönetmeliğe göre hesaplama

---

## 🚀 Hızlı Başlangıç

1. Admin panele girin: `/admin/`
2. **Grade Categories** → Vize (%40) ve Final (%60) ekleyin
3. **Grade Items** → Her kategoriye not kalemi ekleyin
4. **Grades** → Öğrenci notlarını girin
5. Öğrenci `/gradebook/my-grades/` sayfasından görüntülesin!

**Not sistemi artık tam fonksiyonel! 🎉**
