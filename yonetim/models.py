from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

# --- GÖREVLER ---
class Gorevler(models.Model):
    gorev_id = models.AutoField(primary_key=True)
    baslik = models.CharField(max_length=200)
    aciklama = models.TextField(blank=True, null=True)
    
    atayan_personel_id = models.IntegerField(blank=True, null=True)
    gonderen_email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="Gönderen Maili")
    atanan_personel = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='atanan_gorevler')
    ilgili_demirbas = models.ForeignKey('Demirbaslar', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlgili Cihaz")
    
    # İşi bitiren kişi
    cozen_personel = models.ForeignKey(User, models.DO_NOTHING, blank=True, null=True, related_name='cozen_gorevler', verbose_name="Görevi Kapatan")

    durum = models.CharField(max_length=20, blank=True, null=True)
    oncelik = models.CharField(max_length=20, blank=True, null=True)
    olusturma_tarihi = models.DateTimeField(blank=True, null=True)
    tamamlanma_tarihi = models.DateTimeField(blank=True, null=True)

    # --- YENİ EKLENEN: MEMNUNİYET PUANI ---
    memnuniyet = models.IntegerField(blank=True, null=True)
    # --------------------------------------

    # SLA (ACİLİYET) HESAPLAMA
    @property
    def aciliyet_durumu(self):
        if self.durum not in ['Bekliyor', 'Açık']:
            return 'normal'
        
        baslangic = self.olusturma_tarihi or timezone.now()
        
        if timezone.is_naive(baslangic):
            baslangic = timezone.make_aware(baslangic)
        
        gecen_sure = timezone.now() - baslangic
        
        if gecen_sure > timedelta(hours=24):
            return 'kritik'
        elif gecen_sure > timedelta(hours=4):
            return 'uyari'
            
        return 'normal'

    class Meta:
        managed = True
        db_table = 'gorevler'

# --- DEMİRBAŞLAR ---
class Demirbaslar(models.Model):
    CIHAZ_TIPLERI = [('Laptop', '💻 Laptop'), ('Telefon', '📱 Telefon'), ('Monitor', '🖥️ Monitör'), ('Yazici', '🖨️ Yazıcı'), ('Diger', '🔌 Diğer')]
    ad = models.CharField(max_length=100, verbose_name="Cihaz Adı")
    tip = models.CharField(max_length=20, choices=CIHAZ_TIPLERI, default='Laptop')
    seri_no = models.CharField(max_length=50, unique=True, verbose_name="Seri Numarası")
    
    # --- YENİ EKLENEN ALANLAR ---
    ip_adresi = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Adresi")
    rdp_port = models.IntegerField(default=3389, verbose_name="RDP Portu")
    # ----------------------------

    alim_tarihi = models.DateField(null=True, blank=True, verbose_name="Alım Tarihi")
    sahibi = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Zimmetli Personel")
    class Meta: verbose_name = "Demirbaş"; verbose_name_plural = "Demirbaşlar"

    rdp_username = models.CharField(max_length=100, blank=True, null=True, verbose_name="RDP Kullanıcı Adı")
    rdp_password = models.CharField(max_length=100, blank=True, null=True, verbose_name="RDP Şifresi")

    vnc_password = models.CharField(max_length=100, blank=True, null=True, verbose_name="VNC Şifresi")

# --- NOTLAR ---
class GorevNotlari(models.Model):
    gorev = models.ForeignKey('Gorevler', on_delete=models.CASCADE, related_name='notlar')
    yazan = models.ForeignKey(User, on_delete=models.CASCADE)
    mesaj = models.TextField()
    tarih = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['tarih']

# --- BİLDİRİMLER ---
class Bildirim(models.Model):
    kime = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bildirimler')
    gorev = models.ForeignKey('Gorevler', on_delete=models.CASCADE)
    mesaj = models.CharField(max_length=255)
    okundu = models.BooleanField(default=False)
    tarih = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-tarih']

# --- DOSYALAR ---
class GorevDosyalari(models.Model):
    gorev = models.ForeignKey(Gorevler, on_delete=models.CASCADE, related_name='dosyalar')
    yukleyen = models.ForeignKey(User, on_delete=models.CASCADE)
    dosya = models.FileField(upload_to='gorev_dosyalari/')
    tarih = models.DateTimeField(auto_now_add=True)

# --- PERSONEL PROFİLİ ---
class PersonelProfili(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil')
    departman = models.CharField(max_length=100, blank=True, null=True)
    unvan = models.CharField(max_length=100, blank=True, null=True)
    telefon = models.CharField(max_length=20, blank=True, null=True)
    resim = models.ImageField(upload_to='personel_resimleri/', blank=True, null=True)
    def __str__(self): return f"{self.user.username} Profili"
    class Meta: verbose_name = "Personel Detayı"; verbose_name_plural = "Personel Detayları"

# --- DUYURULAR ---
class Duyuru(models.Model):
    ACILIYET_SECENEKLERI = [('Normal', '🔵 Normal Bilgi'), ('Acil', '🔴 Acil Durum'), ('Kutlama', '🟢 Kutlama / Haber')]
    baslik = models.CharField(max_length=200, verbose_name="Duyuru Başlığı")
    mesaj = models.TextField(verbose_name="Duyuru İçeriği")
    oncelik = models.CharField(max_length=20, choices=ACILIYET_SECENEKLERI, default='Normal')
    yayinda = models.BooleanField(default=True, verbose_name="Yayında mı?")
    tarih = models.DateTimeField(auto_now_add=True)
    okuyanlar = models.ManyToManyField(User, blank=True, related_name='okunan_duyurular', verbose_name="Okuyan Personeller")
    def __str__(self): return self.baslik
    class Meta: verbose_name = "Duyuru"; verbose_name_plural = "Duyurular"; ordering = ['-tarih']