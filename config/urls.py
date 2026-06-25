from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from yonetim.views import (
    gorev_listesi, gorev_detay, gorev_tamamla, gorev_sil, gorev_ekle,
    gorev_uzerime_al, gorev_ata_admin, gorev_iade, gorev_not_ekle, gorev_dosya_yukle,
    gorev_arsiv, gorev_raporu, rapor_excel_indir, personel_karti, profilim,
    duyuru_okundu, bildirim_gecmisi, gorev_oyla,
    rdp_baglanti, cihaz_listesi, cihaz_sil, demirbas_detay
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('giris/', auth_views.LoginView.as_view(template_name='login.html'), name='giris'),
    path('cikis/', auth_views.LogoutView.as_view(), name='cikis'),

    path('', gorev_listesi, name='anasayfa'),
    path('detay/<int:id>/', gorev_detay, name='gorev_detay'),
    path('yeni-gorev/', gorev_ekle, name='gorev_ekle'),

    path('gorev/tamamla/<int:id>/', gorev_tamamla, name='gorev_tamamla'),
    path('gorev/sil/<int:id>/', gorev_sil, name='gorev_sil'),
    path('gorev/uzerime-al/<int:id>/', gorev_uzerime_al, name='gorev_uzerime_al'),
    path('gorev/iade/<int:id>/', gorev_iade, name='gorev_iade'),
    path('gorev/admin-ata/<int:id>/', gorev_ata_admin, name='gorev_ata_admin'),
    path('gorev/not-ekle/<int:id>/', gorev_not_ekle, name='gorev_not_ekle'),
    path('gorev/dosya-yukle/<int:id>/', gorev_dosya_yukle, name='gorev_dosya_yukle'),
    path('gorev/pdf/<int:id>/', gorev_detay, name='gorev_pdf_indir'),

    path('arsiv/', gorev_arsiv, name='gorev_arsiv'),
    path('rapor/', gorev_raporu, name='gorev_raporu'),
    path('rapor/indir/', rapor_excel_indir, name='rapor_excel_indir'),
    path('personel/<int:user_id>/', personel_karti, name='personel_karti'),
    path('profilim/', profilim, name='profilim'),
    path('duyuru/okundu/<int:id>/', duyuru_okundu, name='duyuru_okundu'),
    path('bildirimler/', bildirim_gecmisi, name='bildirim_gecmisi'),
    path('gorev/oyla/<int:id>/<int:puan>/', gorev_oyla, name='gorev_oyla'),

    path('rdp-baglanti/<int:cihaz_id>/', rdp_baglanti, name='rdp_baglanti'),
    path('cihazlar/', cihaz_listesi, name='cihaz_listesi'),
    path('cihazlar/sil/<int:id>/', cihaz_sil, name='cihaz_sil'),
    path('cihazlar/detay/<int:id>/', demirbas_detay, name='demirbas_detay'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)