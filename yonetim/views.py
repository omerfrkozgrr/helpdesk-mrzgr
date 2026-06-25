from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings
import openpyxl
import requests as http_requests
import base64
import os

# Mail ve Şifre İşlemleri
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

# Modeller ve Formlar
from .models import Gorevler, GorevNotlari, Bildirim, GorevDosyalari, Demirbaslar, PersonelProfili, Duyuru
from .forms import GorevForm, ProfilGuncellemeForm


# --- ANA SAYFA (DUYURULU & ARAMALI) ---
@login_required
def gorev_listesi(request):
    tum_gorevler = Gorevler.objects.exclude(durum='Tamamlandı').order_by('-olusturma_tarihi')
    aktif_duyurular = Duyuru.objects.filter(yayinda=True).exclude(okuyanlar=request.user)

    arama_kelimesi = request.GET.get('q')
    if arama_kelimesi:
        kullanici_ids = User.objects.filter(username__icontains=arama_kelimesi).values_list('id', flat=True)
        tum_gorevler = tum_gorevler.filter(
            Q(baslik__icontains=arama_kelimesi) |
            Q(aciklama__icontains=arama_kelimesi) |
            Q(gonderen_email__icontains=arama_kelimesi) |
            Q(atanan_personel__in=kullanici_ids)
        )

    toplam_sayi = Gorevler.objects.count()
    bekleyen_sayi = Gorevler.objects.filter(durum='Bekliyor').count()
    tamamlanan_sayi = Gorevler.objects.filter(durum='Tamamlandı').count()
    devam_eden_sayi = Gorevler.objects.filter(durum='Devam Ediyor').count()

    context = {
        'gorevler': tum_gorevler,
        'duyurular': aktif_duyurular,
        'toplam': toplam_sayi,
        'bekleyen': bekleyen_sayi,
        'tamamlanan': tamamlanan_sayi,
        'devam': devam_eden_sayi,
        'aranan': arama_kelimesi
    }
    return render(request, 'gorev_listesi.html', context)


@login_required
def gorev_detay(request, id):
    tek_gorev = get_object_or_404(Gorevler, gorev_id=id)
    Bildirim.objects.filter(kime=request.user, gorev=tek_gorev, okundu=False).update(okundu=True)

    # Göreve cihaz atama
    if request.method == 'POST' and 'cihaz_ata' in request.POST:
        cihaz_id = request.POST.get('cihaz_id')
        if cihaz_id:
            tek_gorev.ilgili_demirbas = get_object_or_404(Demirbaslar, id=cihaz_id)
        else:
            tek_gorev.ilgili_demirbas = None
        tek_gorev.save()
        return redirect('gorev_detay', id=id)

    tum_kullanicilar = None
    if request.user.is_superuser:
        tum_kullanicilar = User.objects.all()

    atanan_isim = "Atanmamış"
    if tek_gorev.atanan_personel:
        atanan_isim = tek_gorev.atanan_personel.username

    context = {
        'gorev': tek_gorev,
        'users': tum_kullanicilar,
        'atanan_isim': atanan_isim,
        'cihazlar': Demirbaslar.objects.all().order_by('ad'),
    }
    return render(request, 'gorev_detay.html', context)
# --- YENİ GÖREV ---
@login_required
def gorev_ekle(request):
    if request.method == 'POST':
        form = GorevForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            yeni_gorev = form.save(commit=False)
            yeni_gorev.olusturma_tarihi = timezone.now()

            secilen_personel = form.cleaned_data.get('atanacak_kisi')
            if secilen_personel:
                yeni_gorev.atanan_personel = secilen_personel
                yeni_gorev.durum = "Devam Ediyor"
                yeni_gorev.atayan_personel_id = request.user.id

            yeni_gorev.save()

            gelen_dosya = request.FILES.get('dosya')
            if gelen_dosya:
                GorevDosyalari.objects.create(gorev=yeni_gorev, yukleyen=request.user, dosya=gelen_dosya)

            if secilen_personel:
                Bildirim.objects.create(kime=secilen_personel, gorev=yeni_gorev, mesaj=f"📢 Admin size görev atadı: {yeni_gorev.baslik}")

            return redirect('anasayfa')
    else:
        form = GorevForm(user=request.user)
    return render(request, 'gorev_ekle.html', {'form': form})


