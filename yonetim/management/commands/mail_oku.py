import imaplib
import email
import time
import re
import os
from email.header import decode_header, make_header
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from yonetim.models import Gorevler, GorevDosyalari


class Command(BaseCommand):
    help = 'Mail kutusunu dinler, sadece kayıtlı kullanıcılardan gelen mailleri ticket\'a dönüştürür.'

    def handle(self, *args, **kwargs):
        IMAP_SERVER = "imap.gmail.com"
        EMAIL_USER = os.environ.get('EMAIL_HOST_USER', '')
        EMAIL_PASS = os.environ.get('EMAIL_HOST_PASSWORD', '')
        BEKLEME_SURESI = 60

        if not EMAIL_USER or not EMAIL_PASS:
            self.stdout.write(self.style.ERROR(
                "❌ EMAIL_HOST_USER ve EMAIL_HOST_PASSWORD ortam değişkenleri tanımlı değil. "
                ".env dosyanızı kontrol edin."
            ))
            return

        self.stdout.write(self.style.WARNING("🤖 Posta botu başlatıldı. Çıkmak için Ctrl+C."))

        admin_user = User.objects.filter(is_superuser=True).first()

        while True:
            try:
                zaman = timezone.now().strftime('%H:%M:%S')
                mail = imaplib.IMAP4_SSL(IMAP_SERVER)
                mail.login(EMAIL_USER, EMAIL_PASS)
                mail.select("inbox")

                status, messages = mail.search(None, 'UNSEEN')

                if not messages[0]:
                    self.stdout.write(f"[{zaman}] 💤 Yeni mail yok...")
                else:
                    mail_ids = messages[0].split()
                    self.stdout.write(self.style.SUCCESS(f"[{zaman}] 🔔 {len(mail_ids)} yeni mail bulundu."))

                    for mail_id in mail_ids:
                        res, msg = mail.fetch(mail_id, "(RFC822)")
                        for response in msg:
                            if isinstance(response, tuple):
                                msg = email.message_from_bytes(response[1])

                                raw_from = msg.get("From", "")
                                from_decoded = str(make_header(decode_header(raw_from)))

                                sender_email_clean = ""
                                match = re.search(r'<(.+?)>', from_decoded)
                                if match:
                                    sender_email_clean = match.group(1)
                                else:
                                    sender_email_clean = from_decoded.strip()

                                sender_email_clean = sender_email_clean.lower().strip()
                                self.stdout.write(f"   🔎 İnceleniyor: '{sender_email_clean}'")

                                user_exists = User.objects.filter(email__iexact=sender_email_clean).exists()

                                if not user_exists:
                                    self.stdout.write(self.style.ERROR(
                                        f"   ⛔ Reddedildi: '{sender_email_clean}' sistemde kayıtlı değil."
                                    ))
                                    mail.store(mail_id, '+FLAGS', '\\Seen')
                                    continue

                                self.stdout.write(self.style.SUCCESS("   ✅ Kullanıcı doğrulandı."))

                                raw_subject = msg.get("Subject", "(Konusuz)")
                                subject_val = str(make_header(decode_header(raw_subject)))

                                body_text = ""
                                dosya_listesi = []

                                if msg.is_multipart():
                                    for part in msg.walk():
                                        content_type = part.get_content_type()
                                        content_disposition = str(part.get("Content-Disposition"))
                                        filename = part.get_filename()

                                        if filename:
                                            filename = str(make_header(decode_header(filename)))
                                            dosya_verisi = part.get_payload(decode=True)
                                            dosya_listesi.append({'ad': filename, 'veri': dosya_verisi})
                                        elif content_type == "text/plain" and "attachment" not in content_disposition:
                                            try:
                                                body_text += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                                            except:
                                                pass
                                else:
                                    try:
                                        body_text = msg.get_payload(decode=True).decode(errors="ignore")
                                    except:
                                        pass

                                if not body_text.strip():
                                    body_text = "(Boş içerik)"

                                final_aciklama = f"Maili Gönderen: {from_decoded}\n\n---\n\n{body_text}"

                                yeni_gorev = Gorevler(
                                    baslik=subject_val,
                                    aciklama=final_aciklama,
                                    durum="Bekliyor",
                                    oncelik="Orta",
                                    olusturma_tarihi=timezone.now(),
                                    gonderen_email=sender_email_clean
                                )
                                yeni_gorev.save()

                                if dosya_listesi and admin_user:
                                    for d in dosya_listesi:
                                        GorevDosyalari.objects.create(
                                            gorev=yeni_gorev,
                                            yukleyen=admin_user,
                                            dosya=ContentFile(d['veri'], name=d['ad'])
                                        )

                                self.stdout.write(f"   → Görev oluşturuldu: '{subject_val}'")

                mail.close()
                mail.logout()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Hata: {str(e)}"))

            time.sleep(BEKLEME_SURESI)
