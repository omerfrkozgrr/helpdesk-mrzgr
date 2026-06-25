from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Gorevler, Demirbaslar, GorevNotlari, Bildirim, PersonelProfili, GorevDosyalari, Duyuru

# --- 1. PERSONEL PROFİLİNİ USER İÇİNE GÖMME ---
class PersonelInline(admin.StackedInline):
    model = PersonelProfili
    can_delete = False
    verbose_name_plural = 'Personel Ek Bilgileri (Departman, Telefon, Resim)'
    fk_name = 'user'

# Mevcut User Admin'i genişletiyoruz
class UserAdmin(BaseUserAdmin):
    inlines = (PersonelInline,)
    
    list_display = ('username', 'first_name', 'last_name', 'email', 'get_departman', 'get_telefon', 'is_staff')
    
    def get_departman(self, obj):
        if hasattr(obj, 'profil'):
            return obj.profil.departman
        return "-"
    get_departman.short_description = 'Departman'

    def get_telefon(self, obj):
        if hasattr(obj, 'profil'):
            return obj.profil.telefon
        return "-"
    get_telefon.short_description = 'Telefon'

# Eski User panelini iptal et, bizim süslü olanı kaydet
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# --- 2. DİĞER TABLOLAR ---
@admin.register(Gorevler)
class GorevlerAdmin(admin.ModelAdmin):
    # 'demirbas' yerine 'ilgili_demirbas' yazdık:
    list_display = ('baslik', 'durum', 'oncelik', 'atanan_personel', 'ilgili_demirbas')
@admin.register(Demirbaslar)
class DemirbasAdmin(admin.ModelAdmin):
    list_display = ('ad', 'tip', 'seri_no', 'ip_adresi', 'rdp_port', 'sahibi')
    list_filter = ('tip', 'sahibi')
    search_fields = ('ad', 'seri_no', 'ip_adresi')

@admin.register(Bildirim)
class BildirimAdmin(admin.ModelAdmin):
    list_display = ('kime', 'mesaj', 'okundu', 'tarih')

@admin.register(GorevDosyalari)
class GorevDosyalariAdmin(admin.ModelAdmin):
    list_display = ('dosya', 'gorev', 'yukleyen', 'tarih')

# --- YENİ EKLENEN DUYURU PANELİ ---
@admin.register(Duyuru)
class DuyuruAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'oncelik', 'yayinda', 'okuyan_sayisi', 'tarih')
    list_editable = ('yayinda',)
    filter_horizontal = ('okuyanlar',) # Okuyanları sağa/sola atmalı kutuda göster

    # Listede kaç kişinin okuduğunu gösteren özel fonksiyon
    def okuyan_sayisi(self, obj):
        return obj.okuyanlar.count()
    okuyan_sayisi.short_description = 'Okuyan Kişi Sayısı' 