# --- İŞLEMLER ---

@login_required
def gorev_tamamla(request, id):
    g = get_object_or_404(Gorevler, gorev_id=id)
    g.durum = "Tamamlandı"
    g.tamamlanma_tarihi = timezone.now()
    g.cozen_personel = request.user
    g.save()

    if g.gonderen_email:
        try:
            site_url = "http://127.0.0.1:8000"
            html_mesaj = f"""
            <h2>Merhaba,</h2>
            <p><strong>"{g.baslik}"</strong> konulu destek talebiniz çözüme kavuşturulmuştur.</p>
            <p>Hizmetimizi değerlendirmek için lütfen tıklayın:</p>
            <div style="display: flex; gap: 20px; margin-top: 20px;">
                <a href="{site_url}/gorev/oyla/{g.gorev_id}/3/" style="text-decoration:none; font-size:24px;">😍 Memnunum</a> &nbsp;
                <a href="{site_url}/gorev/oyla/{g.gorev_id}/2/" style="text-decoration:none; font-size:24px;">😐 Orta</a> &nbsp;
                <a href="{site_url}/gorev/oyla/{g.gorev_id}/1/" style="text-decoration:none; font-size:24px;">😡 Kötü</a>
            </div>
            <br><p>Teşekkürler,<br>MRZGR Helpdesk</p>
            """
            send_mail(
                subject=f"Göreviniz Tamamlandı: {g.baslik}",
                message=strip_tags(html_mesaj),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[g.gonderen_email],
                html_message=html_mesaj,
                fail_silently=False,
            )
        except Exception as e:
            print(f"Mail Hatası: {e}")

    return redirect('gorev_detay', id=id)


# OYLAMA LİNKİ (Login gerektirmez)
def gorev_oyla(request, id, puan):
    gorev = get_object_or_404(Gorevler, gorev_id=id)
    gorev.memnuniyet = puan
    gorev.save()
    return render(request, 'oylama_sonuc.html', {'puan': puan})


@login_required
def gorev_sil(request, id):
    get_object_or_404(Gorevler, gorev_id=id).delete()
    return redirect('anasayfa')


@login_required
def gorev_uzerime_al(request, id):
    g = get_object_or_404(Gorevler, gorev_id=id)
    g.atanan_personel = request.user
    g.durum = "Devam Ediyor"
    g.save()
    return redirect('gorev_detay', id=id)


@login_required
def gorev_iade(request, id):
    g = get_object_or_404(Gorevler, gorev_id=id)
    if g.atanan_personel == request.user or request.user.is_superuser:
        g.atanan_personel = None
        g.durum = "Bekliyor"
        g.save()
    return redirect('gorev_detay', id=id)


@login_required
def gorev_ata_admin(request, id):
    if request.user.is_superuser and request.method == 'POST':
        uid = request.POST.get('secilen_personel')
        if uid:
            g = get_object_or_404(Gorevler, gorev_id=id)
            g.atanan_personel = User.objects.get(id=uid)
            g.durum = "Devam Ediyor"
            g.save()
    return redirect('gorev_detay', id=id)


@login_required
def gorev_not_ekle(request, id):
    if request.method == 'POST':
        gorev = get_object_or_404(Gorevler, gorev_id=id)
        mesaj = request.POST.get('mesaj')
        if mesaj:
            GorevNotlari.objects.create(gorev=gorev, yazan=request.user, mesaj=mesaj)
            hedef = None
            if gorev.atanan_personel and request.user != gorev.atanan_personel:
                hedef = gorev.atanan_personel
            elif request.user == gorev.atanan_personel:
                hedef = User.objects.filter(is_superuser=True).first()
            if hedef:
                Bildirim.objects.create(kime=hedef, gorev=gorev, mesaj=f"💬 {request.user.username.upper()} yorum yazdı: {gorev.baslik}")
    return redirect('gorev_detay', id=id)


@login_required
def gorev_dosya_yukle(request, id):
    if request.method == 'POST':
        gorev = get_object_or_404(Gorevler, gorev_id=id)
        dosya = request.FILES.get('dosya')
        if dosya:
            GorevDosyalari.objects.create(gorev=gorev, yukleyen=request.user, dosya=dosya)
    return redirect('gorev_detay', id=id)


