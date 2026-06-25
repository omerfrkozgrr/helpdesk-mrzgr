from .models import Bildirim

def bildirim_sayisi(request):
    if request.user.is_authenticated:
        # Sadece sayıyı değil, son 5 bildirimin KENDİSİNİ de alıyoruz
        # order_by('-tarih') -> En yeni en üstte
        # [:5] -> Sadece son 5 taneyi getir (Liste çok uzamasın)
        bildirimler = Bildirim.objects.filter(kime=request.user, okundu=False).order_by('-tarih')[:5]
        sayi = Bildirim.objects.filter(kime=request.user, okundu=False).count()
        
        return {
            'bildirim_adet': sayi,
            'bildirim_listesi': bildirimler  # <-- Bunu ekledik
        }
    return {}