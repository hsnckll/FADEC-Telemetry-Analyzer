"""
ai.py
FADEC Telemetri ve Kök Neden Analiz Prompt Motoru & Arayüz Penceresi
"""
import numpy as np
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets

class AIPromptBuilder:
    """
    Telemetri verilerinden sayısal anomali istatistiklerini çıkarıp
    Markdown formatında teşhis promptu derleyen motor sınıfı.
    """
    def __init__(self, df_data=None, hata_kategorileri=None, limitler=None, oturum_adi=""):
        self.df = df_data if df_data is not None else pd.DataFrame()
        self.hata_kategorileri = hata_kategorileri or []
        self.limitler = limitler or {}
        self.oturum_adi = oturum_adi or "Aktif_Test_Oturumu"

    def hata_bloklarini_tara(self):
        """
        Her bir hata kategorisindeki (0 -> 1) ve (1 -> 0) geçişlerini
        NumPy türeviyle tarar; gerçek zaman damgaları arasındaki farkı alarak
        süreyi (saniye) TAMAMEN DİNAMİK hesaplar.
        """
        hata_ozetleri = {}
        if self.df.empty or not self.hata_kategorileri:
            return hata_ozetleri

        # 1. Zaman kolonunu tespit et
        zaman_kolonu = None
        for col in ['Zaman_Gercek', 'Time', 'zaman', 'time', 'Zaman_Gorsel']:
            if col in self.df.columns:
                zaman_kolonu = col
                break

        # 2. Her hata kategorisini tara
        for hk in self.hata_kategorileri:
            if hk not in self.df.columns:
                continue

            arr = self.df[hk].fillna(0).values.astype(int)
            diff = np.diff(np.pad(arr, (1, 1), 'constant'))
            starts = np.where(diff == 1)[0]
            ends = np.where(diff == -1)[0] - 1

            bloklar = []
            for idx, (s, e) in enumerate(zip(starts, ends)):
                if s >= len(self.df) or e >= len(self.df):
                    continue

                t_start = str(self.df[zaman_kolonu].iloc[s]) if zaman_kolonu else f"İndeks {s}"
                t_end = str(self.df[zaman_kolonu].iloc[e]) if zaman_kolonu else f"İndeks {e}"
                nokta_sayisi = int(e - s + 1)

                # --- DİNAMİK SÜRE HESABI ---
                # Gerçek saat damgalarını datetime nesnesine çevirip farkını saniyeye döker
                try:
                    dt_baslangic = pd.to_datetime(t_start)
                    dt_bitis = pd.to_datetime(t_end)
                    sure_sn = round(abs((dt_bitis - dt_baslangic).total_seconds()), 2)

                    # Eğer aynı satırsa (0 sn çıkarsa) en az 1 örnekleme süresi ata
                    if sure_sn == 0 and len(self.df) > 1 and zaman_kolonu:
                        dt_ornekleme = abs((pd.to_datetime(self.df[zaman_kolonu].iloc[1]) - pd.to_datetime(
                            self.df[zaman_kolonu].iloc[0])).total_seconds())
                        sure_sn = round(nokta_sayisi * dt_ornekleme, 2)
                except Exception:
                    # Zaman kolonu tarih formatında değilse satır sayısını temel al
                    sure_sn = float(nokta_sayisi)

                bloklar.append({
                    'blok_no': idx + 1,
                    'start_idx': int(s),
                    'end_idx': int(e),
                    'start_time': t_start,
                    'end_time': t_end,
                    'nokta_sayisi': nokta_sayisi,
                    'sure_sn': sure_sn
                })

            hata_ozetleri[hk] = bloklar

        return hata_ozetleri


    def capraz_cakismalari_bul(self, hata_ozetleri):
        """
        Zaman çizelgesinde eşzamanlı çakışan veya birbirini takip eden
        arıza bloklarını bulur ve GERÇEK ÇAKIŞMA SÜRESİNE (kritikliğe) göre sıralar.
        """
        cakismalar = []
        tum_blok_listesi = []

        # 1. Tüm kategorilerdeki blokları tek bir listeye topla
        for hk, bloklar in hata_ozetleri.items():
            for b in bloklar:
                tum_blok_listesi.append({
                    'kategori': hk,
                    'blok_no': b['blok_no'],
                    'start_idx': b['start_idx'],
                    'end_idx': b['end_idx'],
                    'start_time': b['start_time'],
                    'end_time': b['end_time'],
                    'sure_sn': b.get('sure_sn', 0)
                })

        # 2. Zaman sırasına göre diz
        tum_blok_listesi.sort(key=lambda x: x['start_idx'])

        # 3. Çakışmaları ve çakışma sürelerini tespit et
        for i in range(len(tum_blok_listesi)):
            for j in range(i + 1, min(i + 8, len(tum_blok_listesi))):
                b1 = tum_blok_listesi[i]
                b2 = tum_blok_listesi[j]

                if b1['kategori'] == b2['kategori']:
                    continue

                # --- 1. EŞZAMANLI ÇAKIŞMA ---
                if b2['start_idx'] <= b1['end_idx']:
                    # Ortak devam ettikleri aralık
                    ortak_bitis_idx = min(b1['end_idx'], b2['end_idx'])
                    ortak_nokta = max(0, ortak_bitis_idx - b2['start_idx'] + 1)

                    try:
                        dt_b2_start = pd.to_datetime(b2['start_time'])
                        # Ortak süreyi dinamik hesapla
                        dt1_start = pd.to_datetime(b1['start_time'])
                        fark_sn = round(abs((dt_b2_start - dt1_start).total_seconds()), 2)
                        ortak_sure_sn = round(ortak_nokta * 0.1, 1) if '0.1' else round(
                            ortak_nokta * (b1['sure_sn'] / max(1, (b1['end_idx'] - b1['start_idx']))), 1)
                    except Exception:
                        fark_sn = 0.0
                        ortak_sure_sn = 0.0

                    cakismalar.append({
                        'oncelik': ortak_nokta,  # Çakışma süresi ne kadar uzunsa o kadar kritik
                        'metin': f"⚠️ **Eşzamanlı Çakışma ({ortak_sure_sn} sn ortak sürdü):** `{b1['kategori']}` devam ederken {fark_sn} sn sonra `{b2['kategori']}` tetiklenmiştir ({b2['start_time']} - {b1['end_time']})."
                    })

                # --- 2. ZİNCİRLEME TETİKLENME (30 sn içinde peş peşe) ---
                elif 0 < (b2['start_idx'] - b1['end_idx']) <= 500:
                    try:
                        dt1_bitis = pd.to_datetime(b1['end_time'])
                        dt2_baslangic = pd.to_datetime(b2['start_time'])
                        ara_sn = round(abs((dt2_baslangic - dt1_bitis).total_seconds()), 2)
                    except Exception:
                        ara_sn = 999.0

                    if ara_sn <= 30.0:
                        cakismalar.append({
                            'oncelik': 100 - ara_sn,  # Birbirine ne kadar yakın tetiklendiyse o kadar kritik
                            'metin': f"🔗 **Zincirleme Tetiklenme:** `{b1['kategori']}` bittikten {ara_sn} sn sonra `{b2['kategori']}` başlamıştır."
                        })

        # Gerçek kritiklik derecesine (çakışma şiddetine) göre büyükten küçüğe sırala
        cakismalar.sort(key=lambda x: x['oncelik'], reverse=True)

        # Sadece metinleri liste olarak döndür
        return [c['metin'] for c in cakismalar]

    def sensor_istatistiklerini_cikar(self, hata_ozetleri):
        """
        Tüm sensörlerin motorun sağlıklı dönemindeki (arıza yokken) ortalamaları ile
        test boyunca ulaştıkları Min, Max değerlerini karşılaştırır;
        sapma yüzdelerini (% Delta) ve kullanıcı limit aşımlarını hesaplar.
        """
        sensor_raporlari = []
        if self.df.empty:
            return sensor_raporlari

        # 1. Zaman, Motor No gibi üst verileri hariç tut, sadece sayısal sensörleri al
        haric_kolonlar = set(self.hata_kategorileri + [
            'Time', 'time', 'zaman', 'Zaman_Gercek', 'Zaman_Gorsel', 'Zaman_Index',
            'Motor_No', 'Ayar_1', 'Ayar_2', 'Ayar_3'
        ])
        sensor_kolonlari = [
            c for c in self.df.columns
            if c not in haric_kolonlar and np.issubdtype(self.df[c].dtype, np.number)
        ]

        # 2. Sağlıklı anlar maskesi oluştur (Tüm hata kolonlarının 0 olduğu satırlar)
        if self.hata_kategorileri:
            saglikli_mask = (self.df[self.hata_kategorileri] == 0).all(axis=1)
        else:
            saglikli_mask = pd.Series(True, index=self.df.index)

        df_saglikli = self.df[saglikli_mask]

        # 3. Her bir sensörü matematiksel olarak incele
        for col in sensor_kolonlari:
            # Sağlıklı referans ortalaması
            nominal_mean = df_saglikli[col].mean() if not df_saglikli.empty else self.df[col].mean()
            tum_max = self.df[col].max()
            tum_min = self.df[col].min()

            # Maksimum ve minimum sapma yüzdeleri (% Delta Hesabı)
            if nominal_mean != 0 and not np.isnan(nominal_mean):
                max_sapma_yuzde = round(((tum_max - nominal_mean) / abs(nominal_mean)) * 100, 1)
                min_sapma_yuzde = round(((tum_min - nominal_mean) / abs(nominal_mean)) * 100, 1)
            else:
                max_sapma_yuzde = 0.0
                min_sapma_yuzde = 0.0

            # 4. Kullanıcının belirlediği güvenlik limitleri aşılmış mı?
            limit_ihlal_bilgisi = "Normal Aralıkta"
            if col in self.limitler:
                # Limitler (min, max) şeklinde bir Tuple olarak geliyor
                alt = self.limitler[col][0]
                ust = self.limitler[col][1]

                if ust is not None and tum_max > ust:
                    limit_ihlal_bilgisi = f"🚨 ÜST LİMİT AŞIMI (Limit: {ust}, Ölçülen: {tum_max:.2f})"
                elif alt is not None and tum_min < alt:
                    limit_ihlal_bilgisi = f"🚨 ALT LİMİT AŞIMI (Limit: {alt}, Ölçülen: {tum_min:.2f})"

            sensor_raporlari.append({
                'sensor': col,
                'nominal_ort': round(nominal_mean, 2) if not np.isnan(nominal_mean) else 0.0,
                'min_deger': round(tum_min, 2) if not np.isnan(tum_min) else 0.0,
                'max_deger': round(tum_max, 2) if not np.isnan(tum_max) else 0.0,
                'max_sapma_yuzde': max_sapma_yuzde,
                'min_sapma_yuzde': min_sapma_yuzde,
                'limit_durumu': limit_ihlal_bilgisi
            })

        return sensor_raporlari


    def prompt_derle(self):
        """
        Tüm alt analizleri (Hata Blokları, Çapraz Çakışmalar, Sensör Sapmaları)
        birleştirerek Kıdemli Havacılık Test Mühendisi formatında
        eksiksiz bir Markdown Teşhis Promptu üretir.
        """
        if self.df.empty:
            return "⚠️ Analiz edilecek veri seti bulunamadı. Lütfen önce bir CSV oturumu yükleyiniz."

        # 1. Önceki yazdığımız alt motorları sırayla çalıştır
        hata_ozetleri = self.hata_bloklarini_tara()
        cakismalar = self.capraz_cakismalari_bul(hata_ozetleri)
        sensor_raporlari = self.sensor_istatistiklerini_cikar(hata_ozetleri)

        # 2. Genel oturum metriklerini hesapla
        toplam_satir = len(self.df)
        toplam_blok_sayisi = sum(len(bloklar) for bloklar in hata_ozetleri.values())
        kategori_sayisi = len(self.hata_kategorileri)

        # Toplam oturum süresini dinamik hesapla
        zaman_kolonu = None
        for col in ['Zaman_Gercek', 'Time', 'zaman', 'time', 'Zaman_Gorsel']:
            if col in self.df.columns:
                zaman_kolonu = col
                break

        toplam_sure_str = f"{round(toplam_satir * 0.1 / 60, 1)} dakika"
        if zaman_kolonu and toplam_satir > 1:
            try:
                t0 = pd.to_datetime(self.df[zaman_kolonu].iloc[0])
                t1 = pd.to_datetime(self.df[zaman_kolonu].iloc[-1])
                toplam_dakika = round(abs((t1 - t0).total_seconds()) / 60.0, 1)
                toplam_sure_str = f"{toplam_dakika} dakika ({t0.strftime('%H:%M:%S')} - {t1.strftime('%H:%M:%S')})"
            except Exception:
                pass

        # 3. Metin inşası (Markdown Şablonu)
        metin = []

        # BÖLÜM 1: Rol ve Görev Tanımı
        metin.append("# GÖREV TANIMI VE ROL:")
        metin.append(
            "Sen Kıdemli bir Havacılık Gaz Türbinli Motor, FADEC (Full Authority Digital Engine Control) "
            "ve Uçuş Test Teşhis Başmühendisisin.\n"
            "Aşağıda yer/uçuş test oturumu boyunca telemetri kayıtlarından otomatik olarak çıkarılmış "
            "çok boyutlu anomali blokları, korelasyonlar ve sensör sapma verileri yer almaktadır.\n"
        )
        metin.append("---")

        # BÖLÜM 2: Test Oturumu Genel Özeti
        metin.append("## 1. TEST OTURUMU GENEL METRİKLERİ")
        metin.append(f"* **Oturum / Veri Seti:** `{self.oturum_adi}`")
        metin.append(f"* **Toplam Telemetri Veri Noktası:** {toplam_satir:,} satır (~{toplam_sure_str})")
        metin.append(f"* **İncelenen Hata Kategorisi Sayısı:** {kategori_sayisi} Farklı Hata Kolonu")
        metin.append(f"* **Tespit Edilen Toplam Anomali Olayı:** {toplam_blok_sayisi} Arıza Bloğu\n")
        metin.append("---")

        # BÖLÜM 3: Tüm Hata Kategorileri ve Olay Dağılımı
        metin.append("## 2. TÜM HATA KATEGORİLERİ VE ANOMALİ BLOKLARI")
        for hk, bloklar in hata_ozetleri.items():
            metin.append(f"### 📍 Kategori: `{hk}` ({len(bloklar)} Blok Tespit Edildi)")
            if not bloklar:
                metin.append("  * Bu kategoride herhangi bir anomali tetiklenmemiştir (Nominal).")
            else:
                # İlk 3 bloğu detaylandır, 3'ten fazlaysa özetle
                gosterilecek_bloklar = bloklar[:3]
                for b in gosterilecek_bloklar:
                    metin.append(
                        f"  * **Blok {b['blok_no']}:** {b['start_time']} ➔ {b['end_time']} "
                        f"(Süre: {b['sure_sn']} sn | {b['nokta_sayisi']} Veri Noktası)"
                    )
                if len(bloklar) > 3:
                    metin.append(f"  * *(... ve toplam {len(bloklar)} blok boyunca periyodik olarak devam etti)*")
            metin.append("")
        metin.append("---")

        # BÖLÜM 4: Çapraz Çakışma ve Zincirleme Etkiler
        metin.append("## 3. KRİTİK ZİNCİRLEME VE EŞZAMANLI ARIZA SENARYOLARI (CASCADING FAULTS)")
        if cakismalar:
            for c in cakismalar:
                metin.append(f"* {c}")
        else:
            metin.append("* Farklı hata kategorileri arasında doğrudan eşzamanlı çakışma tespit edilmemiştir.")
        metin.append("\n---")

        # BÖLÜM 5: Sensör Sapmaları Tablosu
        metin.append("## 4. KRİTİK SENSÖR KANALLARI VE SAPMA MATRİSİ")
        metin.append("| Sensör Adı | Nominal Ort | Min Değer | Max Değer | Max Sapma (%) | Limit Durumu |")
        metin.append("| :--- | :---: | :---: | :---: | :---: | :--- |")
        for s in sensor_raporlari:
            sapma_isaret = f"+%{s['max_sapma_yuzde']}" if s['max_sapma_yuzde'] > 0 else f"%{s['max_sapma_yuzde']}"
            metin.append(
                f"| `{s['sensor']}` | {s['nominal_ort']} | {s['min_deger']} | {s['max_deger']} | {sapma_isaret} | {s['limit_durumu']} |"
            )
        metin.append("\n---")

        # BÖLÜM 6: AI'dan İstenen Mühendislik Raporu Formatı
        metin.append("## 5. İSTENEN MÜHENDİSLİK ANALİZ RAPORU FORMATI")
        metin.append("Lütfen yukarıdaki telemetri korelasyonlarını ve anomali bloklarını inceleyerek aşağıdaki 4 ana başlık altında resmi bir teşhis raporu hazırla:\n")
        metin.append("1. **KÖK NEDEN VE ARIZA HİYERARŞİSİ:** Meydana gelen bu farklı hata türleri arasında ilk tetikleyici (Root-Cause) hangisidir? Hangi hatalar diğerlerinin zincirleme sonucudur?")
        metin.append("2. **BİLEŞEN BAZLI SAĞLIK DEĞERLENDİRMESİ:** Kompresör (HPC/LPC), Yanma Odası, Türbin ve FADEC/Yakıt Kontrol sistemlerinin aşınma veya arıza risk seviyeleri nedir?")
        metin.append("3. **MOTOR VE UÇUŞ GÜVENLİĞİ RİSK SEVİYESİ:** Bu anomali örüntüsü motorun havada durması (Flameout), kompresör perdövitesi (Surge/Stall) veya aşırı ısınma açısından ne derece kritiktir?")
        metin.append("4. **ÖNERİLEN BAKIM VE İNCELEME EYLEM PLANI:** TEI test ve bakım mühendislerinin hangarda / test hücresinde sırasıyla uygulaması gereken fiziksel kontrol, boroskop incelemesi ve sensör kalibrasyon adımları nelerdir?")

        return "\n".join(metin)