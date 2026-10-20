import os
import re
from datetime import datetime
import numpy as np
from PIL import Image
import streamlit as st
import pytesseract
import pypdf
from pdf2image import convert_from_bytes

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Ustawienia strony Streamlit
st.set_page_config(page_title="Generator Zaświadczeń MOPS - Sajmon Software Company", page_icon="📄", layout="centered")

# ==============================================================================
# BAZA DANYCH PRACOWNIKÓW
# ==============================================================================
BAZA_PRACOWNIKOW = [
    {
        "klucz_nazwisko": "furmanek",
        "imie": "Eryka Furmanek",
        "adres": "ul. Kościelna 9/10, 63-900 Ostrów Wlkp.",
        "firma_zatrudniajaca": "Foto Szymon Ostrowski, Plac 23 Stycznia 18, 63-400 Ostrów Wielkopolski",
        "umowa_rodzaj": "Umowa o pracę na czas nieokreślony",
        "okres": "od 01.09.2025 r. do 31.08.2028",
        "stanowisko": "Fotograf",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    },
    {
        "klucz_nazwisko": "glowacka",
        "imie": "Oliwia Głowacka",
        "adres": "Koźminiec 78",
        "firma_zatrudniajaca": "Foto Szymon Ostrowski, Plac 23 Stycznia 18, 63-400 Ostrów Wielkopolski",
        "umowa_rodzaj": "Umowa o pracę na czas nieokreślony",
        "okres": "od 01.09.2025 r. do 31.08.2028",
        "stanowisko": "Fotograf",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    },
    {
        "klucz_nazwisko": "szelag",
        "imie": "Adrianna Szeląg",
        "adres": "ul. Kolejowa 15/15",
        "firma_zatrudniajaca": "Foto Kamila Ostrowska, ul. Warmińska 2a, 63-400 Ostrów Wielkopolski",
        "umowa_rodzaj": "Umowa o pracę na czas nieokreślony",
        "okres": "02.09.2024 - 01.09.2027",
        "stanowisko": "Fotograf",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    }
]

# ==============================================================================
# INICJALIZACJA DOMYŚLNYCH ZMIENNYCH SESJI
# ==============================================================================
dzisiejsza_data = datetime.now().strftime("%d.%m.%Y r.")

defaults = {
    "pracodawca": "Pieczęć zakładu pracy",
    "miejscowosc_data": f"Ostrów Wielkopolski, {dzisiejsza_data}",
    "imie": "",
    "adres": "",
    "firma_zatrudniajaca": "Foto Szymon Ostrowski, Plac 23 Stycznia 18, 63-400 Ostrów Wielkopolski",
    "umowa_rodzaj": "Umowa o pracę na czas nieokreślony",
    "okres": "od 01.09.2025 r. do 31.08.2028",
    "stanowisko": "Fotograf",
    "miesiac": "wrzesień 2026",
    "przychod": 830.98,
    "koszty": 0.00,
    "podatek": 0.00,
    "zdrowotna": 35.63,
    "spoleczne": 93.56,
    "chorobowa": 20.36,
    "wykryto_osobe": False,
    "pdf_generated": False,
    "last_uploaded_file": None
}

for klucz, wartosc in defaults.items():
    if klucz not in st.session_state:
        st.session_state[klucz] = wartosc

# Rejestracja czcionki z obsługą polskich znaków
FONT_NAME = "Helvetica"
if os.path.exists("Roboto-Regular.ttf"):
    pdfmetrics.registerFont(TTFont("Roboto", "Roboto-Regular.ttf"))
    FONT_NAME = "Roboto"

def odczytaj_tekst_z_pliku(uploaded_file):
    filename = uploaded_file.name.lower()
    extracted_text = ""
    
    if filename.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(uploaded_file)
            for page in reader.pages:
                extracted_text += page.extract_text() or ""
        except Exception:
            pass
            
        if not extracted_text.strip():
            try:
                uploaded_file.seek(0)
                images = convert_from_bytes(uploaded_file.read(), first_page=1, last_page=1)
                if images:
                    extracted_text = pytesseract.image_to_string(images[0], lang='pol+eng')
            except Exception:
                pass
    else:
        try:
            img = Image.open(uploaded_file)
            extracted_text = pytesseract.image_to_string(img, lang='pol+eng')
        except Exception:
            pass
            
    return extracted_text

