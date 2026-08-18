import random
import math
import pandas
import pandas as pd
import numpy as np
from numpy.ma.core import arange

"""
Bizim bu yaptığımız yapıda veriler rastgele sıçrıyor. Normal bir uçak motorunda böyle bir şey olmaz. Ondan dolayı sonradan bunu düzelteceğiz.   
"""

# pyuic5 -x fadec_arayuz.ui -o arayuz_python.py


zamanListesi=np.arange(1,10001)/10
n1=[]
n2=[]
egt=[]
tork=[]
yakit_akisi=[]
yag_basinci=[]
yag_sicakligi=[]
titresim=[]
hata_durumu=[]


for i in range (len(zamanListesi)): # Rangenin içine tek bir int değeri vermemiz lazım. Yoksa diğer türlü olmaz. Ya 10k ver yada len komutuyla yapabilirsin
    n1_Data=random.uniform(60,105)
    n1.append(round(n1_Data,2))

    n2_Data=random.uniform(95,102)
    n2.append(round(n2_Data,2))

    egt_Data=random.uniform(400,850)
    egt.append(round(egt_Data,2))

    tork_Data=random.uniform(20,110)
    tork.append(round(tork_Data,2))


    #yakit_akisi_Data=random.uniform(80,350)

    onceki_deger = yakit_akisi[-1] if yakit_akisi else 200  # İlk değer 200'den başlar
    yeni_deger = onceki_deger + random.uniform(-10, 10)
    yeni_deger = max(80, min(350, yeni_deger))  # Sınırlardan taşmasın
    yakit_akisi.append(round(yeni_deger, 2))

    #yakit_akisi.append(round(yakit_akisi_Data,2))


    yag_basinci_Data=random.uniform(35,85)
    yag_basinci.append(round(yag_basinci_Data,2))

    yag_sicakligi_Data=random.uniform(50,130)
    yag_sicakligi.append(round(yag_sicakligi_Data,2))

    titresim_Data=random.uniform(0,25)
    titresim.append(round(titresim_Data,2))

    hata_durumu_Data = random.choices([0, 1], weights=[90, 10], k=1)[0]
    hata_durumu.append(hata_durumu_Data)


parametreler={
    "Zaman":zamanListesi,
    "N1":n1,
    "N2":n2,
    "EGT":egt,
    "Tork":tork,
    "Yakıt Akisi":yakit_akisi,
    "Yag Basinci":yag_basinci,
    "Yag Sicakligi":yag_sicakligi,
    "Titresim":titresim,
    "Hata Durumu":hata_durumu
}

df= pandas.DataFrame(parametreler)

df.to_csv("FADEC_Data",sep=";",index=False) # Pandas her satırın başına otomatik sıra numarası 0, 1, ... ekler. Bunu istemiyoruz, False diyerek kapatıyoruz.

print(df)