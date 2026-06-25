from django import forms
from django.contrib.auth.models import User
from .models import Gorevler, PersonelProfili

# --- GÖREV FORMU (GÜNCELLENDİ) ---
class GorevForm(forms.ModelForm):
    ONCELIK_SECENEKLERI = [
        ('Düşük', '🟢 Düşük'),
        ('Orta', '🟡 Orta'),
        ('Yüksek', '🔴 Yüksek'),
    ]
    DURUM_SECENEKLERI = [
        ('Bekliyor', '⏳ Bekliyor'),
        ('Devam Ediyor', '⚙️ Devam Ediyor'),
        ('Tamamlandı', '✅ Tamamlandı'),
        ('İptal', '❌ İptal'),
    ]

    baslik = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Yazıcı kağıt sıkıştırıyor'}))
    aciklama = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Sorunun detaylarını buraya yazın...'}))
    oncelik = forms.ChoiceField(choices=ONCELIK_SECENEKLERI, widget=forms.Select(attrs={'class': 'form-select'}))
    durum = forms.ChoiceField(choices=DURUM_SECENEKLERI, widget=forms.Select(attrs={'class': 'form-select'}))
    
    # Dosya Alanı
    dosya = forms.FileField(required=False, label="Ek Dosya / Fotoğraf", widget=forms.FileInput(attrs={'class': 'form-control'}))

    # --- YENİ: PERSONEL SEÇİMİ (Sadece Admin İçin) ---
    atanacak_kisi = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False, # Zorunlu değil, boş bırakırsa havuza düşer
        label="Görevi Direkt Ata (Opsiyonel)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="-- Havuza Bırak (Kimse) --"
    )

    class Meta:
        model = Gorevler
        fields = ['baslik', 'oncelik', 'durum', 'aciklama']

    # Form oluşturulurken kimin girdiğine bakalım
    def __init__(self, *args, **kwargs):
        # View'den gönderilen 'user' bilgisini al
        user = kwargs.pop('user', None)
        super(GorevForm, self).__init__(*args, **kwargs)
        
        # Eğer kullanıcı Admin değilse, 'atanacak_kisi' kutusunu sil!
        if user and not user.is_superuser:
            del self.fields['atanacak_kisi']

# ... (Alttaki ProfilGuncellemeForm aynen kalsın) ...
class ProfilGuncellemeForm(forms.ModelForm):
    first_name = forms.CharField(label="Ad", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Soyad", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="E-posta", widget=forms.EmailInput(attrs={'class': 'form-control'}))
    departman = forms.CharField(required=False, label="Departman", widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefon = forms.CharField(required=False, label="Telefon", widget=forms.TextInput(attrs={'class': 'form-control'}))
    resim = forms.ImageField(required=False, label="Profil Resmi", widget=forms.FileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = PersonelProfili
        fields = ['departman', 'telefon', 'resim']