def wykryj_miesiac(text):
    text_clean = re.sub(r'stycznia', '', text, flags=re.IGNORECASE)

    miesiace_dict = {
        "wrze": "wrzesień", "paźd": "październik", "pazd": "październik",
        "list": "listopad", "grud": "grudzień", "lut": "luty",
        "marc": "marzec", "kwiet": "kwiecień", "maj": "maj",
        "czerw": "czerwiec", "lipc": "lipiec", "sierp": "sierpień",
        "styczeń": "styczeń", "styczen": "styczeń"
    }
    
    rok_match = re.search(r'202[0-9]', text)
    rok = rok_match.group(0) if rok_match else "2026"
    
    for klucz, nazwa in miesiace_dict.items():
        if klucz in text_clean.lower():
            return f"{nazwa} {rok}"
    return f"wrzesień {rok}"

def wykryj_kwoty(text):
    kwoty = {}
    
    match_35 = re.search(r'\b35[\.,]63\b', text)
    if match_35:
        kwoty['zdrowotna'] = 35.63
    else:
        zdr_pos = text.lower().find("ubezp. zdr")
        if zdr_pos != -1:
            fragment = text[zdr_pos:zdr_pos+250]
            numery = re.findall(r'\b\d+[\.,]\d{2}\b', fragment)
            for n in numery:
                val = float(n.replace(',', '.'))
                if val > 0:
                    kwoty['zdrowotna'] = val
                    break
        
        if 'zdrowotna' not in kwoty:
            potracenia_pos = text.lower().find("potrącenia")
            if potracenia_pos != -1:
                fragment = text[potracenia_pos:potracenia_pos+250]
                numery = re.findall(r'\b\d+[\.,]\d{2}\b', fragment)
                for n in numery:
                    val = float(n.replace(',', '.'))
                    if val > 0 and val not in [830.98, 681.43]:
                        kwoty['zdrowotna'] = val
                        break

    return kwoty

st.title("📄 Generator Zaświadczenia dla MOPS by Sajmon Software Company")
st.write("Wgraj plik lists płac (zdjęcie JPG/PNG lub dokument PDF). System automatycznie rozpozna pracownika z bazy i przygotuje formularz.")

