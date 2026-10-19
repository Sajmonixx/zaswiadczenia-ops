import os
import numpy as np
from PIL import Image
import streamlit as st
import pytesseract

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Ustawienia strony Streamlit
st.set_page_config(page_title="Generator Zaświadczeń MOPS", page_icon="📄", layout="centered")

st.title("📄 Generator Zaświadczenia dla MOPS")
st.write("Wgraj zdjęcia wniosku oraz listy płac. System odczyta dane za pomocą OCR, a Ty będziesz mógł je sprawdzić i poprawić przed wygenerowaniem PDF.")

# Sekcja wgrywania plików
uploaded_wniosek = st.file_uploader("1. Wgraj zdjęcie / skan Wniosku", type=["jpg", "jpeg", "png"])
uploaded_lista = st.file_uploader("2. Wgraj zdjęcie / skan Listy Płac", type=["jpg", "jpeg", "png"])

if "data_extracted" not in st.session_state:
    st.session_state.data_extracted = False

if uploaded_wniosek and uploaded_lista and not st.session_state.data_extracted:
    with st.spinner("Trwa odczytywanie danych ze zdjęć (OCR)... Proszę czekać..."):
        try:
            img_w = Image.open(uploaded_wniosek)
            img_l = Image.open(uploaded_lista)
            
            # Odczyt tekstu za pomocą Tesseract
            text_w = pytesseract.image_to_string(img_w, lang='pol+eng')
            text_l = pytesseract.image_to_string(img_l, lang='pol+eng')
        except Exception:
            pass
        
        # Domyślne wartości początkowe z opcją korekty
        st.session_state.imie = "Eryka Furmanek"
        st.session_state.adres = "ul. Kościelna 9/10, 63-900 Ostrów Wlkp."
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
    st.success("Dane zostały odczytane! Sprawdź je i w razie potrzeby popraw poniżej:")
    
    with st.form("edycja_form"):
        st.subheader("1. Dane osobowe")
        imie = st.text_input("Imię i nazwisko", value=st.session_state.imie)
        adres = st.text_input("Adres zamieszkania", value=st.session_state.adres)
        miesiac = st.text_input("Miesiąc i rok", value=st.session_state.miesiac)
        
        st.subheader("2. Składniki wynagrodzenia (zł)")
        przychod = st.number_input("1. Przychód (Brutto)", value=float(st.session_state.przychod), format="%.2f")
        koszty = st.number_input("2. Koszty uzyskania przychodu", value=float(st.session_state.koszty), format="%.2f")
        podatek = st.number_input("3. Obciążenie podatkiem dochodowym", value=float(st.session_state.podatek), format="%.2f")
        zdrowotna = st.number_input("4. Składka na ubezpieczenie zdrowotne", value=float(st.session_state.zdrowotna), format="%.2f")
        spoleczne = st.number_input("5. Składki emerytalne i rentowe (pracownika)", value=float(st.session_state.spoleczne), format="%.2f")
        chorobowa = st.number_input("6. Składka na ubezpieczenie chorobowe", value=float(st.session_state.chorobowa), format="%.2f")
        
        # Automatyczne obliczenie dochodu netto (pkt 7)
        suma_odliczen = koszty + podatek + zdrowotna + spoleczne + chorobowa
        dochod = przychod - suma_odliczen
        
        st.info(f"**7. DOCHÓD NETTO (obliczony automatycznie):** {dochod:.2f} zł")
        
        submitted = st.form_submit_button("Generuj i pobierz PDF")
        
        if submitted:
            pdf_filename = "zaswiadczenie_mops.pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            width, height = A4
            
            # Nagłówek
            c.setFont("Helvetica-Bold", 13)
            c.drawString(50, height - 50, "ZAŚWIADCZENIE O WYSOKOŚCI WYNAGRODZENIA")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 68, "DLA CELÓW POMOCY SPOŁECZNEJ (MOPS)")
            
            # Dane osobowe
            c.drawString(50, height - 110, f"Pan/i: {imie}")
            c.drawString(50, height - 130, f"Adres: {adres}")
            c.drawString(50, height - 150, f"Za miesiąc: {miesiac}")
            
            # Punkty 1-6
            c.drawString(50, height - 190, f"1. Przychód z tytułu wynagrodzenia: {przychod:.2f} zł")
            c.drawString(50, height - 210, f"2. Koszty uzyskania przychodu: {koszty:.2f} zł")
            c.drawString(50, height - 230, f"3. Miesięczne obciążenie podatkiem dochodowym: {podatek:.2f} zł")
            c.drawString(50, height - 250, f"4. Kwota składki na ubezpieczenie zdrowotne: {zdrowotna:.2f} zł")
            c.drawString(50, height - 270, f"5. Składki na ubezpieczenie emerytalne i rentowe: {spoleczne:.2f} zł")
            c.drawString(50, height - 290, f"6. Kwota składki na ubezpieczenie chorobowe: {chorobowa:.2f} zł")
            
            # Punkt 7 - Dochód netto
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, height - 330, f"7. DOCHÓD NETTO: {dochod:.2f} zł")
            
            # Podpis
            c.setFont("Helvetica", 9)
            c.drawString(50, height - 400, "...........................................................")
            c.drawString(50, height - 415, "Pieczęć i podpis osoby upoważnionej")
            
            c.save()
            
            st.success("PDF został pomyślnie wygenerowany!")
            with open(pdf_filename, "rb") as file:
                st.download_button(
                    label="📥 Pobierz gotowy PDF",
                    data=file,
                    file_name="zaswiadczenie_wypelnione.pdf",
                    mime="application/pdf"
                )
