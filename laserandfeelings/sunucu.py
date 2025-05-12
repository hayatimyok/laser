import random
import socket
import threading
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

# Oyun ayarları
HOST = '0.0.0.0'  # Herhangi bir IP adresinden bağlanmaya izin ver
PORT = 12345
MAX_OYUNCU = 4

# Flask uygulamasını ve SocketIO'yu başlat
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # CORS'u etkinleştir

# Ortak Kullanılacak Veri Yapıları
oyuncular = {}  # {socket.sid: {ad, lazer, duygu, karakter_adı}} - Oyuncuların soket oturum kimliklerine göre saklandığı sözlük
gemi = {}  # Geminin özelliklerini saklayan sözlük
hikaye = ""  # Oyunun hikayesini saklayan değişken
oyun_devam_ediyor = True  # Oyunun devam edip etmediğini kontrol eden boolean değişkeni
tur_numarasi = 0  # Mevcut tur numarasını saklayan değişken

# Yardımcı Fonksiyonlar
def zar_at(numara, kullanim, ek_zar=0):
    """
    Zar atma mekaniğini uygular.

    Args:
        numara: Oyuncunun Lazer veya Duygu değeri (2-5).
        kullanim: "Lazer" veya "Duygu" (hangi yeteneğin kullanıldığını belirtir).
        ek_zar: Ekstra atılacak zar sayısı (isteğe bağlı, varsayılan 0).

    Returns:
        Bir zar sonuçları listesi. Her bir zar 1-6 arasında rastgele bir sayı üretir.
    """
    zarlar = [random.randint(1, 6) for _ in range(1 + ek_zar)]  # Atılan zarları bir listede sakla
    print(f"Zarlar: {zarlar}")  # Sunucu konsoluna atılan zarları yazdır (debug amaçlı)

    # Kullanılan yeteneğe göre başarılı zarları belirle
    if kullanim == "Lazer":
        basarili_zarlar = [zar for zar in zarlar if zar <= numara]  # Lazer kullanılıyorsa, numara'ya eşit veya küçük zarlar başarılıdır
    elif kullanim == "Duygu":
        basarili_zarlar = [zar for zar in zarlar if zar > numara]  # Duygu kullanılıyorsa, numara'dan büyük zarlar başarılıdır
    else:
        return "Geçersiz kullanım. 'Lazer' veya 'Duygu' kullanın."  # Geçersiz bir kullanım değeri verilirse hata mesajı döndür

    return basarili_zarlar  # Başarılı zarların listesini döndür

def lazer_duygu_kontrol(numara):
    """
    Lazer ve Duygu değerlerinin 2-5 aralığında olup olmadığını kontrol eder.

    Args:
        numara: Kontrol edilecek sayı.

    Returns:
        True ise 2-5 aralığındadır, False ise değildir.
    """
    return 2 <= numara <= 5  # Verilen numara 2 ile 5 arasındaysa True, değilse False döndür

# SOHBET İLE İLGİLİ FONKSİYONLAR
def sohbet_mesaji(sid, mesaj, gonderen="Sistem"):
    """
    Bir sohbet mesajını tüm oyunculara gönderir.

    Args:
        sid: Mesajı gönderen oyuncunun SocketIO oturum kimliği.
        mesaj: Gönderilecek mesajın içeriği.
        gonderen: Mesajı gönderenin adı (varsayılan "Sistem").
    """
    for alici_sid in oyuncular:  # Tüm oyuncuların oturum kimlikleri üzerinde döngü
        if alici_sid != sid:  # Gönderen oyuncuya mesajı gönderme
            emit('sohbet_mesaji', {'gonderen': gonderen, 'mesaj': mesaj}, room=alici_sid)  # 'sohbet_mesaji' olayını alıcıya gönder

# OYUN İLE İLGİLİ FONKSİYONLAR

