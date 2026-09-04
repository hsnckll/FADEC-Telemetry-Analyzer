# FADEC Data Visualization - EXE Olarak Derleme Rehberi

Bu döküman, Python (PyQt5) ile geliştirilen bu projeyi Windows üzerinde kurulum gerektirmeden çalışabilen tek bir `.exe` formatına dönüştürmek için gereken adımları içerir.

## Adım 1: Proje Klasörüne Giriş Yapın
Öncelikle bir komut satırı (CMD, PowerShell veya VS Code Terminali) açın ve projenizin ana dizinine geçiş yapın:

```bash
cd C:\Users\petti\FadecDataVisualization
```

## Adım 2: PyInstaller'ı Yükleyin
Projeyi derleyip `.exe` haline getirmek için `pyinstaller` paketini kullanacağız. Sisteminizde yüklü değilse şu komutla yükleyin:

```bash
pip install pyinstaller
```

## Adım 3: Projeyi EXE'ye Çevirin
Terminalde aşağıdaki kodu çalıştırarak derleme işlemini başlatın. Bu komuttaki `--noconsole` parametresi uygulamanın arkasında siyah bir CMD penceresi çıkmasını engeller, `--onefile` ise her şeyi tek bir `.exe` dosyasında toplar.

```bash
pyinstaller --noconsole --onefile main.py
```

*(Opsiyonel: Eğer programınıza bir ikon eklemek isterseniz komutu şu şekilde çalıştırabilirsiniz: `pyinstaller --noconsole --onefile --icon=ikonunuz.ico main.py`)*

## Adım 4: Dosyayı Çalıştırma
İşlem başarıyla tamamlandığında, projenizin bulunduğu klasörde **`dist`** isimli yeni bir klasör oluşacaktır.
Oluşturulan `main.exe` dosyası bu klasörün içindedir. Programın adını isterseniz değiştirebilirsiniz.

**⚠️ ÖNEMLİ BİLGİ:** 
Program çalıştığında `parameters.json` gibi dışarıdan okuduğu yapılandırma dosyalarına ihtiyaç duyar. `.exe` dosyasını `dist` klasöründen alıp nereye taşırsanız taşıyın, o veri dosyalarını da mutlaka `.exe`'nin **yanına (aynı klasöre)** kopyalamayı unutmayın. Aksi takdirde program parametreleri bulamayacağı için hata verebilir veya açılmayabilir.