# --- RAPORLAR VE PROFİL ---
@login_required
def gorev_arsiv(request):
    bitenler = Gorevler.objects.filter(durum='Tamamlandı').order_by('-tamamlanma_tarihi')
    q = request.GET.get('q')
    if q:
        bitenler = bitenler.filter(
            Q(baslik__icontains=q) |
            Q(aciklama__icontains=q) |
            Q(cozen_personel__username__icontains=q)
        )
    return render(request, 'gorev_arsiv.html', {'gorevler': bitenler, 'aranan': q})


@login_required
def gorev_raporu(request):
    if not request.user.is_superuser:
        return redirect('anasayfa')

    baslangic = request.GET.get('baslangic')
    bitis = request.GET.get('bitis')
    dep = request.GET.get('departman')

    tum_personeller = User.objects.all()
    if dep:
        tum_personeller = tum_personeller.filter(profil__departman__icontains=dep)

    rapor_listesi = []
    grafik_isimler = []
    grafik_data = []
    sirket_durum = {'Bekliyor': 0, 'Devam Ediyor': 0, 'Tamamlandı': 0}

    for p in tum_personeller:
        gorevler = Gorevler.objects.filter(atanan_personel=p)
        if baslangic and bitis:
            gorevler = gorevler.filter(olusturma_tarihi__date__range=[baslangic, bitis])

        top = gorevler.count()
        bit = gorevler.filter(durum='Tamamlandı').count()
        dev = gorevler.filter(durum='Devam Ediyor').count()
        bek = gorevler.filter(durum='Bekliyor').count()

        sirket_durum['Tamamlandı'] += bit
        sirket_durum['Devam Ediyor'] += dev
        sirket_durum['Bekliyor'] += bek

        oylanan_gorevler = gorevler.filter(memnuniyet__isnull=False)
        toplam_puan = sum([g.memnuniyet for g in oylanan_gorevler])
        oy_sayisi = oylanan_gorevler.count()
        ortalama_puan = round(toplam_puan / oy_sayisi, 1) if oy_sayisi > 0 else 0

        basari = int((bit / top) * 100) if top > 0 else 0

        rapor_listesi.append({
            'id': p.id,
            'ad': p.username,
            'departman': getattr(p, 'profil', None).departman if hasattr(p, 'profil') else '-',
            'toplam': top,
            'tamamlanan': bit,
            'aktif': dev,
            'yuzde': basari,
            'puan': ortalama_puan,
            'oy_sayisi': oy_sayisi
        })

        if top > 0:
            grafik_isimler.append(p.username)
            grafik_data.append(bit)

    sirket_toplam = sum(sirket_durum.values())
    sirket_basari = int((sirket_durum['Tamamlandı'] / sirket_toplam) * 100) if sirket_toplam > 0 else 0

    context = {
        'raporlar': rapor_listesi,
        'filtreler': {'bas': baslangic, 'bit': bitis, 'dep': dep},
        'grafik_pasta': list(sirket_durum.values()),
        'grafik_isimler': grafik_isimler,
        'grafik_data': grafik_data,
        'ozet': {'toplam': sirket_toplam, 'biten': sirket_durum['Tamamlandı'], 'devam': sirket_durum['Devam Ediyor'], 'basari': sirket_basari}
    }
    return render(request, 'gorev_raporu.html', context)


@login_required
def rapor_excel_indir(request):
    if not request.user.is_superuser:
        return redirect('anasayfa')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Personel", "Toplam", "Biten", "Devam", "Başarı %"])
    for p in User.objects.all():
        t = Gorevler.objects.filter(atayan_personel_id=p.id).count()
        b = Gorevler.objects.filter(atayan_personel_id=p.id, durum='Tamamlandı').count()
        d = t - b
        y = int((b / t) * 100) if t > 0 else 0
        ws.append([p.username, t, b, d, y])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Rapor.xlsx'
    wb.save(response)
    return response