def karakter_yarat(sid, ad, lazer, duygu, karakter_adı):
    """
    Bir oyuncu için karakter yaratır.

    Args:
        sid: Oyuncunun SocketIO oturum kimliği.
        ad: Oyuncunun adı.
        lazer: Oyuncunun Lazer değeri (2-5).
        duygu: Oyuncunun Duygu değeri (2-5).
        karakter_adı: Oyuncunun karakter adı.

    Returns:
        Karakter oluşturulursa True, aksi halde False.
    """
    if not lazer_duygu_kontrol(lazer) or not lazer_duygu_kontrol(duygu):  # Lazer ve Duygu değerlerini kontrol et
        emit('hata_mesaji', {'mesaj': 'Lazer ve Duygu değerleri 2-5 arasında olmalıdır.'}, room=sid)  # Hata mesajı gönder
        return False  # Hata durumunda False döndür

    oyuncular[sid] = {  # Oyuncular sözlüğüne yeni oyuncuyu ekle
        'ad': ad,
        'lazer': lazer,
        'duygu': duygu,
        'karakter_adı': karakter_adı
    }
    emit('karakter_olusturuldu', {  # Karakter oluşturuldu mesajını oyuncuya gönder
        'ad': ad,
        'lazer': lazer,
        'duygu': duygu,
        'karakter_adı': karakter_adı
    }, room=sid)
    return True  # Başarı durumunda True döndür


def gemi_yarat(sid, guc1, guc2, sorun):
    """
    Oyuncuların gemisini yaratır. Sadece ilk oyuncu tarafından çağrılır.

    Args:
        sid: Oyuncunun SocketIO oturum kimliği (ilk oyuncu).
        guc1: Geminin ilk gücü.
        guc2: Geminin ikinci gücü.
        sorun: Geminin sorunu.
    """
    global gemi  # global gemi değişkenine erişim
    if gemi:  # Eğer gemi zaten oluşturulduysa
        emit('hata_mesaji', {'mesaj': 'Gemi zaten oluşturuldu.'}, room=sid)  # Hata mesajı gönder
        return  # Fonksiyondan çık

    gemi = {  # gemi sözlüğünü oluştur
        'guc1': guc1,
        'guc2': guc2,
        'sorun': sorun
    }
    emit('gemi_olusturuldu', gemi, room=sid)  # Gemi oluşturuldu mesajını ilk oyuncuya gönder

def hikaye_olustur(sid, tehdit, amac, kaynak, eylem):
    """
    Oyunun hikayesini oluşturur. Sadece ilk oyuncu tarafından çağrılır.

    Args:
        sid: Oyuncunun SocketIO oturum kimliği (ilk oyuncu).
        tehdit: Hikayenin tehdidi.
        amac: Tehdidin amacı.
        kaynak: Tehdidin kaynağı.
        eylem: Tehdidin eylemi.
    """
    global hikaye  # global hikaye değişkenine erişim
    if hikaye:  # Eğer hikaye zaten oluşturulduysa
        emit('hata_mesaji', {'mesaj': 'Hikaye zaten oluşturuldu.'}, room=sid)  # Hata mesajı gönder
        return  # Fonksiyondan çık

    hikaye = {  # hikaye sözlüğünü oluştur
        'tehdit': tehdit,
        'tehdit_amaci': amac,
        'tehdit_kaynagi': kaynak,
        'tehdit_eylemi': eylem
    }
    emit('hikaye_olusturuldu', hikaye, room=sid)  # Hikaye oluşturuldu mesajını ilk oyuncuya gönder


