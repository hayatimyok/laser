const socket = io();

let oyunDevamEdiyor = true;
let oyuncular = {};
let gemi = {};
let hikaye = {};

socket.on('connect', () => {
    console.log('Bağlandı:', socket.id);
    emitAdGirildi();
});

function emitAdGirildi() {
    const ad = prompt('Adınızı Girin:');
    if (ad && ad.trim()) {
        socket.emit('ad_girildi', { ad: ad.trim() });
    } else {
        alert('Lütfen geçerli bir ad girin!');
        emitAdGirildi();
    }
}

socket.on('baglanti_basarili', (data) => {
    console.log(data.mesaj);
    mesajGoster(data.mesaj);
});

socket.on('hata_mesaji', (data) => {
    console.error(data.mesaj);
    alert(data.mesaj);
});

socket.on('karakter_istek', (data) => {
    karakterOlusturFormuGoster();
});

function karakterOlusturFormuGoster() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h1>Karakter Oluştur</h1>
        <div class="form-group">
            <label for="lazer">Lazer Değeri (2-5):</label>
            <input type="number" id="lazer" min="2" max="5" required>
        </div>
        <div class="form-group">
            <label for="duygu">Duygu Değeri (2-5):</label>
            <input type="number" id="duygu" min="2" max="5" required>
        </div>
        <div class="form-group">
            <label for="karakter_adi">Karakter Adı:</label>
            <input type="text" id="karakter_adi" required>
        </div>
        <div class="form-group">
            <button id="karakter-olustur-button">Karakter Oluştur</button>
        </div>
    `;

    const karakterOlusturButton = document.getElementById('karakter-olustur-button');
    karakterOlusturButton.addEventListener('click', () => {
        const lazer = parseInt(document.getElementById('lazer').value);
        const duygu = parseInt(document.getElementById('duygu').value);
        const karakter_adi = document.getElementById('karakter_adi').value;

        if (lazer >= 2 && lazer <= 5 && duygu >= 2 && duygu <= 5 && karakter_adi.trim()) {
            socket.emit('karakter_olustur', { lazer, duygu, karakter_adi });
        } else {
            alert('Lütfen geçerli değerler girin (Lazer ve Duygu 2-5 arasında olmalı, Karakter Adı boş olmamalı)!');
        }
    });
}

socket.on('zaten_karakter_var', (data) => {
    alert(data.mesaj);
});

socket.on('karakter_olusturuldu', (data) => {
    oyuncular[socket.id] = data;
    alert(`Karakteriniz oluşturuldu: ${data.ad} (Lazer: ${data.lazer}, Duygu: ${data.duygu}, Karakter Adı: ${data.karakter_adı})`);
    mesajGoster(`Karakteriniz oluşturuldu: ${data.ad} (Lazer: ${data.lazer}, Duygu: ${data.duygu}, Karakter Adı: ${data.karakter_adı})`);
     oyuncuListesiGuncelle();
    if (Object.keys(oyuncular).length === 1) {
        gemiOlusturFormuGoster(); // İlk oyuncu gemiyi oluşturur
    }
});

function oyuncuListesiGuncelle() {
    const oyunAlani = document.getElementById('oyun-alani');
    let oyuncuListesiHTML = '<h2>Oyuncular:</h2><ul>';
    for (const sid in oyuncular) {
        const oyuncu = oyuncular[sid];
        oyuncuListesiHTML += `<li>${oyuncu.ad} (${oyuncu.karakter_adı}) - Lazer: ${oyuncu.lazer}, Duygu: ${oyuncu.duygu}</li>`;
    }
    oyuncuListesiHTML += '</ul>';
    oyunAlani.innerHTML += oyuncuListesiHTML;
}

function gemiOlusturFormuGoster() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h1>Gemi Oluştur</h1>
        <div class="form-group">
            <label for="guc1">Gemi Gücü 1 (örn. Hızlı):</label>
            <input type="text" id="guc1" required>
        </div>
        <div class="form-group">
            <label for="guc2">Gemi Gücü 2 (örn. Güçlü Kalkanlar):</label>
            <input type="text" id="guc2" required>
        </div>
        <div class="form-group">
            <label for="sorun">Gemi Sorunu (örn. Yakıt Tüketimi Yüksek):</label>
            <input type="text" id="sorun" required>
        </div>
        <div class="form-group">
            <button id="gemi-olustur-button">Gemiyi Oluştur</button>
        </div>
    `;

    const gemiOlusturButton = document.getElementById('gemi-olustur-button');
    gemiOlusturButton.addEventListener('click', () => {
        const guc1 = document.getElementById('guc1').value;
        const guc2 = document.getElementById('guc2').value;
        const sorun = document.getElementById('sorun').value;

        if (guc1.trim() && guc2.trim() && sorun.trim()) {
            socket.emit('gemi_olustur', { guc1, guc2, sorun });
        } else {
            alert('Lütfen tüm gemi özelliklerini girin!');
        }
    });
}

