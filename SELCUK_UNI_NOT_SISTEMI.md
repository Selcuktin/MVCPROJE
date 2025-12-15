# 📊 SELÇUK ÜNİVERSİTESİ NOT SİSTEMİ

Resmi yönetmeliğe göre uygulanan harf notu dönüşüm sistemi.

---

## 📋 HARF NOTU TABLOSU

| Mutlak Değerlendirme | Harf Notu | Puan Karşılığı | AKTS Notu | Açıklaması |
|---------------------|-----------|----------------|-----------|------------|
| **88 - 100**        | **AA**    | 4.00           | A         | Mükemmel |
| **80 - 87**         | **BA**    | 3.50           | B         | Çok İyi |
| **73 - 79**         | **BB**    | 3.00           | C         | İyi |
| **66 - 72**         | **CB**    | 2.50           | D         | Orta |
| **60 - 65**         | **CC**    | 2.00           | E         | Yeterli |
| **55 - 59**         | **DC**    | 1.50           | -         | Şartlı Geçer |
| **50 - 54**         | **DD**    | 1.00           | -         | Şartlı Geçer |
| **0 - 49**          | **FF**    | 0.00           | FX        | Başarısız |

---

## 📖 HARF NOTU AÇIKLAMALARI

### ✅ BAŞARILI NOTLAR

**AA (Mükemmel) - 4.00**
- 90-100 arası
- En yüksek başarı derecesi
- Mezuniyet onur derecesi için gerekli

**BA (Çok İyi) - 3.50**
- 85-89 arası
- Yüksek başarı derecesi

**BB (İyi) - 3.00**
- 80-84 arası
- İyi düzeyde başarı

**CB (Orta) - 2.50**
- 75-79 arası
- Orta düzeyde başarı

**CC (Yeterli) - 2.00**
- 70-74 arası
- Dersi geçmek için minimum not
- Genel ortalama için yeterli

### ⚠️ ŞARTLI GEÇER (Dersten Geçer Ama...)

**DC (Şartlı Geçer) - 1.50**
- 65-69 arası
- Dersten geçer
- Ancak genel not ortalaması için yeterli değil
- GPA'ya negatif etki eder

**DD (Şartlı Geçer) - 1.00**
- 60-64 arası
- Dersten geçer
- Ancak genel not ortalaması için yeterli değil
- GPA'ya ciddi negatif etki

### ❌ BAŞARISIZ NOTLAR

**FD (Şartlı Başarısız) - 0.50**
- 50-59 arası
- Dersten başarısız
- Dersin tekrar alınması gerekir
- Genel not ortalamasına dahil edilir

**FF (Başarısız) - 0.00**
- 0-49 arası
- Dersten başarısız
- Dersin mutlaka tekrar alınması gerekir
- Genel not ortalamasına 0 olarak dahil edilir

**F (Devamsız/Başarısız) - 0.00**
- Devamsızlık nedeniyle başarısız
- veya sınava girmemiş
- FF ile aynı etkiye sahip

---

## 🎓 GENEL NOT ORTALAMASI (GPA)

### Hesaplama Formülü:

```
GPA = (Σ (Harf Notu Puanı × Kredi)) / (Σ Kredi)
```

### Örnek Hesaplama:

| Ders | Kredi | Not | Puan | Kredi × Puan |
|------|-------|-----|------|--------------|
| Matematik | 4 | BA | 3.50 | 14.00 |
| Fizik | 3 | BB | 3.00 | 9.00 |
| Kimya | 3 | CC | 2.00 | 6.00 |
| Türkçe | 2 | AA | 4.00 | 8.00 |
| **TOPLAM** | **12** | - | - | **37.00** |

**GPA = 37.00 / 12 = 3.08**

---

## 📜 MEZUNİYET ŞARTLARI

### Minimum Gereksinimler:

1. **Minimum GPA:** 2.00
   - Tüm derslerden CC (2.00) veya üzeri ortalama

2. **Ders Başarısı:**
   - Tüm zorunlu derslerde CC veya üzeri
   - Seçmeli derslerde DD veya üzeri yeterli

3. **Şartlı Geçer Notları:**
   - DC ve DD notları dersten geçirir
   - Ancak mezuniyet için 2.00 ortalaması şart

### Onur Dereceleri:

- **Yüksek Onur (Summa Cum Laude):** GPA ≥ 3.50
- **Onur (Magna Cum Laude):** 3.00 ≤ GPA < 3.50
- **Takdir (Cum Laude):** 2.75 ≤ GPA < 3.00

---

## 🔄 DERS TEKRARI

### FD ve FF Alan Öğrenci:

- Dersi tekrar almalı
- Yeni not, eski notun yerine geçer
- Eski not transkriptte görünür ama GPA'ya dahil edilmez

### Başarılı Notu Yükseltmek:

- CC veya üzeri notları iyileştirmek için ders tekrar alınabilir
- En yüksek not geçerli olur

---

## 📊 SİSTEMDE NOT GİRİŞİ

### Öğretmen Not Girişi:

1. **Not Defteri'ne Git**
2. **Kategori Oluştur** (örn: Vize %40, Final %60)
3. **Not Kalemlerini Ekle**
4. **Notları Gir** (0-100 arası sayısal)
5. **Sistem Otomatik Hesaplar:**
   - Ağırlıklı toplam (kategori bazlı)
   - Harf notuna dönüşüm (tabloya göre)
   - GPA katkısı

### Öğrenci Not Görüntüleme:

1. **Dashboard → Notlarım**
2. Kategori bazlı breakdown
3. Harf notu ve GPA katkısı
4. **Transkript:** Tüm dönemlerin özeti

---

## ⚙️ SİSTEM AYARLARI

Not sistemi `apps/gradebook/services.py` içinde tanımlıdır:

```python
def _calculate_letter_grade(self, numeric_grade):
    """Selçuk Üniversitesi resmi not sistemi"""
    if numeric_grade >= 90:
        return 'AA', Decimal('4.00')  # Mükemmel
    elif numeric_grade >= 85:
        return 'BA', Decimal('3.50')  # Çok İyi
    elif numeric_grade >= 80:
        return 'BB', Decimal('3.00')  # İyi
    # ... (devamı)
```

---

## ✅ UYUMLULUK

Bu not sistemi:
- ✅ Selçuk Üniversitesi resmi yönetmeliğine uygun
- ✅ AKTS (Avrupa Kredi Transfer Sistemi) ile uyumlu
- ✅ YÖK (Yükseköğretim Kurulu) standartlarına uygun
- ✅ Bologna sürecine uyumlu

---

## 📚 KAYNAKLAR

- Selçuk Üniversitesi Lisans Eğitim-Öğretim ve Sınav Yönetmeliği
- AKTS Kullanım Kılavuzu
- YÖK Kredi ve Not Sistemi Yönergesi

---

*Bu döküman Selçuk Üniversitesi'nin resmi not yönetmeliğine göre hazırlanmıştır.*  
*Son güncelleme: 14 Aralık 2025*