def tur_oyna(sid, eylem):
    """
    Bir tur oynanmasını yönetir.

    Args:
        sid: Şu anda turu olan oyuncunun SocketIO oturum kimliği.
        eylem: Oyuncunun gerçekleştirdiği eylem.
    """
    global tur_numarasi  # global tur_numarasi değişkenine erişim
    tur_numarasi += 1  # Tur numarasını arttır
    emit('tur_basladi', {'tur_numarasi': tur_numarasi}, room=sid)  # Turun başladığını oyuncuya bildir

    if "Lazer" in eylem:  # Oyuncunun eyleminde "Lazer" kelimesi geçiyorsa
        kullanim = "Lazer"  # kullanılacak yeteneği Lazer olarak ayarla
    elif "Duygu" in eylem:  # Oyuncunun eyleminde "Duygu" kelimesi geçiyorsa
        kullanim = "Duygu"  # kullanılacak yeteneği Duygu olarak ayarla
    else:
        emit('hata_mesaji', {'mesaj': "Geçersiz eylem. 'Lazer' veya 'Duygu' içeren bir eylem girin."}, room=sid)  # Geçersiz eylem mesajı gönder
        return  # Fonksiyondan çık

    oyuncu = oyuncular[sid]  # Mevcut oyuncunun bilgilerini al
    zar_sonuclari = zar_at(oyuncu['lazer'] if kullanim == "Lazer" else oyuncu['duygu'], kullanim)  # Zar at ve sonuçları al
    mesaj = f"{oyuncu['karakter_adı']} {kullanim} kullanarak bir eylem yaptı. Zar Sonuçları: {zar_sonuclari}"  # Sohbet mesajı oluştur
    sohbet_mesaji(sid, mesaj, gonderen=oyuncu['ad'])  # Sohbet mesajını gönder

    # Zar sonuçlarına göre istemciye mesaj gönder
    if not zar_sonuclari:
        emit('tur_sonucu', {'sonuc': 'Eylem başarısız oldu.'}, room=sid)  # Başarısızlık mesajı
    elif len(zar_sonuclari) == 1:
        emit('tur_sonucu', {'sonuc': 'Eylem zar zor başarıldı.'}, room=sid)  # Kısmi başarı mesajı
    elif len(zar_sonuclari) == 2:
        emit('tur_sonucu', {'sonuc': 'Eylem başarıyla gerçekleştirildi.'}, room=sid)  # Başarı mesajı
    elif len(zar_sonuclari) >= 3:
        emit('tur_sonucu', {'sonuc': 'Eylem büyük bir başarıyla gerçekleştirildi!'}, room=sid)  # Büyük başarı mesajı

def oyun_sonu(sid):
    """
    Oyunun sonunu yönetir.

    Args:
        sid: Oyunu bitiren oyuncunun SocketIO oturum kimliği.
    """
    global oyun_devam_ediyor  # global oyun_devam_ediyor değişkenine erişim
    oyun_devam_ediyor = False  # Oyunun devam ettiğini belirten değişkeni False yap
    sohbet_mesaji(sid, "Oyun bitti!")  # Sohbet mesajı gönder
    emit('oyun_bitti', {}, broadcast=True)  # Tüm oyunculara oyunun bittiğini bildir

# SocketIO Olayları

@socketio.on('connect')
def baglanti():
    """
    Bir oyuncu bağlandığında gerçekleşir.
    """
    print(f"İstemci bağlandı: {request.sid}")  # Sunucu konsoluna istemci bağlantısını yazdır
    emit('baglanti_basarili', {'mesaj': 'Bağlantı başarılı! Adınızı girin:'}, room=request.sid)  # Bağlantı mesajını gönder

@socketio.on('ad_girildi')
def ad_girildi(data):
    """
    Bir oyuncu adını girdiğinde gerçekleşir.

    Args:
        data: {'ad': oyuncunun adı} - Gelen veri içinde oyuncunun adı olmalı
    """
    sid = request.sid  # Bağlanan istemcinin SocketIO oturum kimliğini al
    ad = data['ad']  # Gelen veriden oyuncunun adını al

    if sid not in oyuncular:  # Eğer oyuncu henüz kayıtlı değilse
        emit('karakter_istek', {'mesaj': 'Lazer ve Duygu değerlerinizi (2-5) ve karakter adınızı girin.'}, room=sid)  # Karakter oluşturma isteği gönder
    else:
        emit('zaten_karakter_var', {'mesaj': 'Zaten bir karakteriniz var.'}, room=sid)  # Oyuncuya zaten karakteri olduğunu bildir