socket.on('gemi_olusturuldu', (data) => {
    gemi = data;
    alert(`Geminiz Oluşturuldu: ${data.guc1}, ${data.guc2}, ${data.sorun}`);
    mesajGoster(`Geminiz Oluşturuldu: ${data.guc1}, ${data.guc2}, ${data.sorun}`);
    gemiBilgisiGoster();
    if (Object.keys(oyuncular).length === 1) {
        hikayeOlusturFormuGoster(); // İlk oyuncu hikayeyi oluşturur
    }
});

function gemiBilgisiGoster() {
    const oyunAlani = document.getElementById('oyun-alani');
    const gemiBilgisiHTML = `<div id="gemi-bilgisi">
                                        <h2>Gemi Bilgisi:</h2>
                                        <p>Güç 1: ${gemi.guc1}</p>
                                        <p>Güç 2: ${gemi.guc2}</p>
                                        <p>Sorun: ${gemi.sorun}</p>
                                    </div>`;
    oyunAlani.innerHTML += gemiBilgisiHTML;
}

function hikayeOlusturFormuGoster() {
    const container = document.querySelector('.container');
    container.innerHTML = `
                <h1>Hikaye Oluştur</h1>
                <div class="form-group">
                    <label for="tehdit">Tehdit (örn. Zorgon the Conqueror):</label>
                    <input type="text" id="tehdit" required>
                </div>
                <div class="form-group">
                    <label for="amac">Tehdidin Amacı (örn. Yok Etmek):</label>
                    <input type="text" id="amac" required>
                </div>
                <div class="form-group">
                    <label for="kaynak">Tehdidin Kaynağı (örn. Uzay Korsanları):</label>
                    <input type="text" id="kaynak" required>
                </div>
                <div class="form-group">
                    <label for="eylem">Tehdidin Eylemi (örn. Bir güneş sistemini yok etmek):</label>
                    <input type="text" id="eylem" required>
                </div>
                <div class="form-group">
                    <button id="hikaye-olustur-button">Hikayeyi Oluştur</button>
                </div>
            `;

    const hikayeOlusturButton = document.getElementById('hikaye-olustur-button');
    hikayeOlusturButton.addEventListener('click', () => {
        const tehdit = document.getElementById('tehdit').value;
        const amac = document.getElementById('amac').value;
        const kaynak = document.getElementById('kaynak').value;
        const eylem = document.getElementById('eylem').value;

        if (tehdit.trim() && amac.trim() && kaynak.trim() && eylem.trim()) {
            socket.emit('hikaye_olustur', { tehdit, amac, kaynak, eylem });
        } else {
            alert('Lütfen tüm hikaye ayrıntılarını girin!');
        }
    });
}

socket.on('hikaye_olusturuldu', (data) => {
    hikaye = data;
    alert(`Hikaye Oluşturuldu: ${data.tehdit}, ${data.amac}, ${data.kaynak}, ${data.eylem}`);
    mesajGoster(`Hikaye Oluşturuldu: ${data.tehdit}, ${data.amac}, ${data.kaynak}, ${data.eylem}`);
    hikayeBilgisiGoster();
    oyunBaslat();
});

function hikayeBilgisiGoster() {
    const oyunAlani = document.getElementById('oyun-alani');
    const hikayeBilgisiHTML = `<div id="hikaye-bilgisi">
                                        <h2>Hikaye Bilgisi:</h2>
                                        <p>Tehdit: ${hikaye.tehdit}</p>
                                        <p>Amaç: ${hikaye.amac}</p>
                                        <p>Kaynak: ${hikaye.kaynak}</p>
                                        <p>Eylem: ${hikaye.eylem}</p>
                                    </div>`;
    oyunAlani.innerHTML += hikayeBilgisiHTML;
}

function oyunBaslat() {
    mesajGoster("Oyun başlıyor!");
    turOyna();
}

function turOyna() {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <h1>Tur Oyna</h1>
        <div class="form-group">
            <label for="eylem">Eyleminizi Girin (örn. Lazerle ateş et, Duygularımla ikna et):</label>
            <input type="text" id="eylem" required>
        </div>
        <div class="form-group">
            <button id="zar-at-button">Zarı At</button>
        </div>
        <div id="zar-sonucu"></div>
    `;

    const zarAtButton = document.getElementById('zar-at-button');
    zarAtButton.addEventListener('click', () => {
        const eylem = document.getElementById('eylem').value;
        if (eylem.trim()) {
            socket.emit('tur_oyna', { eylem });
        } else {
            alert('Lütfen bir eylem girin!');
        }
    });
}

socket.on('tur_basladi', (data) => {
    alert(`--- ${data.tur_numarasi}. Tur ---`);
    mesajGoster(`--- ${data.tur_numarasi}. Tur ---`);
});

socket.on('tur_sonucu', (data) => {
    alert(data.sonuc);
    mesajGoster(data.sonuc);
    if (oyunDevamEdiyor) {
        turOyna();
    }
});

socket.on('oyun_bitti', (data) => {
    alert("Oyun Bitti!");
    mesajGoster("Oyun Bitti!");
    oyunDevamEdiyor = false;
});

function mesajGoster(mesaj) {
    const oyunAlani = document.getElementById('oyun-alani');
    oyunAlani.innerHTML += `<p>${mesaj}</p>`;
    oyunAlani.scrollTop = oyunAlani.scrollHeight;
}
