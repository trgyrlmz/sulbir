import os
import pandas as pd
from django.core.management.base import BaseCommand
from sulama.models import Kanal, KanalAbak

class Command(BaseCommand):
    help = "Kanal abak verilerini Excel'den okur ve KanalAbak modeline kaydeder."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Excel dosya yolu (varsayılan: kanal_abak.xlsx)')
        parser.add_argument('--clear', action='store_true', help='Mevcut kanal abak kayıtlarını siler.')

    def handle(self, *args, **options):
        file_path = options.get('file')
        clear = options.get('clear')
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        if file_path:
            excel_path = file_path
        else:
            excel_path = os.path.join(BASE_DIR, "./kanal_abak.xlsx")
        excel_path = os.path.abspath(excel_path)

        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f"Excel dosyası bulunamadı: {excel_path}"))
            return

        # Mevcut kayıtları temizle (eğer --clear parametresi verilmişse)
        if clear:
            KanalAbak.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Mevcut kanal abak verileri temizlendi."))

        try:
            excel_file = pd.ExcelFile(excel_path)
            sheet_names = excel_file.sheet_names
            
            toplam_kayit = 0
            
            self.stdout.write(f"Excel dosyası açıldı: {excel_path}")
            self.stdout.write(f"Bulunan sayfalar: {sheet_names}")

            for sheet_name in sheet_names:
                self.stdout.write(f"\n{sheet_name} sayfası işleniyor...")
                
                try:
                    # Excel sayfasını oku
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    
                    # Kanal ismini bulma - ÇELTEK REGÜLATÖRÜ İLETİM kanalını kullan
                    kanal_obj = None
                    try:
                        # Önce ÇELTEK içeren kanalı ara
                        kanal_obj = Kanal.objects.filter(isim__icontains="ÇELTEK").first()
                        if kanal_obj:
                            self.stdout.write(f"✓ Kanal bulundu: {kanal_obj.isim}")
                        else:
                            # Tek kanal varsa onu kullan
                            all_kanals = Kanal.objects.all()
                            if all_kanals.count() == 1:
                                kanal_obj = all_kanals.first()
                                self.stdout.write(f"✓ Tek kanal bulundu: {kanal_obj.isim}")
                            else:
                                self.stdout.write(self.style.ERROR(f"❌ ÇELTEK kanalı bulunamadı"))
                                self.stdout.write(f"   Mevcut kanallar: {[k.isim for k in Kanal.objects.all()]}")
                                continue
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"❌ Kanal arama hatası: {e}"))
                        continue

                    # DataFrame'i kontrol et
                    if df.empty:
                        self.stdout.write(self.style.WARNING(f"⚠️ {sheet_name} sayfası boş"))
                        continue

                    # Excel yapısını analiz et
                    self.stdout.write(f"   DataFrame boyutu: {df.shape}")
                    self.stdout.write(f"   Sütunlar: {list(df.columns)}")
                    
                    # Sütun isimlerini standartlaştır
                    df.columns = df.columns.astype(str)
                    
                    # Olası sütun isimleri
                    yukseklik_sutunlari = ['yukseklik', 'yükseklik', 'h', 'height', 'Yükseklik', 'YÜKSEKLIK']
                    hacim_sutunlari = ['hacim', 'debi', 'flow', 'volume', 'Hacim', 'HACİM', 'Debi', 'DEBİ']
                    
                    yukseklik_sutun = None
                    hacim_sutun = None
                    
                    # Sütun isimlerini bul
                    for col in df.columns:
                        col_lower = str(col).lower().strip()
                        if any(y in col_lower for y in ['yukseklik', 'yükseklik', 'h']):
                            yukseklik_sutun = col
                        elif any(h in col_lower for h in ['hacim', 'debi', 'flow', 'volume']):
                            hacim_sutun = col
                    
                    # Eğer sütun isimleri bulunamazsa, ilk iki sütunu kullan
                    if yukseklik_sutun is None or hacim_sutun is None:
                        if len(df.columns) >= 2:
                            yukseklik_sutun = df.columns[0]
                            hacim_sutun = df.columns[1]
                            self.stdout.write(f"   Otomatik sütun ataması: Yükseklik={yukseklik_sutun}, Hacim={hacim_sutun}")
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ Yeterli sütun bulunamadı: {sheet_name}"))
                            continue
                    
                    # Verileri işle
                    sayac = 0
                    for index, row in df.iterrows():
                        try:
                            # Yükseklik değerini al
                            yukseklik_raw = row[yukseklik_sutun]
                            if pd.isnull(yukseklik_raw) or str(yukseklik_raw).strip() == '':
                                continue
                            
                            yukseklik = float(str(yukseklik_raw).replace(',', '.'))
                            
                            # Hacim değerini al
                            hacim_raw = row[hacim_sutun]
                            if pd.isnull(hacim_raw) or str(hacim_raw).strip() == '':
                                continue
                            
                            hacim = float(str(hacim_raw).replace(',', '.'))
                            
                            # Kanal abak kaydını oluştur veya güncelle
                            kanal_abak, created = KanalAbak.objects.get_or_create(
                                kanal=kanal_obj,
                                yukseklik=yukseklik,
                                defaults={'hacim': hacim}
                            )
                            
                            if not created:
                                # Var olan kaydı güncelle
                                kanal_abak.hacim = hacim
                                kanal_abak.save()
                                self.stdout.write(f"   🔄 Güncellendi: Y={yukseklik}m -> H={hacim}m³")
                            else:
                                self.stdout.write(f"   ✓ Eklendi: Y={yukseklik}m -> H={hacim}m³")
                            
                            sayac += 1
                            toplam_kayit += 1
                            
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"   ❌ Satır {index} hatası: {e}"))
                            continue
                    
                    self.stdout.write(f"✅ {sheet_name} tamamlandı: {sayac} kayıt işlendi")
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ {sheet_name} sayfa hatası: {e}"))
                    continue

            self.stdout.write(f"\n🎉 İşlem tamamlandı!")
            self.stdout.write(f"📊 Toplam işlenen kayıt: {toplam_kayit}")
            
            # Özet bilgi
            for kanal in Kanal.objects.all():
                abak_sayisi = kanal.abaklar.count()
                if abak_sayisi > 0:
                    self.stdout.write(f"   {kanal.isim}: {abak_sayisi} abak kaydı")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Genel hata: {e}")) 