@socketio.on('karakter_olustur')
def karakter_olustur(data):
    """
    Oyuncu karakterini oluşturduğunda gerçekleşir.

    Args:
        data: {'lazer': lazer_değeri, 'duygu': duygu_değeri, 'karakter_adı': karakter_adı}
    """
    sid = request.sid  # Bağlanan istemcinin SocketIO oturum kimliğini al
    ad = oyuncular[sid]['ad']  #ad bilgisini al
    lazer = data['lazer']  # Gelen veriden Lazer değerini al
    duygu = data['duygu']  # Gelen veriden Duygu değerini al
    karakter_adı = data['karakter_adı']  # Gelen veriden karakter adını al
    if karakter_yarat(sid, ad, lazer, duygu, karakter_adı):  # karakter_yarat fonksiyonunu çağır ve başarılıysa
        sohbet_mesaji(sid, f"{ad} oyuna katıldı.")  # Sohbet mesajı gönder
        if len(oyuncular) == 1:  # Eğer oyundaki ilk oyuncuysa
            emit('gemi_istek', {'mesaj': 'Gemi özelliklerini girin (örn. Hızlı, Güçlü Kalkanlar, Yakıt Tüketimi Yüksek):'}, room=sid)  # Gemi oluşturma isteği gönder

@socketio.on('gemi_olustur')
def gemi_olustur(data):
    """
    Oyuncular gemiyi oluşturduğunda gerçekleşir.

    Args:
        data: {guc1, guc2, sorun} - Gemi özellikleri
    """
    sid = request.sid  # Bağlanan istemcinin SocketIO oturum kimliğini al
    gemi_gucu1 = data['guc1']  # Gelen veriden gemi gücü 1'i al
    gemi_gucu2 = data['guc2']  # Gelen veriden gemi gücü 2'yi al
    gemi_sorunu = data['sorun']  # Gelen veriden gemi sorununu al
    gemi_yarat(sid, gemi_gucu1, gemi_gucu2, gemi_sorunu)  # gemi_yarat fonksiyonunu çağır
    emit('hikaye_istek', {'mesaj': 'Hikayeyi oluşturun (Tehdit, Amaç, Kaynak, Eylem):'}, room=sid)  # Hikaye oluşturma isteği gönder

@socketio.on('hikaye_olustur')
def hikaye_olustur(data):
    """
    Oyuncular hikayeyi oluşturduğunda gerçekleşir.

    Args:
        data: {tehdit, amac, kaynak, eylem} - Hikaye bilgileri
    """
    sid = request.sid  # Bağlanan istemcinin SocketIO oturum kimliğini al
    tehdit = data['tehdit']  # Gelen veriden tehdidi al
    amac = data['amac']  # Gelen veriden amacı al
    kaynak = data['kaynak']  # Gelen veriden kaynağı al
    eylem = data['eylem']  # Gelen veriden eylemi al
    hikaye_olustur(sid, tehdit, amac, kaynak, eylem)  # hikaye_olustur fonksiyonunu çağır
    emit('oyun_basliyor', {}, broadcast=True)  # Tüm oyunculara oyunun başladığını bildir

@socketio.on('tur_oyna')
def tur_oyna_event(data):
    """
    Bir oyuncu tur oynadığında gerçekleşir.

    Args:
        data: {eylem} - Oyuncunun eylemi
    """
    sid = request.sid  # Bağlanan istemcinin SocketIO oturum kimliğini al
    eylem = data['eylem']  # Gelen veriden eylemi al
    tur_oyna(sid, eylem)  # tur_oyna fonksiyonunu çağır

@socketio.on('oyun_bitt')
def oyun_bitt_event(data):
    """
    Oyun bittiğinde gerçekleşir.
    """
    sid = request.sid  # Oyunu bitiren oyuncunun SocketIO oturum kimliğini al
    oyun_sonu(sid)  # oyun_sonu fonksiyonunu çağır

# Web Sayfası
@app.route('/')
def index():
    """
    Ana sayfayı (index.html) sunar.
    """
    return render_template('index.html')  # 'index.html' şablonunu render et

if __name__ == "__main__":
    """
    Uygulama çalıştırıldığında bu blok yürütülür.
    """
    socketio.run(app, host=HOST, port=PORT, debug=True)  # SocketIO sunucusunu başlat
