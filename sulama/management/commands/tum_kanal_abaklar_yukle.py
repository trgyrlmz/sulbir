import os
import pandas as pd
from django.core.management.base import BaseCommand
from sulama.models import Kanal, KanalAbak

class Command(BaseCommand):
    help = "Tüm kanal abak verilerini tek Excel dosyasından (çoklu sayfa) okur ve KanalAbak modeline kaydeder."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Excel dosya yolu (varsayılan: kanal_abaklar.xlsx)')
        parser.add_argument('--clear', action='store_true', help='Mevcut kanal abak kayıtlarını siler.')

    def handle(self, *args, **options):
        file_path = options.get('file')
        clear = options.get('clear')
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        if file_path:
            excel_path = file_path
        else:
            excel_path = os.path.join(BASE_DIR, "./kanal_abaklar.xlsx")
        excel_path = os.path.abspath(excel_path)

        if not os.path.exists(excel_path):
            self.stdout.write(self.style.ERROR(f"Excel dosyası bulunamadı: {excel_path}"))
            return

        # Sayfa adı → Kanal adı eşleştirmesi
        SAYFA_KANAL_MAPPING = {
            'çeltek regülatörü': 'ÇELTEK REGÜLATÖRÜ İLETİM',  # Mevcut kanal
            'Çeltek Regülatörü': 'ÇELTEK REGÜLATÖRÜ İLETİM',
            'Sheet1': 'ÇELTEK REGÜLATÖRÜ İLETİM',
            'Suluova Solsahil S1 Ana Kanalı': 'SULUOVA SOLSAHIL S1 ANA KANALI',
            'Suluova Solsahil S2 Ana Kanalı': 'SULUOVA SOLSAHIL S2 ANA KANALI', 
            'Suluova Sağsahil S2 Ana Kanalı': 'SULUOVA SAĞSAHIL S2 ANA KANALI'
        }

        # Mevcut kayıtları temizle (eğer --clear parametresi verilmişse)
        if clear:
            KanalAbak.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Mevcut kanal abak verileri temizlendi."))

        try:
            excel_file = pd.ExcelFile(excel_path)
            sheet_names = excel_file.sheet_names
            
            toplam_kayit = 0
            basarili_kanallar = []
            hatali_sayfalar = []
            
            self.stdout.write(f"Excel dosyası açıldı: {excel_path}")
            self.stdout.write(f"Bulunan sayfalar: {sheet_names}")
            
            # Mevcut kanalları listele
            mevcut_kanallar = {k.isim: k for k in Kanal.objects.all()}
            self.stdout.write(f"Sistemdeki kanallar: {list(mevcut_kanallar.keys())}")

            for sheet_name in sheet_names:
                self.stdout.write(f"\n{'='*50}")
                self.stdout.write(f"📋 {sheet_name} sayfası işleniyor...")
                
                try:
                    # Excel sayfasını oku
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)
                    
                    # Kanal adını belirle
                    kanal_adi = SAYFA_KANAL_MAPPING.get(sheet_name)
                    if not kanal_adi:
                        # Eğer mapping'de yoksa, sayfa adını doğrudan kullan
                        kanal_adi = sheet_name.strip()
                    
                    # Kanalı bul
                    kanal_obj = None
                    for mevcut_adi, kanal in mevcut_kanallar.items():
                        if kanal_adi.upper() in mevcut_adi.upper() or mevcut_adi.upper() in kanal_adi.upper():
                            kanal_obj = kanal
                            self.stdout.write(f"✓ Kanal eşleşti: '{sheet_name}' → '{kanal.isim}'")
                            break
                    
                    if not kanal_obj:
                        self.stdout.write(self.style.WARNING(f"⚠️ Kanal bulunamadı: '{kanal_adi}'"))
                        self.stdout.write(f"   Lütfen önce admin panelinden '{kanal_adi}' kanalını oluşturun")
                        hatali_sayfalar.append(sheet_name)
                        continue

                    # DataFrame'i kontrol et
                    if df.empty:
                        self.stdout.write(self.style.WARNING(f"⚠️ {sheet_name} sayfası boş"))
                        continue

                    # Baraj formatını işle
                    sayac = self.process_sheet_data(df, kanal_obj, sheet_name)
                    
                    if sayac > 0:
                        toplam_kayit += sayac
                        basarili_kanallar.append(f"{kanal_obj.isim}: {sayac} kayıt")
                        self.stdout.write(f"✅ {sheet_name} tamamlandı: {sayac} kayıt işlendi")
                    else:
                        self.stdout.write(f"⚠️ {sheet_name}: Hiç kayıt işlenemedi")
                        hatali_sayfalar.append(sheet_name)
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ {sheet_name} sayfa hatası: {e}"))
                    hatali_sayfalar.append(sheet_name)
                    continue

            # Özet rapor
            self.stdout.write(f"\n{'='*50}")
            self.stdout.write(f"🎉 İşlem tamamlandı!")
            self.stdout.write(f"📊 Toplam işlenen kayıt: {toplam_kayit}")
            self.stdout.write(f"✅ Başarılı kanallar ({len(basarili_kanallar)}):")
            for kanal_info in basarili_kanallar:
                self.stdout.write(f"   • {kanal_info}")
            
            if hatali_sayfalar:
                self.stdout.write(f"❌ Sorunlu sayfalar ({len(hatali_sayfalar)}): {hatali_sayfalar}")
            
            # Örnek veriler
            if toplam_kayit > 0:
                self.stdout.write(f"\n📋 Örnek veriler:")
                for kanal in Kanal.objects.filter(abaklar__isnull=False).distinct()[:3]:
                    ornekler = kanal.abaklar.order_by('yukseklik')[:3]
                    self.stdout.write(f"   {kanal.isim}:")
                    for ornek in ornekler:
                        self.stdout.write(f"     Y={ornek.yukseklik}m → D={ornek.hacim}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Genel hata: {e}"))

    def process_sheet_data(self, df, kanal_obj, sheet_name):
        """Bir sayfa verilerini işle"""
        # Baraj formatını kullan - kot ekleri sistemi
        self.stdout.write(f"   DataFrame boyutu: {df.shape}")
        
        # İlk sütun ana yükseklik değerleri
        ana_yukseklik_sutun = df.columns[0]
        
        # Kot ekleri (0, 0.01, 0.02, vb.) - sütun başlıklarından al
        kot_ekleri = []
        kot_eki_sutunlari = []
        
        for i, col_name in enumerate(df.columns[1:], 1):  # İlk sütun hariç
            col_str = str(col_name).strip()
            try:
                # Sayısal değerler kot ekleri
                if col_str.replace('.', '').replace(',', '').isdigit() or col_str in ['0', '0.0']:
                    kot_eki = float(col_str.replace(',', '.'))
                    kot_ekleri.append(kot_eki)
                    kot_eki_sutunlari.append(col_name)
                    if len(kot_ekleri) <= 5:  # İlk 5 kot ekini göster
                        self.stdout.write(f"   Kot eki {kot_eki}: {col_name} sütunu")
            except:
                continue
        
        self.stdout.write(f"   Toplam {len(kot_ekleri)} kot eki bulundu")
        
        # Verileri işle
        sayac = 0
        for index, row in df.iterrows():
            try:
                # Ana yükseklik değerini al
                ana_yukseklik_raw = row[ana_yukseklik_sutun]
                if pd.isnull(ana_yukseklik_raw) or str(ana_yukseklik_raw).strip() == '':
                    continue
                
                ana_yukseklik = float(str(ana_yukseklik_raw).replace(',', '.'))
                
                # Her kot eki için işlem yap
                for kot_eki, sutun_adi in zip(kot_ekleri, kot_eki_sutunlari):
                    try:
                        # Debi değerini al
                        debi_raw = row[sutun_adi]
                        if pd.isnull(debi_raw) or str(debi_raw).strip() == '':
                            continue
                        
                        debi = float(str(debi_raw).replace(',', '.'))
                        
                        # Final yükseklik = ana yükseklik + kot eki
                        final_yukseklik = round(ana_yukseklik + kot_eki, 2)
                        
                        # Kanal abak kaydını oluştur veya güncelle
                        kanal_abak, created = KanalAbak.objects.get_or_create(
                            kanal=kanal_obj,
                            yukseklik=final_yukseklik,
                            defaults={'hacim': debi}
                        )
                        
                        if not created:
                            # Var olan kaydı güncelle
                            kanal_abak.hacim = debi
                            kanal_abak.save()
                        
                        sayac += 1
                        
                        # İlk birkaç kaydı detaylı göster
                        if sayac <= 10:
                            action = "🔄" if not created else "✓"
                            self.stdout.write(f"   {action} Y={final_yukseklik}m → D={debi}")
                        elif sayac == 11:
                            self.stdout.write(f"   ... (daha fazla kayıt işleniyor)")
                        
                    except Exception as e:
                        if sayac < 5:  # İlk 5 hatayı göster
                            self.stdout.write(self.style.ERROR(f"   ❌ Kot eki {kot_eki} hatası: {e}"))
                        continue
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Satır {index} ana yükseklik hatası: {e}"))
                continue
        
        return sayac 