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
        "klucz_nazwisko": "kowalski",
        "imie": "Jan Kowalski",
        "adres": "ul. Słoneczna 15, 63-900 Ostrów Wlkp.",
        "firma_zatrudniajaca": "Foto Szymon Ostrowski, Plac 23 Stycznia 18, 63-400 Ostrów Wielkopolski",
        "umowa_rodzaj": "Umowa o pracę na czas nieokreślony",
        "okres": "od 01.09.2025 r. do 31.08.2028",
        "stanowisko": "Fotograf",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    },
    {
        "klucz_nazwisko": "nowak",
        "imie": "Anna Nowak",
        "adres": "ul. Długa 4/2, 63-900 Ostrów Wlkp.",
        "firma_zatrudniajaca": "Foto Szymon Ostrowski, Plac 23 Stycznia 18, 63-400 Ostrów Wielkopolski",
        "umowa_rodzaj": "Umowa o pracę na czas nieokreślony",
        "okres": "od 01.09.2025 r. do 31.08.2028",
        "stanowisko": "Fotograf",
        "pracodawca_pieczec": "Pieczęć zakładu pracy"
    }
]

# ==============================================================================
# INICJALIZACJA DOMYŚLNYCH ZMIENNYCH SESJI
# ==============================================================================
defaults = {
    "pracodawca": "Pieczęć zakładu pracy",
    "miejscowosc_data": "Ostrów Wielkopolski, 19.10.2026 r.",
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
    "zdrowotna": 0.00,
    "spoleczne": 93.56,
    "chorobowa": 20.36,
    "wykryto_osobe": False,
    "wybrana_osoba_imie": "-- Wybierz ręcznie z bazy --",
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
                images = convert_from_bytes(uploaded_file.read(), first_page=1, last_page
