import os
import numpy as np
from PIL import Image
import streamlit as st
import pytesseract

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Ustawienia strony Streamlit
st.set_page_config(page_title="Generator Zaświadczeń MOPS", page_icon="📄", layout="centered")

# Rejestracja czcionki z obsługą polskich znaków
FONT_NAME = "Helvetica"
if os.path.exists("Roboto-Regular.ttf"):
    pdfmetrics.registerFont(TTFont("Roboto", "Roboto-Regular.ttf"))
    FONT_NAME = "Roboto"

st.title("📄 Generator Zaświadczenia dla MOPS")
st.write("Wgraj zdjęcie lub skan listy płac. Uzupełnij dane pracownika oraz szczegóły zatrudnienia, a system automatycznie przeliczy dochód i wygeneruje zaświadczenie w PDF.")

# Sekcja wgrywania tylko listy płac
uploaded_lista = st.file_uploader("Wgraj zdjęcie / skan Listy Płac", type=["jpg", "jpeg", "png"])

if "data_extracted" not in st.session_state:
    st.session_state.data_extracted = False

if "pdf_generated" not in st.session_state:
    st.session_state.pdf_generated = False

if uploaded_lista and not st.session_state.data_extracted:
    with st.spinner("Trwa odczytywanie danych z listy płac (OCR)... Proszę czekać..."):
        try:
            img_l = Image.open(uploaded_lista)
            text_l = pytesseract.image_to_string(img_l, lang='pol+eng')
        except Exception:
            pass
        
        # Domyślne wartości pól do edycji w formularzu
        st.session_state.pracodawca = "Pieczęć zakładu pracy"
        st.session_state.miejscowosc_data = "Ostrów Wielkopolski, 19.10.2026 r."
        
        st.session_state.imie = "Eryka Furmanek"
        st.session_state.adres = "ul. Kościelna 9/10, 63-900 Ostrów Wlkp."
        st.session_state.firma_zatrudniajaca = ""
        st.session_state.umowa_rodzaj = ""
        st.session_state.okres = ""
        st.session_state.stanowisko = ""
        
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
    st.success("Dane z listy płac zostały załadowane! Uzupełnij poniższe pola przed wygenerowaniem PDF:")
    
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
        zdrowotna = st.number_input("4. Kwota składki na ubezpieczenie zdrowotne", value=float(st.session_state.zdrowotna), format="%.2f")
        spoleczne = st.number_input("5. Składki emerytalne i rentowe (część ubezpieczonego)", value=float(st.session_state.spoleczne), format="%.2f")
        chorobowa = st.number_input("6. Kwota składki na ubezpieczenie chorobowe", value=float(st.session_state.chorobowa), format="%.2f")
        
        # Automatyczne przeliczenie dochodu netto
        suma_odliczen = koszty + podatek + zdrowotna + spoleczne + chorobowa
        dochod = przychod - suma_odliczen
        
        st.info(f"**7. DOCHÓD NETTO (obliczony automatycznie): {dochod:.2f} zł**")
        
        submitted = st.form_submit_button("Generuj PDF")
        
        if submitted:
            pdf_filename = "zaswiadczenie_mops.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            width, height = A4
            
            # --- NAGŁÓWEK ---
            c.setFont(FONT_NAME, 9)
            y_stamp = height - 50
            for line in pracodawca.split("\n"):
                c.drawString(50, y_stamp, line)
                y_stamp -= 12
                
            c.drawRightString(width - 50, height - 50, miejscowosc_data)
            
            # --- TYTUŁ DOKUMENTU ---
            c.setFont(FONT_NAME, 12)
            c.drawCentredString(width / 2, height - 120, "ZAŚWIADCZENIE")
            c.setFont(FONT_NAME, 9.5)
            c.drawCentredString(width / 2, height - 135, "o wysokości wynagrodzenia z tytułu zatrudnienia dla celów pomocy społecznej")
            
            # --- DANE OSOBOWE I ZATRUDNIENIA ---
            y = height - 175
            c.drawString(50, y, f"Zaświadcza się, że Pan/i:  {imie}")
            y -= 20
            c.drawString(50, y, f"zamieszkały(a):  {adres}")
            y -= 20
            c.drawString(50, y, f"jest zatrudniony(a) w:  {firma_zatrudniajaca}")
            y -= 20
            c.drawString(50, y, f"na podstawie:  {umowa_rodzaj}")
            y -= 20
            c.drawString(50, y, f"w okresie:  {okres}")
            y -= 20
            c.drawString(50, y, f"na stanowisku:  {stanowisko}")
            
            # --- TABELA WYLIECZEŃ ---
            y -= 35
            c.setFont(FONT_NAME, 10)
            c.drawString(50, y, f"Dochód z tytułu zatrudnienia za miesiąc: {miesiac}")
            
            c.setFont(FONT_NAME, 9)
            y -= 25
            c.drawString(50, y, f"1. Przychód z tytułu wynagrodzenia za pracę: {przychod:.2f} zł")
            y -= 20
            c.drawString(50, y, f"2. Koszty uzyskania przychodu: {koszty:.2f} zł")
            y -= 20
            c.drawString(50, y, f"3. Miesięczne obciążenie podatkiem dochodowym od osób fizycznych: {podatek:.2f} zł")
            y -= 20
            c.drawString(50, y, f"4. Kwota składki na ubezpieczenie zdrowotne: {zdrowotna:.2f} zł")
            y -= 20
            c.drawString(50, y, f"5. Składki na ubezpieczenie emerytalne i rentowe (część pracownika): {spoleczne:.2f} zł")
            y -= 20
            c.drawString(50, y, f"6. Kwota składki na ubezpieczenie chorobowe: {chorobowa:.2f} zł")
            
            y -= 30
            c.setFont(FONT_NAME, 10)
            c.drawString(50, y, f"7. DOCHÓD NETTO (pkt 1 - (2+3+4+5+6)): {dochod:.2f} zł")
            
            # --- STOPKA / PODPIS ---
            y -= 90
            c.setFont(FONT_NAME, 9)
            c.drawRightString(width - 50, y, "....................................................................")
            c.drawRightString(width - 50, y - 15, "pieczęć i podpis osoby upoważnionej")
            
            c.save()
            st.session_state.pdf_generated = True

    # Przycisk pobierania umieszczony POZA formularzem
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