@login_required
def personel_karti(request, user_id):
    if not request.user.is_superuser and request.user.id != user_id:
        return redirect('anasayfa')
    p = get_object_or_404(User, id=user_id)
    z = Demirbaslar.objects.filter(sahibi=p)
    b = Gorevler.objects.filter(atayan_personel_id=p.id, durum='Tamamlandı').count()
    return render(request, 'personel_karti.html', {'personel': p, 'zimmetler': z, 'biten_isler': b})


@login_required
def profilim(request):
    try:
        profil = request.user.profil
    except:
        profil = PersonelProfili.objects.create(user=request.user)

    if request.method == 'POST':
        if 'bilgi_guncelle' in request.POST:
            bilgi_form = ProfilGuncellemeForm(request.POST, request.FILES, instance=profil,
                initial={'first_name': request.user.first_name, 'last_name': request.user.last_name, 'email': request.user.email})
            sifre_form = PasswordChangeForm(request.user)
            if bilgi_form.is_valid():
                bilgi_form.save()
                u = request.user
                u.first_name = bilgi_form.cleaned_data['first_name']
                u.last_name = bilgi_form.cleaned_data['last_name']
                u.email = bilgi_form.cleaned_data['email']
                u.save()
                return redirect('profilim')
        elif 'sifre_degistir' in request.POST:
            sifre_form = PasswordChangeForm(request.user, request.POST)
            bilgi_form = ProfilGuncellemeForm(instance=profil)
            if sifre_form.is_valid():
                user = sifre_form.save()
                update_session_auth_hash(request, user)
                return redirect('profilim')
    else:
        bilgi_form = ProfilGuncellemeForm(instance=profil,
            initial={'first_name': request.user.first_name, 'last_name': request.user.last_name, 'email': request.user.email})
        sifre_form = PasswordChangeForm(request.user)
    return render(request, 'profilim.html', {'bilgi_form': bilgi_form, 'sifre_form': sifre_form})


# --- DUYURU OKUNDU İŞARETLEME ---
@login_required
def duyuru_okundu(request, id):
    duyuru = get_object_or_404(Duyuru, id=id)
    duyuru.okuyanlar.add(request.user)
    return redirect('anasayfa')


# --- BİLDİRİM VE DUYURU GEÇMİŞİ ---
@login_required
def bildirim_gecmisi(request):
    gecmis_bildirimler = Bildirim.objects.filter(kime=request.user, okundu=True).order_by('-tarih')
    gecmis_duyurular = Duyuru.objects.filter(okuyanlar=request.user).order_by('-tarih')
    context = {'bildirimler': gecmis_bildirimler, 'duyurular': gecmis_duyurular}
    return render(request, 'bildirim_gecmisi.html', context)


# --- DEMİRBAŞ DETAY ---
@login_required
def demirbas_detay(request, id):
    cihaz = get_object_or_404(Demirbaslar, id=id)
    ilgili_gorevler = Gorevler.objects.filter(ilgili_demirbas=cihaz).order_by('-olusturma_tarihi')
    return render(request, 'demirbas_detay.html', {'cihaz': cihaz, 'ilgili_gorevler': ilgili_gorevler})


