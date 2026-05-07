# 5G Signal Analyzer — O'rnatish yo'riqnomasi

## Talablar
- Python 3.8 yoki undan yuqori (python.org dan yuklab oling)
- Internet (IP joylashuv uchun)

## Dasturni ishga tushirish (to'g'ridan-to'g'ri)

```
python signal_analyzer.py
```

## .EXE yaratish (bir marta)

1. `build.bat` faylini ikki marta bosing
2. Kutib turing (~1-2 daqiqa)
3. `dist\SignalAnalyzer.exe` fayli tayyor bo'ladi

## Dastur imkoniyatlari

- 3G / 4G / 5G texnologiyalarini tanlash
- Antenna masofasi, bino zichligi, quvvatni sozlash
- PL, BL, Pr, SNR, Throughput hisoblash (Shannon formulasi)
- Android RSRP qiymatini kiritib real signal tahlili
- IP manzil orqali shahar va koordinatni aniqlash
- Signal kuchi vizualizatsiyasi (rangli barlar)

## Formulalar

```
PL  = 20·log10(freq_MHz) + 20·log10(dist_km) + 32.44
BL  = building_density × distance_m × attenuation / 1000
Pr  = Pt − (PL + BL)
SNR = Pr − noise_level
C   = BW × log2(1 + SNR_linear)   [Shannon]
```

## Android RSRP olish

Telefonda: *#*#4636#*#* → Phone information → Signal strength
