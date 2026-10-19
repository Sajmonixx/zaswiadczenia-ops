import os
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
st.set_page_config(page_title="Generator Zaświadczeń MOPS", page_icon="📄", layout="centered")

# ==============================================================================
# BAZA DANYCH PRACOWNIKÓW - Tutaj dodajesz kolejne osoby
# ==============================================================================
BAZA_PRACOWNIKOW = [
    {
        "klucz_nazwisko": "furmanek",
        "imie": "Eryka Furmanek",
        "adres": "ul. Kościelna 9/10, 63-900 Ostrów Wlkp.",
        "firma_zatrudniajaca": "ABC Sp. z o.o., ul. Główna 1, 63-900 Ostrów Wlkp.",
        "umowa_rodzaj": "Umowa o pracę (1/1 etatu)",
        "okres": "od 01.01.2023 r. do nadal",
        "stanowisko": "Pracownik biurowy",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    },
    {
        "klucz_nazwisko": "kowalski",
        "imie": "Jan Kowalski",
        "adres": "ul. Słoneczna 15, 63-900 Ostrów Wlkp.",
        "firma_zatrudniajaca": "XYZ Sp. z o.o., ul. Parkowa 5, 63-900 Ostrów Wlkp.",
        "umowa_rodzaj": "Umowa zlecenie",
        "okres": "od 01.05.2024 r. do 31.12.2026 r.",
        "stanowisko": "Magazynier",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    },
    {
        "klucz_nazwisko": "nowak",
        "imie": "Anna Nowak",
        "adres": "ul. Długa 4/2, 63-900 Ostrów Wlkp.",
        "firma_zatrudniajaca": "ABC Sp. z o.o., ul. Główna 1, 63-900 Ostrów Wlkp.",
        "umowa_rodzaj": "Umowa o pracę (1/2 etatu)",
        "okres": "od 15.02.2022 r. do nadal",
        "stanowisko": "Sprzedawca",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    }
]

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
            
    return extracted_text.lower()

st.title("📄 Generator Zaświadczenia dla MOPS")
st.write("Wgraj plik listy płac (zdjęcie JPG/PNG lub dokument PDF). System rozpozna pracownika z bazy i przeliczy dochód netto.")

uploaded_lista = st.file_uploader("Wgraj plik Listy Płac (Zdjęcie lub PDF)", type=["jpg", "jpeg", "png", "pdf"])

if "data_extracted" not in st.session_state:
    st.session_state.data_extracted = False

if "pdf_generated" not in st.session_state:
    st.session_state.pdf_generated = False

if uploaded_lista and not st.session_state.data_extracted:
    with st.spinner("Trwa analiza pliku i odczytywanie danych... Proszę czekać..."):
        ocr_text = odczytaj_tekst_z_pliku(uploaded_lista)
        
        dopasowany_pracownik = None
        for osoba in BAZA_PRACOWNIKOW:
            if osoba["klucz_nazwisko"].lower() in ocr_text:
                dopasowany_pracownik = osoba
                break
        
        if dopasowany_pracownik:
            st.session_state.wykryto_osobe = True
            st.session_state.wybrana_osoba_imie = dopasowany_pracownik["imie"]
            st.session_state.pracodawca = dopasowany_pracownik["pracodawca_pieczec"]
            st.session_state.imie = dopasowany_pracownik["imie"]
            st.session_state.adres = dopasowany_pracownik["adres"]
            st.session_state.firma_zatrudniajaca = dopasowany_pracownik["firma_zatrudniajaca"]
            st.session_state.umowa_rodzaj = dopasowany_pracownik["umowa_rodzaj"]
            st.session_state.okres = dopasowany_pracownik["okres"]
            st.session_state.stanowisko = dopasowany_pracownik["stanowisko"]
        else:
            st.session_state.wykryto_osobe = False
            st.session_state.wybrana_osoba_imie = "-- Wybierz ręcznie z bazy --"
            st.session_state.pracodawca = "Pieczęć zakładu pracy"
            st.session_state.imie = ""
            st.session_state.adres = ""
            st.session_state.firma_zatrudniajaca = ""
            st.session_state.umowa_rodzaj = ""
            st.session_state.okres = ""
            st.session_state.stanowisko = ""

        st.session_state.miejscowosc_data = "Ostrów Wielkopolski, 19.10.2026 r."
        st.session_state.miesiac = "wrzesień 2026"
        st.session_state.przychod = 830.98
        st.session_state.koszty = 0.00
        st.session_state.podatek = 0.00
        st.session_state.zdrowotna = 0.00
        st.session_state.spoleczne = 93.56
        st.session_state.chorobowa = 20.36
        
        st.session_state.data_extracted = True
        st.rerun()

if st.session_state.data_extracted:
    opcje_bazy = ["-- Wybierz ręcznie z bazy --"] + [p["imie"] for p in BAZA_PRACOWNIKOW]
    
    idx_domyslny = 0
    if st.session_state.get("wybrana_osoba_imie") in opcje_bazy:
        idx_domyslny = opcje_bazy.index(st.session_state.wybrana_osoba_imie)
        
    wybrany_z_listy = st.selectbox(
        "👤 Wybierz lub zmień pracownika z bazy:",
        opcje_bazy,
        index=idx_domyslny
    )
    
    if wybrany_z_listy != st.session_state.get("wybrana_osoba_imie"):
        st.session_state.wybrana_osoba_imie = wybrany_z_listy
        osoba_znaleziona = next((p for p in BAZA_PRACOWNIKOW if p["imie"] == wybrany_z_listy), None)
        if osoba_znaleziona:
            st.session_state.pracodawca = osoba_znaleziona["pracodawca_pieczec"]
            st.session_state.imie = osoba_znaleziona["imie"]
            st.session_state.adres = osoba_znaleziona["adres"]
            st.session_state.firma_zatrudniajaca = osoba_znaleziona["firma_zatrudniajaca"]
            st.session_state.umowa_rodzaj = osoba_znaleziona["umowa_rodzaj"]
            st.session_state.okres = osoba_znaleziona["okres"]
            st.session_state.stanowisko = osoba_znaleziona["stanowisko"]
            st.session_state.wykryto_osobe = True
        else:
            st.session_state.wykryto_osobe = False
        st.rerun()

    if st.session_state.wykryto_osobe:
        st.success(f"Załadowano dane dla: **{st.session_state.imie}**")
    else:
        st.info("Wpisz dane pracownika ręcznie w poniższym formularzu lub wybierz osobę z listy rozwijanej powyżej.")

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
        przychod