# --- CİHAZ LİSTESİ ---
@login_required
def cihaz_listesi(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return redirect('anasayfa')

    if request.method == 'POST':
        ad = request.POST.get('ad')
        tip = request.POST.get('tip')
        seri_no = request.POST.get('seri_no')
        ip_adresi = request.POST.get('ip_adresi') or None
        rdp_port = request.POST.get('rdp_port') or 3389
        rdp_username = request.POST.get('rdp_username') or None
        rdp_password = request.POST.get('rdp_password') or None
        vnc_password = request.POST.get('vnc_password') or None
        alim_tarihi = request.POST.get('alim_tarihi') or None
        sahibi_id = request.POST.get('sahibi') or None
        sahibi = User.objects.get(id=sahibi_id) if sahibi_id else None
        Demirbaslar.objects.create(
            ad=ad, tip=tip, seri_no=seri_no,
            ip_adresi=ip_adresi, rdp_port=rdp_port,
            rdp_username=rdp_username, rdp_password=rdp_password,
            vnc_password=vnc_password,
            alim_tarihi=alim_tarihi, sahibi=sahibi
        )
        return redirect('cihaz_listesi')

    cihazlar = Demirbaslar.objects.all().order_by('ad')
    context = {
        'cihazlar': cihazlar,
        'kullanicilar': User.objects.all(),
        'laptop_sayisi': cihazlar.filter(tip='Laptop').count(),
        'rdp_hazir': cihazlar.exclude(ip_adresi=None).count(),
    }
    return render(request, 'cihaz_listesi.html', context)


# --- CİHAZ SİL ---
@login_required
def cihaz_sil(request, id):
    if request.user.is_superuser:
        get_object_or_404(Demirbaslar, id=id).delete()
    return redirect('cihaz_listesi')


# --- RDP / VNC BAĞLANTI (DİNAMİK) ---
@login_required
def rdp_baglanti(request, cihaz_id):
    cihaz = get_object_or_404(Demirbaslar, id=cihaz_id)

    if not cihaz.ip_adresi:
        return HttpResponse("Bu cihaz için IP adresi tanımlanmamış.", status=400)

    try:
        connection_name = f"cihaz-{cihaz.id}"
        xml_yolu = os.path.join(settings.BASE_DIR, 'guac_config', 'user-mapping.xml')

        # VNC şifresi varsa noVNC, yoksa RDP kullan
        if cihaz.vnc_password:
            # Token dosyasına cihazı kaydet (websockify okur)
            import os as _os
            token_dosyasi = _os.path.join(settings.BASE_DIR, 'novnc_tokens', 'token.cfg')
            _os.makedirs(_os.path.dirname(token_dosyasi), exist_ok=True)
            satirlar = {}
            if _os.path.exists(token_dosyasi):
                with open(token_dosyasi, 'r') as tf:
                    for satir in tf:
                        satir = satir.strip()
                        if ': ' in satir and not satir.startswith('#'):
                            k, v = satir.split(': ', 1)
                            satirlar[k.strip()] = v.strip()
            satirlar[f"cihaz-{cihaz.id}"] = f"{cihaz.ip_adresi}:5900"
            with open(token_dosyasi, 'w') as tf:
                for k, v in satirlar.items():
                    tf.write(f"{k}: {v}\n")

            sunucu_ip = settings.NOVNC_HOST
            token = f"cihaz-{cihaz.id}"
            novnc_url = (
                f"http://{sunucu_ip}:6080/vnc.html"
                f"?path=websockify%3Ftoken%3D{token}"
                f"&password={cihaz.vnc_password}"
                f"&autoconnect=true"
                f"&reconnect=true"
                f"&resize=scale"
            )
            return redirect(novnc_url)
        else:
            baglanti_xml = f"""        <connection name="{connection_name}" id="{cihaz.id}">
            <protocol>rdp</protocol>
            <param name="hostname">{cihaz.ip_adresi}</param>
            <param name="port">{cihaz.rdp_port}</param>
            <param name="username">{cihaz.rdp_username or settings.RDP_USERNAME}</param>
            <param name="password">{cihaz.rdp_password or settings.RDP_PASSWORD}</param>
            <param name="ignore-cert">true</param>
            <param name="security">any</param>
            <param name="server-layout">en-us-qwerty</param>
        </connection>"""

        yeni_xml = f"""<user-mapping>
    <authorize username="" + os.environ.get("GUAC_USERNAME", "guacadmin") + "" password="" + os.environ.get("GUAC_PASSWORD", "guacadmin") + "">
{baglanti_xml}
    </authorize>
</user-mapping>"""

        with open(xml_yolu, 'w') as f:
            f.write(yeni_xml)

        response = http_requests.post(
            'http://127.0.0.1:8081/guacamole/api/tokens',
            data={'username': os.environ.get('GUAC_USERNAME', 'guacadmin'), 'password': os.environ.get('GUAC_PASSWORD', 'guacadmin')}
        )
        token_data = response.json()
        auth_token = token_data['authToken']

        connection_string = f"{connection_name}\x00c\x00default"
        encoded = base64.b64encode(connection_string.encode('utf-8')).decode('utf-8')

        guac_url = f"http://localhost:8081/guacamole/#/client/{encoded}?token={auth_token}"
        return redirect(guac_url)

    except Exception as e:
        return HttpResponse(f"Bağlantı hatası: {e}", status=500)