uploaded_lista = st.file_uploader("Wgraj plik Listy Płac (Zdjęcie lub PDF)", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_lista is not None and st.session_state.last_uploaded_file != uploaded_lista.name:
    with st.spinner("Trwa analiza pliku i odczytywanie danych... Proszę czekać..."):
        st.session_state.last_uploaded_file = uploaded_lista.name
        ocr_text = odczytaj_tekst_z_pliku(uploaded_lista)
        
        st.session_state.miesiac = wykryj_miesiac(ocr_text)
        st.session_state.miejscowosc_data = f"Ostrów Wielkopolski, {datetime.now().strftime('%d.%m.%Y r.')}"
        
        odczytane_kwoty = wykryj_kwoty(ocr_text)
        if 'zdrowotna' in odczytane_kwoty:
            st.session_state.zdrowotna = odczytane_kwoty['zdrowotna']
        else:
            st.session_state.zdrowotna = 35.63
        
        dopasowany_pracownik = None
        for osoba in BAZA_PRACOWNIKOW:
            if osoba["klucz_nazwisko"].lower() in ocr_text.lower():
                dopasowany_pracownik = osoba
                break
        
        if dopasowany_pracownik:
            st.session_state.wykryto_osobe = True
            st.session_state.pracodawca = dopasowany_pracownik["pracodawca_pieczec"]
            st.session_state.imie = dopasowany_pracownik["imie"]
            st.session_state.adres = dopasowany_pracownik["adres"]
            st.session_state.firma_zatrudniajaca = dopasowany_pracownik["firma_zatrudniajaca"]
            st.session_state.umowa_rodzaj = dopasowany_pracownik["umowa_rodzaj"]
            st.session_state.okres = dopasowany_pracownik["okres"]
            st.session_state.stanowisko = dopasowany_pracownik["stanowisko"]
        else:
            st.session_state.wykryto_osobe = False
            st.session_state.imie = ""
            st.session_state.adres = ""

if uploaded_lista is not None:
    if st.session_state.wykryto_osobe:
        st.success(f"Rozpoznano pracownika: **{st.session_state.imie}**!")
    else:
        st.warning("Nie rozpoznano nazwiska na wgranym pliku. Uzupełnij dane pracownika ręcznie w poniższym formularzu.")

    with st.form("edycja_form"):
        st.subheader("1. Nagłówek i data")
        pracodawca = st.text_area("Pieczęć / Dane zakładu pracy (górny lewy róg)", value=st.session_state.pracodawca, height=70)
        miejscowosc_data = st.text_input("Miejscowość i data (górny prawy róg)", value=st.session_state.miejscowosc_data)
        
        st.subheader("2. Dane pracownika")
        imie = st.text_input("Pan/i (Imię i nazwisko)", value=st.session_state.imie)
        adres = st.text_input("Zamieszkały(a) (Adres)", value=st.session_state.adres)
        
        st.subheader("3. Dane o zatrudnieniu")
        firma_zatrudniajaca = st.text_input("Jest zatrudniony(a) w (nazwa i adres firmy)", value=st.session_state.firma_zatrudniajaca)
        umowa_rodzaj = st.text_input("Na podstawie (np. umowa o pracę, 1/1 etatu)", value=st.session_state.umowa_rodzaj)
        okres = st.text_input("W okresie (np. od 01.01.2023 r. do nadal)", value=st.session_state.okres)
        stanowisko = st.text_input("Na stanowisku (np. Sprzedawca, Magazynier)", value=st.session_state.stanowisko)
        
        st.subheader("4. Składniki wynagrodzenia za miesiąc")
        miesiac = st.text_input("Za miesiąc", value=st.session_state.miesiac)
        przychod = st.number_input("1. Przychód z tytułu wynagrodzenia (Brutto)", value=float(st.session_state.przychod), format="%.2f")
        koszty = st.number_input("2. Koszty uzyskania przychodu", value=float(st.session_state.koszty), format="%.2f")
        podatek = st.number_input("3. Miesięczne obciążenie podatkiem dochodowym", value=float(st.session_state.podatek), format="%.2f")
        zdrowotna = st.number_input("4. Kwota składki na ubezpieczenie zdrowotne (Kolumna 9 - Potrącenia)", value=float(st.session_state.zdrowotna), format="%.2f")
        spoleczne = st.number_input("5. Składki emerytalne i rentowe (część ubezpieczonego)", value=float(st.session_state.spoleczne), format="%.2f")
        chorobowa = st.number_input("6. Kwota składki na ubezpieczenie chorobowe", value=float(st.session_state.chorobowa), format="%.2f")
        
        suma_odliczen = koszty + podatek + zdrowotna + spoleczne + chorobowa
        dochod = przychod - suma_odliczen
        
        st.info(f"**7. DOCHÓD = 1 - (2+3+4+5+6): {dochod:.2f} zł**")
        
        submitted = st.form_submit_button("Generuj PDF")
        
        if submitted:
            pdf_filename = "zaswiadczenie_mops.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            width, height = A4
            
            # --- NAGŁÓWEK ---
            c.setFont(FONT_NAME, 10)
            y_stamp = height - 50
            for line in pracodawca.split("\n"):
                c.drawString(50, y_stamp, line)
                y_stamp -= 14
                
            c.drawRightString(width - 50, height - 50, miejscowosc_data)
            
            # --- TYTUŁ DOKUMENTU (Zwiększony odstęp od nagłówka: height - 160) ---
            c.setFont(FONT_NAME, 11.5)
            c.drawCentredString(width / 2, height - 160, "ZAŚWIADCZENIE O WYSOKOŚCI WYNAGRODZENIA Z TYTUŁU ZATRUDNIENIA")
            c.drawCentredString(width / 2, height - 178, "DLA CELÓW POMOCY SPOŁECZNEJ")
            
            # --- DANE OSOBOWE I ZATRUDNIENIA ---
            y = height - 215
            c.setFont(FONT_NAME, 10.5)
            c.drawString(50, y, "Zaświadcza się, że")
            y -= 18
            c.drawString(50, y, f"Pan/i. {imie}")
            y -= 22
            c.drawString(50, y, f"Zamieszkały(a) {adres}")
            y -= 22
            c.drawString(50, y, f"Jest zatrudniony (a) {firma_zatrudniajaca}")
            y -= 22
            c.drawString(50, y, f"na podstawie {umowa_rodzaj}    w okresie {okres}")
            y -= 22
            c.drawString(50, y, f"na stanowisku {stanowisko}")
            
            # --- TABELA WYLICZEŃ (WYJUSTOWANIE KWOT DO PRAWEJ STRONY) ---
            y -= 35
            c.setFont(FONT_NAME, 10.5)
            c.drawString(50, y, "1. Przychód z tytułu wynagrodzenia")
            y -= 16
            c.drawString(65, y, f"za pracę w miesiącu {miesiac}:")
            c.drawRightString(width - 50, y, f"{przychod:.2f} zł")
            
            y -= 22
            c.drawString(50, y, "2. Koszty uzyskania przychodu:")
            c.drawRightString(width - 50, y, f"{koszty:.2f} zł")
            
            y -= 22
            c.drawString(50, y, "3. Miesięczne obciążenie podatkiem dochodowym od osób fizycznych:")
            c.drawRightString(width - 50, y, f"{podatek:.2f} zł")
            
            y -= 22
            c.drawString(50, y, "4. Kwota składki na ubezpieczenie zdrowotne:")
            c.drawRightString(width - 50, y, f"{zdrowotna:.2f} zł")
            
            y -= 22
            c.drawString(50, y, "5. Kwota składki na ubezpieczenie emerytalne i rentowe")
            y -= 16
            c.drawString(65, y, "w części finansowanej przez Ubezpieczonego:")
            c.drawRightString(width - 50, y, f"{spoleczne:.2f} zł")
            
            y -= 22
            c.drawString(50, y, "6. Kwota składki na ubezpieczenie chorobowe:")
            c.drawRightString(width - 50, y, f"{chorobowa:.2f} zł")
            
            y -= 28
            c.setFont(FONT_NAME, 11.5)
            c.drawString(50, y, "7. DOCHÓD = 1 - (2+3+4+5+6):")
            c.drawRightString(width - 50, y, f"{dochod:.2f} zł")
            
            # --- STOPKA / PODPIS ---
            y -= 80
            c.setFont(FONT_NAME, 10)
            c.drawRightString(width - 50, y, "....................................................................")
            c.drawRightString(width - 50, y - 16, "Pieczęć i podpis pracodawcy")
            
            c.save()
            st.session_state.pdf_generated = True

    if st.session_state.pdf_generated:
        st.success("PDF został pomyślnie wygenerowany!")
        if os.path.exists("zaswiadczenie_mops.pdf"):
            with open("zaswiadczenie_mops.pdf", "rb") as pdf_file:
                st.download_button(
                    label="📥 Pobierz gotowy PDF",
                    data=pdf_file,
                    file_name="zaswiadczenie_wypelnione.pdf",
                    mime="application/pdf"
                )
else:
    st.info("💡 Wgraj plik z listą płac (zdjęcie JPG/PNG lub plik PDF) powyżej, aby automatycznie odczytać dane i wygenerować zaświadczenie.")
