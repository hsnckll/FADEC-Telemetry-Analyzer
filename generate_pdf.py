# -*- coding: utf-8 -*-
"""
================================================================================
FADEC VERİ ANALİZİ VE OTOMATİK PDF RAPOR ÜRETİM MOTORU
================================================================================
@file    generate_pdf.py
@brief   CSV telemetri verilerinden otomatik istatistiksel analiz, anomali 
         korelasyonu, Z-Skoru kök neden sıralaması ve A4 kurumsal PDF test 
         raporu üreten motor.
@author  FADEC Test & Diagnostic Engine
@date    2026-08-30
================================================================================
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtPrintSupport


class PDFRaporMotoru:
    """
    @brief Telemetri verilerini analiz ederek kurumsal PDF raporu üreten ana sınıf.
    """

    def __init__(self, df, hata_kategorileri=None, limitler=None, oturum_adi="Aktif Test Oturumu"):
        """
        @param df (pd.DataFrame) Ham veya birleştirilmiş telemetri verisi.
        @param hata_kategorileri (list) Hata/anomali durumu kolon isimleri listesi.
        @param limitler (dict) Sensör sınır limitleri { 'Sensor_Adi': (min, max) }.
        @param oturum_adi (str) Raporlanacak test oturumunun başlık ismi.
        """
        self.df = df
        self.hata_kategorileri = hata_kategorileri if hata_kategorileri else []
        self.limitler = limitler if limitler else {}
        self.oturum_adi = oturum_adi

        # Analiz sonuçları
        self.metrikler = {}
        self.kategori_raporlari = []
        self.sensor_raporlari = []
        self.en_uzun_blok = {}
        self.cakismalar = []

    def analiz_yap(self):
        """
        @brief Tüm telemetri verisini baştan sona matematiksel olarak analiz eder.
        """
        if self.df is None or self.df.empty:
            raise ValueError("Analiz edilecek veri seti boş!")

        total_satir = len(self.df)

        # 1. Örnekleme Aralığı (dt) ve Zamanlama Tespiti
        dt_saniye = 0.1
        baslangic_zaman_str = "-"
        bitis_zaman_str = "-"

        if "Zaman_Gorsel" in self.df.columns and total_satir >= 2:
            try:
                t0 = pd.to_datetime(str(self.df.iloc[0]["Zaman_Gorsel"]))
                t1 = pd.to_datetime(str(self.df.iloc[1]["Zaman_Gorsel"]))
                fark = (t1 - t0).total_seconds()
                if fark > 0:
                    dt_saniye = fark
                baslangic_zaman_str = str(self.df.iloc[0]["Zaman_Gorsel"])
                bitis_zaman_str = str(self.df.iloc[-1]["Zaman_Gorsel"])
            except Exception:
                pass

        toplam_sure_sn = total_satir * dt_saniye

        # 2. Sağlıklı vs Hatalı Durum Maskesi
        gecerli_hata_kolonlari = [c for c in self.hata_kategorileri if c in self.df.columns]
        
        if gecerli_hata_kolonlari:
            hata_maskesi = (self.df[gecerli_hata_kolonlari] == 1).any(axis=1)
            arizali_satir = int(hata_maskesi.sum())
        else:
            hata_maskesi = pd.Series(False, index=self.df.index)
            arizali_satir = 0

        saglikli_satir = total_satir - arizali_satir
        saglikli_yuzde = (saglikli_satir / total_satir * 100.0) if total_satir > 0 else 100.0
        arizali_yuzde = 100.0 - saglikli_yuzde
        saglikli_sure_sn = saglikli_satir * dt_saniye
        arizali_sure_sn = arizali_satir * dt_saniye

        # 3. Hata Kategorileri ve Blok Analizi
        toplam_anomali_olayi = 0
        tum_bloklar = []

        for kat in gecerli_hata_kolonlari:
            dizi = (self.df[kat] == 1).to_numpy(dtype=bool)
            farklar = np.diff(np.pad(dizi.astype(np.int8), (1, 1), 'constant'))
            baslangiclar = np.where(farklar == 1)[0]
            bitisler = np.where(farklar == -1)[0]

            kat_blok_sayisi = len(baslangiclar)
            toplam_anomali_olayi += kat_blok_sayisi
            kat_toplam_satir = int(dizi.sum())
            kat_toplam_sure_sn = kat_toplam_satir * dt_saniye
            kat_oran = (kat_toplam_satir / total_satir * 100.0) if total_satir > 0 else 0.0

            kat_en_uzun_sure = 0.0
            kat_en_uzun_zaman = "-"

            for b_idx, e_idx in zip(baslangiclar, bitisler):
                b_satir = e_idx - b_idx
                b_sure = b_satir * dt_saniye
                
                t_bas = str(self.df.iat[b_idx, self.df.columns.get_loc("Zaman_Gorsel")]) if "Zaman_Gorsel" in self.df.columns else str(b_idx)
                t_bit = str(self.df.iat[e_idx - 1, self.df.columns.get_loc("Zaman_Gorsel")]) if "Zaman_Gorsel" in self.df.columns else str(e_idx)

                blok_bilgisi = {
                    'kategori': kat,
                    'start_idx': b_idx,
                    'end_idx': e_idx,
                    'sure_sn': b_sure,
                    'start_time': t_bas,
                    'end_time': t_bit
                }
                tum_bloklar.append(blok_bilgisi)

                if b_sure > kat_en_uzun_sure:
                    kat_en_uzun_sure = b_sure
                    kat_en_uzun_zaman = f"{t_bas} ➔ {t_bit}"

            self.kategori_raporlari.append({
                'kategori': kat,
                'blok_sayisi': kat_blok_sayisi,
                'toplam_sure_sn': kat_toplam_sure_sn,
                'oran_yuzde': kat_oran,
                'en_uzun_sure_sn': kat_en_uzun_sure,
                'en_uzun_zaman': kat_en_uzun_zaman
            })

        # En Uzun Global Kriz Bloğunu Belirle
        if tum_bloklar:
            tum_bloklar.sort(key=lambda x: x['sure_sn'], reverse=True)
            self.en_uzun_blok = tum_bloklar[0]
        else:
            self.en_uzun_blok = {
                'kategori': '-',
                'sure_sn': 0.0,
                'start_time': '-',
                'end_time': '-',
                'start_idx': 0,
                'end_idx': 0
            }

        # 4. Çakışan (Kaskad / Zincirleme) Hataların Analizi
        if len(gecerli_hata_kolonlari) >= 2:
            cakisma_matrisi = (self.df[gecerli_hata_kolonlari] == 1).astype(int)
            aktif_hata_sayisi = cakisma_matrisi.sum(axis=1)
            cakisma_satir_sayisi = int((aktif_hata_sayisi >= 2).sum())
            cakisma_sure_sn = cakisma_satir_sayisi * dt_saniye
        else:
            cakisma_satir_sayisi = 0
            cakisma_sure_sn = 0.0

        # 5. Sensör İstatistikleri ve Z-Skoru Kök Neden Sıralaması
        haric_kolonlar = set(self.hata_kategorileri + [
            'Time', 'time', 'zaman', 'Zaman_Gercek', 'Zaman_Gorsel', 'Zaman_Index',
            'Motor_No', 'Ayar_1', 'Ayar_2', 'Ayar_3'
        ])

        if self.limitler:
            sensor_kolonlari = [c for c in self.limitler.keys() if c in self.df.columns]
        else:
            sensor_kolonlari = [
                c for c in self.df.columns
                if c not in haric_kolonlar and np.issubdtype(self.df[c].dtype, np.number)
            ]

        # Sağlıklı ve Arızalı Veri Parçaları
        df_saglikli = self.df[~hata_maskesi] if arizali_satir > 0 else self.df
        df_arizali = self.df[hata_maskesi] if arizali_satir > 0 else self.df



        for col in sensor_kolonlari: #Burada bütün kolonları tek tek geziyor. Ondan dolayı kolon karışmıyor
            y_tum = self.df[col].to_numpy(dtype=np.float64, copy=False)
            tum_min = float(np.nanmin(y_tum))
            tum_max = float(np.nanmax(y_tum))
            tum_mean = float(np.nanmean(y_tum))

            # Sağlıklı Referans Değerleri
            if not df_saglikli.empty and col in df_saglikli.columns:
                y_saglikli = df_saglikli[col].to_numpy(dtype=np.float64, copy=False)
                saglikli_mean = float(np.nanmean(y_saglikli))
                saglikli_std = float(np.nanstd(y_saglikli))
            else:
                saglikli_mean = tum_mean
                saglikli_std = float(np.nanstd(y_tum))

            if saglikli_std == 0 or np.isnan(saglikli_std):
                saglikli_std = 1e-6

            # KULLANICI MANTIĞI: Her bir hata bloğu için Radar Z-Skorunu hesapla ve ortalamasını al
            block_z_skorlari = []
            if tum_bloklar:
                for b in tum_bloklar:
                    b_start = b['start_idx']
                    b_end = b['end_idx']
                    if b_end > b_start:
                        b_dilim = y_tum[b_start:b_end] # O zaman dilimini al
                        b_mean = float(np.nanmean(b_dilim))
                        # Radar Z-Skoru formülü: |Kriz_Ortalaması - Normal_Ortalama| / Normal_Std
                        b_z = abs(b_mean - saglikli_mean) / saglikli_std
                        block_z_skorlari.append(b_z)

            if block_z_skorlari:
                z_score = float(np.mean(block_z_skorlari))
                peak_block_z = float(np.max(block_z_skorlari))
            else:
                z_score = 0.0
                peak_block_z = 0.0

            # Maksimum anlık sapma yüzdesi
            fark_max = abs(tum_max - saglikli_mean)
            fark_min = abs(tum_min - saglikli_mean)
            max_sapma_birim = max(fark_max, fark_min)
            max_sapma_yuzde = (max_sapma_birim / abs(saglikli_mean) * 100.0) if saglikli_mean != 0 else 0.0

            # Limit Kontrolü
            limit_durumu = "Normal"
            limit_ihlal_var = False
            if col in self.limitler and len(self.limitler[col]) >= 2:
                alt = self.limitler[col][0]
                ust = self.limitler[col][1]
                if ust is not None and tum_max > ust:
                    limit_durumu = f"Üst Limit Aşımı (+{tum_max - ust:.2f})"
                    limit_ihlal_var = True
                elif alt is not None and tum_min < alt:
                    limit_durumu = f"Alt Limit Aşımı (-{alt - tum_min:.2f})"
                    limit_ihlal_var = True

            # Teşhis Sınıflandırması (Radar Blok Z-Skoruna Göre)
            if limit_ihlal_var and z_score >= 0.5:
                teshis = "KÖK NEDEN ŞÜPHELİSİ"
                seviye = "Kritik"
            elif limit_ihlal_var or z_score >= 0.5:
                teshis = "YÜKSEK SAPMA (SEMPTOM)"
                seviye = "Orta"
            elif z_score >= 0.2:
                teshis = "ORTA DERECELİ ETKİ"
                seviye = "Orta"
            else:
                teshis = "NORMAL / DÜŞÜK ETKİ"
                seviye = "Düşük"

            self.sensor_raporlari.append({
                'sensor': col,
                'nominal_mean': saglikli_mean,
                'tum_min': tum_min,
                'tum_max': tum_max,
                'z_score': z_score,
                'peak_block_z': peak_block_z,
                'max_sapma_yuzde': max_sapma_yuzde,
                'limit_durumu': limit_durumu,
                'limit_ihlal_var': limit_ihlal_var,
                'teshis': teshis,
                'seviye': seviye
            })

        # Sensörleri Z-Skoru ve Limit İhlaline Göre Sırala (En şüpheliden aza doğru)
        self.sensor_raporlari.sort(key=lambda x: (x['limit_ihlal_var'], x['z_score']), reverse=True)

        # En Uzun Kriz Bloğunda En Çok Sapan Sensörü Bul
        en_cok_sapan_kriz_sensoru = "-"
        if self.en_uzun_blok.get('end_idx', 0) > self.en_uzun_blok.get('start_idx', 0):
            b_start = self.en_uzun_blok['start_idx']
            b_end = self.en_uzun_blok['end_idx']
            df_kriz = self.df.iloc[b_start:b_end]

            en_buyuk_kriz_sapma = -1.0
            for col in sensor_kolonlari:
                if col in df_kriz.columns:
                    k_mean = df_kriz[col].mean()
                    # Bu sensörün sağlıklı ortalaması
                    s_ref = next((s['nominal_mean'] for s in self.sensor_raporlari if s['sensor'] == col), k_mean)
                    if s_ref != 0:
                        sapma = abs(k_mean - s_ref) / abs(s_ref) * 100.0
                        if sapma > en_buyuk_kriz_sapma:
                            en_buyuk_kriz_sapma = sapma
                            en_cok_sapan_kriz_sensoru = f"{col} (+%{sapma:.1f} Sapma)"

        # Genel Metrikler Özeti (Süre formatlama Türkçeleştirildi)
        toplam_sn_int = int(toplam_sure_sn)
        td_gun = toplam_sn_int // 86400
        td_kalan = toplam_sn_int % 86400
        td_saat = td_kalan // 3600
        td_kalan2 = td_kalan % 3600
        td_dakika = td_kalan2 // 60
        td_saniye = td_kalan2 % 60
        
        if td_gun > 0:
            toplam_sure_str = f"{td_gun} Gün, {td_saat:02d}:{td_dakika:02d}:{td_saniye:02d}"
        elif td_saat > 0:
            toplam_sure_str = f"{td_saat:02d}:{td_dakika:02d}:{td_saniye:02d}"
        else:
            toplam_sure_str = f"{td_dakika:02d}:{td_saniye:02d}"

        self.metrikler = {
            'toplam_satir': total_satir,
            'toplam_sure_sn': toplam_sure_sn,
            'toplam_sure_str': toplam_sure_str,
            'dt_hz': round(1.0 / dt_saniye, 1) if dt_saniye > 0 else 10.0,
            'baslangic_zamani': baslangic_zaman_str,
            'bitis_zamani': bitis_zaman_str,
            'saglikli_yuzde': saglikli_yuzde,
            'arizali_yuzde': arizali_yuzde,
            'saglikli_sure_sn': saglikli_sure_sn,
            'arizali_sure_sn': arizali_sure_sn,
            'toplam_anomali_olayi': toplam_anomali_olayi,
            'cakisma_olay_sayisi': cakisma_satir_sayisi,
            'cakisma_sure_sn': cakisma_sure_sn,
            'bas_supheli_sensor': self.sensor_raporlari[0]['sensor'] if self.sensor_raporlari else "-",
            'kriz_en_cok_sapan_sensor': en_cok_sapan_kriz_sensoru
        }

    def html_sablonu_olustur(self):
        """
        @brief Hesaplanan istatistikleri modern, kurumsal bir HTML A4 raporuna dönüştürür.
        @return (str) HTML formatında rapor metni.
        """
        rapor_tarihi = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

        # Top 5 Sensör Satırları
        top5_sensorler = self.sensor_raporlari[:5]
        top5_satirlar_html = ""
        for i, s in enumerate(top5_sensorler, start=1):
            limit_badge = f"<span class='badge-limit-danger'>{s['limit_durumu']}</span>" if s['limit_ihlal_var'] else "<span class='badge-limit-ok'>Normal</span>"
            
            top5_satirlar_html += f"""
            <tr>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center; font-weight: bold;'>{i}</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'><b>{s['sensor']}</b></td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'>{s['nominal_mean']:.2f}</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'>{s['tum_max']:.2f}</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'>{limit_badge}</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center; font-weight: bold; color: #0284c7;'>{s['z_score']:.2f} σ</td>
            </tr>
            """

        # Hata Kategorileri Satırları
        kat_satirlar_html = ""
        for kat in self.kategori_raporlari:
            kat_satirlar_html += f"""
            <tr>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px;'><b>{kat['kategori']}</b></td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'>{kat['blok_sayisi']} Olay</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'>{kat['toplam_sure_sn']:.1f} sn</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center; font-weight: bold; color: #dc2626;'>%{kat['oran_yuzde']:.3f}</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;'>{kat['en_uzun_sure_sn']:.1f} sn</td>
                <td style='border: 1px solid #cbd5e1; padding: 4px 6px; font-size: 8pt; color: #475569; text-align: center;'>{kat['en_uzun_zaman']}</td>
            </tr>
            """

        # Sağlık Durumu Rengi
        saglik_renk = "#16a34a" if self.metrikler['saglikli_yuzde'] >= 90 else ("#eab308" if self.metrikler['saglikli_yuzde'] >= 75 else "#dc2626")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{
                    size: A4;
                    margin: 0;
                }}
                body {{
                    font-family: 'Segoe UI', Arial, Helvetica, sans-serif;
                    color: #0f172a;
                    margin: 0;
                    padding: 0;
                    font-size: 9.5pt;
                    line-height: 1.35;
                }}
                .header-table {{
                    width: 100%;
                    border-bottom: 2px solid #0284c7;
                    padding-bottom: 6px;
                    margin-bottom: 10px;
                }}
                .header-title {{
                    font-size: 15pt;
                    font-weight: bold;
                    color: #0369a1;
                    margin: 0;
                }}
                .header-subtitle {{
                    font-size: 8.5pt;
                    color: #64748b;
                    margin-top: 2px;
                }}
                .kpi-container {{
                    width: 100%;
                    margin-bottom: 10px;
                }}
                .kpi-box {{
                    background-color: #f8fafc;
                    border: 1px solid #cbd5e1;
                    border-radius: 5px;
                    padding: 7px 8px;
                    text-align: center;
                }}
                .kpi-value {{
                    font-size: 12.5pt;
                    font-weight: bold;
                    color: #0f172a;
                }}
                .kpi-label {{
                    font-size: 7.5pt;
                    color: #64748b;
                    text-transform: uppercase;
                    font-weight: bold;
                    margin-top: 2px;
                }}
                .section-title {{
                    font-size: 9.5pt;
                    font-weight: bold;
                    color: #0369a1;
                    border-left: 3.5px solid #0284c7;
                    padding-left: 6px;
                    margin-top: 9px;
                    margin-bottom: 4px;
                }}
                table.data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 8px;
                    font-size: 8.2pt;
                    border: 1px solid #cbd5e1;
                }}
                table.data-table th {{
                    background-color: #f1f5f9;
                    color: #334155;
                    font-weight: bold;
                    text-align: left;
                    padding: 4.5px 6px;
                    border: 1px solid #cbd5e1;
                }}
                table.data-table td {{
                    padding: 4px 6px;
                    border: 1px solid #cbd5e1;
                }}
                table.data-table tr:nth-child(even) {{
                    background-color: #f8fafc;
                }}
                .badge-danger {{
                    background-color: #fee2e2;
                    color: #991b1b;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 7pt;
                }}
                .badge-warning {{
                    background-color: #fef3c7;
                    color: #92400e;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 7pt;
                }}
                .badge-success {{
                    background-color: #dcfce7;
                    color: #166534;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-weight: bold;
                    font-size: 7pt;
                }}
                .badge-limit-danger {{
                    color: #dc2626;
                    font-weight: bold;
                }}
                .badge-limit-ok {{
                    color: #16a34a;
                }}
                .callout {{
                    background-color: #f0f9ff;
                    border-left: 3.5px solid #0284c7;
                    border-top: 1px solid #bae6fd;
                    border-right: 1px solid #bae6fd;
                    border-bottom: 1px solid #bae6fd;
                    border-radius: 4px;
                    padding: 6px 9px;
                    margin-bottom: 8px;
                    font-size: 8.2pt;
                    line-height: 1.32;
                }}
                .footer {{
                    margin-top: 10px;
                    border-top: 1px solid #cbd5e1;
                    padding-top: 4px;
                    font-size: 7pt;
                    color: #94a3b8;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <!-- Üst Başlık -->
            <table class="header-table">
                <tr>
                    <td>
                        <div class="header-title">FADEC UÇUŞ TEST RAPORU</div>
                        <div class="header-subtitle">Otomatik Uçuş Verileri Analizi ve Değerlendirilmesi</div>
                    </td>
                    <td style="text-align: right; vertical-align: bottom; font-size: 8pt; color: #64748b;">
                        <b>Rapor Tarihi:</b> {rapor_tarihi}<br>
                        <b>Oturum:</b> {self.oturum_adi}
                    </td>
                </tr>
            </table>

            <!-- 1. Yönetici Özeti (KPI Kutucukları) -->
            <table class="kpi-container" cellspacing="5">
                <tr>
                    <td class="kpi-box" style="width: 25%;">
                        <div class="kpi-value" style="color: {saglik_renk};">%{self.metrikler['saglikli_yuzde']:.1f}</div>
                        <div class="kpi-label">Sağlık Skoru</div>
                    </td>
                    <td class="kpi-box" style="width: 25%;">
                        <div class="kpi-value">{self.metrikler['toplam_sure_str']}</div>
                        <div class="kpi-label">Toplam Test Süresi</div>
                    </td>
                    <td class="kpi-box" style="width: 25%;">
                        <div class="kpi-value" style="color: #dc2626;">{self.metrikler['toplam_anomali_olayi']} Olay</div>
                        <div class="kpi-label">Toplam Anomali</div>
                    </td>
                    <td class="kpi-box" style="width: 25%;">
                        <div class="kpi-value" style="color: #0284c7;">{self.metrikler['bas_supheli_sensor']}</div>
                        <div class="kpi-label">Şüpheli Sensör</div>
                    </td>
                </tr>
            </table>

            <!-- Oturum Detay Özeti -->
            <div class="callout">
                <b>📌 Uçuş / Test Oturumu Bilgisi:</b> Toplam <b>{self.metrikler['toplam_satir']:,}</b> veri noktası incelenmiştir. 
                Test <b>{self.metrikler['baslangic_zamani']}</b> ile <b>{self.metrikler['bitis_zamani']}</b> aralığında gerçekleşmiştir. 
                Test süresinin <b>%{self.metrikler['arizali_yuzde']:.2f}'si ({self.metrikler['arizali_sure_sn']:.1f} saniye)</b> anomali/arıza durumu altında geçmiştir.
            </div>

            <!-- 2. En Uzun Kriz Anı Odak İncelemesi -->
            <div class="section-title">1. En Kritik Kriz Anı İncelemesi</div>
            <table class="data-table" border="1" cellspacing="0" cellpadding="4" style="border: 1px solid #cbd5e1; border-collapse: collapse; width: 100%;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 20%; text-align: center;">Kriz Kategorisi</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 30%; text-align: center;">Zaman Aralığı</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Kesintisiz Süre</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 35%; text-align: center;">Hata Anındaki En Büyük Sapma</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;"><b>{self.en_uzun_blok.get('kategori', '-')}</b></td>
                        <td style="border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;">{self.en_uzun_blok.get('start_time', '-')} ➔ {self.en_uzun_blok.get('end_time', '-')}</td>
                        <td style="border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center; font-weight: bold; color: #dc2626;">{self.en_uzun_blok.get('sure_sn', 0.0):.1f} sn</td>
                        <td style="border: 1px solid #cbd5e1; padding: 4px 6px; color: #0369a1; font-weight: bold; text-align: center;">{self.metrikler['kriz_en_cok_sapan_sensor']}</td>
                    </tr>
                </tbody>
            </table>

            <!-- 3. Şüpheli Sensörler ve Z-Skoru Tablosu -->
            <div class="section-title">2. En Yüksek Sapma Gösteren İlk 5 Şüpheli Sensör (Z-Skoruna Göre)</div>
            <table class="data-table" border="1" cellspacing="0" cellpadding="4" style="border: 1px solid #cbd5e1; border-collapse: collapse; width: 100%;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 5%; text-align: center;">#</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 35%; text-align: center;">Sensör Adı</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Ortalama Değer</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Ölçülen Max</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Limit Durumu</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Ortalama Z-Skoru</th>
                    </tr>
                </thead>
                <tbody>
                    {top5_satirlar_html}
                </tbody>
            </table>

            <!-- 4. Hata Kategorileri Dağılım Tablosu -->
            <div class="section-title">3. Hata Kategorileri ve Anomali Dağılımı</div>
            <table class="data-table" border="1" cellspacing="0" cellpadding="4" style="border: 1px solid #cbd5e1; border-collapse: collapse; width: 100%;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 25%; text-align: center;">Hata Kategorisi</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Blok Sayısı</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 15%; text-align: center;">Toplam Süre</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 14%; text-align: center;">Genel Oran (%)</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 13%; text-align: center;">En Uzun Blok</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4.5px 6px; background-color: #f1f5f9; width: 20%; text-align: center;">En Uzun Blok Zamanı</th>
                    </tr>
                </thead>
                <tbody>
                    {kat_satirlar_html}
                </tbody>
            </table>

            <!-- 5. Kaskad ve Çakışma Durumu -->
            <div class="section-title">4. Zincirleme Arıza Değerlendirmesi</div>
            <div class="callout" style="background-color: #fffbeb; border-left-color: #f59e0b; border-color: #fde68a;">
                <b>Çakışma ve Yayılma Analizi:</b> 
                Test oturumunda <b>{self.metrikler['cakisma_olay_sayisi']} adet veri noktasında ({self.metrikler['cakisma_sure_sn']:.1f} saniye)</b> 
                aynı anda birden fazla hata kategorisi aktif olmuştur. Bu durum, arızanın tek bir bileşende kalmayıp komşu alt sistemlere 
                yayıldığını doğrulamaktadır.
            </div>

            <!-- Alt Bilgi (Footer) -->
            <div class="footer">
                Bu rapor FADEC Uçuş &amp; Test Analiz Sistemi tarafından otomatik olarak oluşturulmuştur.
            </div>
        </body>
        </html>
        """
        return html

    def pdf_kaydet(self, dosya_yolu):
        """
        @brief Oluşturulan HTML şablonunu QtPrintSupport ile yüksek çözünürlüklü A4 PDF'e basar.
        @param dosya_yolu (str) PDF dosyasının kaydedileceği mutlak yol.
        @return tuple (bool, str) Başarı durumu ve durum mesajı.
        """
        try:
            self.analiz_yap()
            html_icerik = self.html_sablonu_olustur()

            # PyQt5 QTextDocument ve QPrinter ile Vektörel PDF Çıktısı
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setPaperSize(QtPrintSupport.QPrinter.A4)
            printer.setOutputFileName(dosya_yolu)
            printer.setPageMargins(5, 5, 5, 5, QtPrintSupport.QPrinter.Millimeter)

            doc = QtGui.QTextDocument()
            doc.setDocumentMargin(0)
            doc.setHtml(html_icerik)
            doc.print_(printer)

            return True, f"Rapor başarıyla kaydedildi:\n{dosya_yolu}"
        except Exception as e:
            return False, f"PDF oluşturma sırasında hata meydana geldi:\n{str(e)}"
