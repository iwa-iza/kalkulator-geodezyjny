# ═══════════════════════════════════════════════════════════════
#  KALKULATOR GEODEZYJNY
#  Politechnika Morska w Szczecinie | Geoinformatyka | PiG
#  Autorzy: [Imię Nazwisko 1], [Imię Nazwisko 2], [Imię Nazwisko 3]
# ═══════════════════════════════════════════════════════════════

import streamlit as st
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# ── Konfiguracja strony ──────────────────────────────────────
st.set_page_config(
    page_title="Kalkulator Geodezyjny",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── Style CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { padding-top: 0.5rem; }
    .stButton > button {
        border-radius: 8px;
        font-weight: bold;
        font-size: 1rem;
    }
    .stMetric { background: #f0f4ff; border-radius: 8px; padding: 4px; }
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.2rem !important; color: #1e40af; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# PANEL BOCZNY – INSTRUKCJA OBSŁUGI
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📖 Instrukcja obsługi")
    st.caption("Kalkulator Geodezyjny v1.0 | PM Szczecin")
    st.divider()

    with st.expander("🚀 Uruchomienie"):
        st.markdown("""
**Lokalnie:**
1. Zainstaluj biblioteki: `pip install -r requirements.txt`
2. Uruchom: `streamlit run app.py`
3. Otwórz przeglądarkę: `localhost:8501`

**Na telefonie (ta sama sieć Wi-Fi):**
Wpisz adres IP komputera zamiast `localhost`.
        """)

    with st.expander("📏 Odległość"):
        st.markdown("""
**Wzór:**
$$d = \\sqrt{(X_2-X_1)^2 + (Y_2-Y_1)^2}$$

**Dane wejściowe:** X₁, Y₁, X₂, Y₂ w metrach

**Przykład:**
- X₁=100, Y₁=200, X₂=250, Y₂=500
- Wynik: **d = 335.4102 m**
        """)

    with st.expander("🧭 Azymut"):
        st.markdown("""
**Wzór:**
$$A = (90° - \\arctan2(\\Delta Y, \\Delta X)) \\mod 360°$$

**Dane wejściowe:** X₁,Y₁ (skąd), X₂,Y₂ (dokąd)

**Przykład:**
- Wynik: **A = 26° 33' 54.18"**
        """)

    with st.expander("📐 Pole Gaussa"):
        st.markdown("""
**Wzór sznurowy:**
$$P = \\frac{1}{2} \\left| \\sum_{i=1}^{n}(x_i y_{i+1} - x_{i+1} y_i) \\right|$$

**Dane wejściowe:** Wierzchołki X Y, jeden na linię

**Przykład:**
100 200
150 350
300 300
250 150
Wynik: **P = 27500.00 m² = 2.75 ha**
        """)

    with st.expander("➡️ Biegunowe → Prostokątne"):
        st.markdown("""
**Wzory:**
$$\\Delta X = d \\cdot \\cos(A)$$
$$\\Delta Y = d \\cdot \\sin(A)$$

**Dane:** odległość d [m], azymut A [°]
        """)

    with st.expander("⬅️ Prostokątne → Biegunowe"):
        st.markdown("""
**Wzory:**
$$d = \\sqrt{\\Delta X^2 + \\Delta Y^2}$$
$$A = (90° - \\arctan2(\\Delta Y, \\Delta X)) \\mod 360°$$
        """)

    with st.expander("📍 Wcięcie liniowe"):
        st.markdown("""
Wyznaczenie punktu **P** z dwóch znanych punktów **A**, **B**
i odległości **dA**, **dB**.

Daje **2 rozwiązania geometryczne** – wybierz zgodne
z lokalizacją w terenie.

**Przykład:**
- A=(0,0), B=(100,0), dA=70, dB=60
- P1: X=47.50, Y=50.50
- P2: X=47.50, Y=-50.50
        """)

    with st.expander("🗺️ Przeliczanie układów"):
        st.markdown("""
**Obsługiwane układy:**
- WGS84 (GPS) – EPSG:4326
- PUWG 1992 – EPSG:2180
- PUWG 2000 str. 5 – EPSG:2176
- PUWG 2000 str. 6 – EPSG:2177
- PUWG 2000 str. 7 – EPSG:2178
- PUWG 2000 str. 8 – EPSG:2179

Po przeliczeniu punkt pojawi się **na mapie OSM**.
        """)

    st.divider()
    st.markdown("""
**Autorzy:**
[Imię Nazwisko 1]
[Imię Nazwisko 2]
[Imię Nazwisko 3]

*Geoinformatyka | PM Szczecin | 2025/2026*
    """)


# ═══════════════════════════════════════════════════════════════
# FUNKCJE GEODEZYJNE
# ═══════════════════════════════════════════════════════════════

def odleglosc(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def azymut(x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        raise ValueError("Punkty są identyczne – brak kierunku.")
    return (90 - math.degrees(math.atan2(dy, dx))) % 360


def pole_gaussa(punkty):
    n = len(punkty)
    if n < 3:
        raise ValueError("Wielobok musi mieć co najmniej 3 wierzchołki.")
    return abs(sum(
        punkty[i][0] * punkty[(i + 1) % n][1] -
        punkty[(i + 1) % n][0] * punkty[i][1]
        for i in range(n)
    )) / 2


def biegunowe_na_prostokatne(d, az_deg):
    a = math.radians(az_deg)
    return d * math.cos(a), d * math.sin(a)


def prostokatne_na_biegunowe(dx, dy):
    d = math.sqrt(dx ** 2 + dy ** 2)
    if d == 0:
        raise ValueError("Oba przyrosty są zerowe.")
    az = (90 - math.degrees(math.atan2(dy, dx))) % 360
    return d, az


def wciecie_liniowe(xA, yA, xB, yB, dA, dB):
    dAB = odleglosc(xA, yA, xB, yB)
    if dAB == 0:
        raise ValueError("Punkty A i B są identyczne.")
    if dA + dB < dAB or abs(dA - dB) > dAB:
        raise ValueError("Podane odległości nie tworzą trójkąta – brak rozwiązania.")
    cos_alfa = (dA ** 2 + dAB ** 2 - dB ** 2) / (2 * dA * dAB)
    cos_alfa = max(-1.0, min(1.0, cos_alfa))
    alfa = math.acos(cos_alfa)
    az_AB = math.radians(azymut(xA, yA, xB, yB))
    rozw = []
    for znak in [+1, -1]:
        az_P = az_AB + znak * alfa
        xP = xA + dA * math.cos(az_P)
        yP = yA + dA * math.sin(az_P)
        rozw.append((xP, yP))
    return rozw


def dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = ((deg - d) * 60 - m) * 60
    return f"{d}° {m}' {s:.2f}\""


# ── Słownik układów EPSG ─────────────────────────────────────
UKLADY = {
    "WGS84 (GPS)":         "EPSG:4326",
    "PUWG 1992":           "EPSG:2180",
    "PUWG 2000 strefa 5":  "EPSG:2176",
    "PUWG 2000 strefa 6":  "EPSG:2177",
    "PUWG 2000 strefa 7":  "EPSG:2178",
    "PUWG 2000 strefa 8":  "EPSG:2179",
}


def przelicz_uklad(x_in, y_in, uklad_z, uklad_na):
    t = Transformer.from_crs(
        UKLADY[uklad_z], UKLADY[uklad_na], always_xy=False
    )
    return t.transform(x_in, y_in)


# ═══════════════════════════════════════════════════════════════
# RYSUNKI GEOMETRYCZNE (matplotlib)
# ═══════════════════════════════════════════════════════════════

def rysuj_azymut(x1, y1, x2, y2, az_deg):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.set_facecolor("#f8fafc")
    ax.set_aspect("equal")
    margin = max(abs(x2 - x1), abs(y2 - y1)) * 0.25
    ax.set_xlim(min(y1, y2) - margin, max(y1, y2) + margin)
    ax.set_ylim(min(x1, x2) - margin, max(x1, x2) + margin)

    # linia kierunku
    ax.plot([y1, y2], [x1, x2], "b-o", lw=2, ms=8, zorder=4)

    # strzałka Północy
    n_len = margin * 0.8
    ax.annotate("", xy=(y1, x1 + n_len), xytext=(y1, x1),
                arrowprops=dict(arrowstyle="-|>", color="red", lw=2.5),
                zorder=5)
    ax.text(y1, x1 + n_len + margin * 0.08, "N",
            color="red", fontsize=11, ha="center", fontweight="bold")

    # łuk kąta
    r = margin * 0.4
    theta1_deg = 90
    theta2_deg = 90 - az_deg
    if theta2_deg > theta1_deg:
        theta1_deg, theta2_deg = theta2_deg, theta1_deg
    arc = mpatches.Arc((y1, x1), 2 * r, 2 * r,
                       angle=0,
                       theta1=min(theta1_deg, 90),
                       theta2=max(theta2_deg, 90 - az_deg),
                       color="green", lw=2)
    ax.add_patch(arc)
    ax.text(y1 + r * 0.6, x1 + r * 0.4,
            f"A = {az_deg:.2f}°", color="green", fontsize=9)

    # etykiety punktów
    ax.text(y1 - margin * 0.12, x1, "P1",
            fontsize=11, fontweight="bold", color="#1d4ed8")
    ax.text(y2 + margin * 0.04, x2, "P2",
            fontsize=11, fontweight="bold", color="#1d4ed8")

    ax.set_xlabel("Y [m]")
    ax.set_ylabel("X [m]")
    ax.set_title("Schemat azymutu geodezyjnego", fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def rysuj_wciecie(xA, yA, xB, yB, dA, dB, rozwiazania):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_facecolor("#f8fafc")
    ax.set_aspect("equal")

    wszystkie_x = [xA, xB] + [r[0] for r in rozwiazania]
    wszystkie_y = [yA, yB] + [r[1] for r in rozwiazania]
    margin = max(max(wszystkie_x) - min(wszystkie_x),
                 max(wszystkie_y) - min(wszystkie_y)) * 0.25
    ax.set_xlim(min(wszystkie_y) - margin, max(wszystkie_y) + margin)
    ax.set_ylim(min(wszystkie_x) - margin, max(wszystkie_x) + margin)

    # okręgi pomocnicze
    okrag_A = plt.Circle((yA, xA), dA, fill=False,
                         color="#1d4ed8", ls="--", lw=1.2, alpha=0.4)
    okrag_B = plt.Circle((yB, xB), dB, fill=False,
                         color="#9333ea", ls="--", lw=1.2, alpha=0.4)
    ax.add_patch(okrag_A)
    ax.add_patch(okrag_B)

    # punkty osnowy
    ax.plot([yA, yB], [xA, xB], "ko", ms=10, zorder=5)
    ax.text(yA - margin * 0.15, xA, "A",
            fontsize=12, fontweight="bold")
    ax.text(yB + margin * 0.05, xB, "B",
            fontsize=12, fontweight="bold")
    ax.plot([yA, yB], [xA, xB], "k-", lw=1.5, alpha=0.5)

    # linie i punkty wynikowe
    kolory = ["#16a34a", "#dc2626"]
    for i, (rozw, kol) in enumerate(zip(rozwiazania, kolory)):
        xP, yP = rozw
        ax.plot([yA, yP], [xA, xP], "--", color=kol, lw=1.5, alpha=0.7)
        ax.plot([yB, yP], [xB, xP], ":",  color=kol, lw=1.5, alpha=0.7)
        ax.plot(yP, xP, "*", color=kol, ms=18, zorder=6)
        ax.text(yP + margin * 0.04, xP,
                f"P{i+1}\n({xP:.2f}, {yP:.2f})",
                fontsize=8, color=kol, fontweight="bold")

    ax.set_xlabel("Y [m]")
    ax.set_ylabel("X [m]")
    ax.set_title("Schemat wcięcia liniowego", fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def rysuj_wielobok(punkty):
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_facecolor("#f8fafc")
    ax.set_aspect("equal")

    ys = [p[1] for p in punkty]
    xs = [p[0] for p in punkty]
    margin = max(max(xs) - min(xs), max(ys) - min(ys)) * 0.15

    # zamknięty wielobok
    xs_closed = xs + [xs[0]]
    ys_closed = ys + [ys[0]]
    ax.fill(ys_closed, xs_closed, alpha=0.25, color="#3b82f6")
    ax.plot(ys_closed, xs_closed, "b-o", lw=2, ms=7, zorder=4)

    # etykiety wierzchołków
    for i, (x, y) in enumerate(zip(xs, ys)):
        ax.text(y + margin * 0.06, x + margin * 0.06,
                f"P{i+1}\n({x:.1f},{y:.1f})",
                fontsize=7.5, color="#1e3a5f")

    ax.set_xlabel("Y [m]")
    ax.set_ylabel("X [m]")
    ax.set_title("Wielobok – wizualizacja", fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def rysuj_strefy_2000():
    fig, ax = plt.subplots(figsize=(5, 6))
    ax.set_facecolor("#e8f4f8")
    ax.set_xlim(13.5, 25); ax.set_ylim(48.5, 55.5)

    strefy_info = [
        ("Strefa 5\n(L=15°E)", 13.5, 16.5, "#fff3cd"),
        ("Strefa 6\n(L=18°E)", 16.5, 19.5, "#d4edda"),
        ("Strefa 7\n(L=21°E)", 19.5, 22.5, "#cce5ff"),
        ("Strefa 8\n(L=24°E)", 22.5, 25.0, "#f8d7da"),
    ]
    for nazwa, x1, x2, kol in strefy_info:
        ax.axvspan(x1, x2, alpha=0.65, color=kol)
        ax.text((x1 + x2) / 2, 55.2, nazwa,
                ha="center", fontsize=8, fontweight="bold")
        ax.axvline(x2, color="#888", lw=0.8, ls="--")

    ax.set_xlabel("Długość geograficzna [°E]", fontsize=9)
    ax.set_ylabel("Szerokość geograficzna [°N]", fontsize=9)
    ax.set_title("Układ PUWG 2000 – strefy", fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════
# NAGŁÓWEK APLIKACJI
# ═══════════════════════════════════════════════════════════════

st.title("📐 Kalkulator Geodezyjny")
st.caption("Politechnika Morska w Szczecinie | Geoinformatyka | PiG 2025/26")
st.info(
    "💡 Otwórz panel **≡** (lewy górny róg) aby wyświetlić instrukcję obsługi.",
    icon="ℹ️"
)
st.divider()

# ─── Wybór funkcji ────────────────────────────────────────────
funkcja = st.selectbox(
    "Wybierz funkcję geodezyjną:",
    [
        "📏 Odległość między punktami",
        "🧭 Azymut kierunku",
        "📐 Pole powierzchni (wzór Gaussa)",
        "➡️ Biegunowe → Prostokątne",
        "⬅️ Prostokątne → Biegunowe",
        "📍 Wcięcie liniowe",
        "🗺️ Przeliczanie układów współrzędnych",
    ],
    help="Wybierz jedną z 7 dostępnych funkcji geodezyjnych"
)
st.divider()


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 1 – ODLEGŁOŚĆ
# ═══════════════════════════════════════════════════════════════
if funkcja.startswith("📏"):
    st.subheader("📏 Odległość między punktami")

    c1, c2 = st.columns(2)
    x1 = c1.number_input("X₁ [m]", value=100.0, format="%.4f",
                          help="Współrzędna X punktu 1")
    y1 = c2.number_input("Y₁ [m]", value=200.0, format="%.4f",
                          help="Współrzędna Y punktu 1")
    x2 = c1.number_input("X₂ [m]", value=250.0, format="%.4f",
                          help="Współrzędna X punktu 2")
    y2 = c2.number_input("Y₂ [m]", value=500.0, format="%.4f",
                          help="Współrzędna Y punktu 2")

    if st.button("🔢 Oblicz odległość", type="primary",
                 use_container_width=True):
        d = odleglosc(x1, y1, x2, y2)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        st.success(f"### d = {d:.4f} m")
        c1, c2, c3 = st.columns(3)
        c1.metric("Odległość d", f"{d:.4f} m")
        c2.metric("Przyrost ΔX", f"{dx:.4f} m")
        c3.metric("Przyrost ΔY", f"{dy:.4f} m")


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 2 – AZYMUT
# ═══════════════════════════════════════════════════════════════
elif funkcja.startswith("🧭"):
    st.subheader("🧭 Azymut kierunku")

    c1, c2 = st.columns(2)
    x1 = c1.number_input("X₁ [m]", value=100.0, format="%.4f",
                          help="Punkt początkowy – współrzędna X")
    y1 = c2.number_input("Y₁ [m]", value=200.0, format="%.4f",
                          help="Punkt początkowy – współrzędna Y")
    x2 = c1.number_input("X₂ [m]", value=250.0, format="%.4f",
                          help="Punkt końcowy – współrzędna X")
    y2 = c2.number_input("Y₂ [m]", value=500.0, format="%.4f",
                          help="Punkt końcowy – współrzędna Y")

    if st.button("🔢 Oblicz azymut", type="primary",
                 use_container_width=True):
        try:
            az = azymut(x1, y1, x2, y2)
            d  = odleglosc(x1, y1, x2, y2)
            st.success(f"### A = {dms(az)}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Azymut [°]",   f"{az:.6f}°")
            c2.metric("Azymut D°M'S\"", dms(az))
            c3.metric("Odległość",     f"{d:.4f} m")
            with st.expander("📌 Schemat geometryczny"):
                st.pyplot(rysuj_azymut(x1, y1, x2, y2, az))
        except ValueError as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 3 – POLE GAUSSA
# ═══════════════════════════════════════════════════════════════
elif funkcja.startswith("📐"):
    st.subheader("📐 Pole powierzchni wieloboku (wzór Gaussa)")
    st.caption("Wpisz wierzchołki – każdy w osobnej linii jako: X Y")

    tekst = st.text_area(
        "Wierzchołki wieloboku:",
        "100 200\n150 350\n300 300\n250 150",
        height=160,
        help="Format: X spacja Y, jeden punkt na linię, min. 3 punkty"
    )

    if st.button("🔢 Oblicz pole", type="primary",
                 use_container_width=True):
        try:
            pts = []
            for linia in tekst.strip().splitlines():
                vals = linia.split()
                if len(vals) >= 2:
                    pts.append([float(vals[0]), float(vals[1])])
            p = pole_gaussa(pts)
            st.success(f"### P = {p:.4f} m²")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pole [m²]",   f"{p:.4f} m²")
            c2.metric("Pole [ha]",   f"{p/10000:.6f} ha")
            c3.metric("Liczba pkt.", str(len(pts)))
            with st.expander("📌 Wizualizacja wieloboku"):
                st.pyplot(rysuj_wielobok(pts))
        except ValueError as e:
            st.error(str(e))
        except Exception:
            st.error("Błąd danych. Sprawdź format: X spacja Y, jeden punkt na linię.")


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 4 – BIEGUNOWE → PROSTOKĄTNE
# ═══════════════════════════════════════════════════════════════
elif funkcja.startswith("➡️"):
    st.subheader("➡️ Biegunowe → Prostokątne")
    st.caption("Zamiana (d, A) na (ΔX, ΔY)")

    c1, c2 = st.columns(2)
    d  = c1.number_input("Odległość d [m]", value=150.0, format="%.4f",
                          help="Długość wektora w metrach")
    az = c2.number_input("Azymut A [°]",    value=45.0,  format="%.6f",
                          help="Azymut w stopniach dziesiętnych (0–360)")

    if st.button("🔢 Oblicz", type="primary", use_container_width=True):
        dx, dy = biegunowe_na_prostokatne(d, az)
        st.success(f"ΔX = {dx:.4f} m   |   ΔY = {dy:.4f} m")
        c1, c2 = st.columns(2)
        c1.metric("Przyrost ΔX [m]", f"{dx:.4f}")
        c2.metric("Przyrost ΔY [m]", f"{dy:.4f}")


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 5 – PROSTOKĄTNE → BIEGUNOWE
# ═══════════════════════════════════════════════════════════════
elif funkcja.startswith("⬅️"):
    st.subheader("⬅️ Prostokątne → Biegunowe")
    st.caption("Zamiana (ΔX, ΔY) na (d, A)")

    c1, c2 = st.columns(2)
    dx = c1.number_input("Przyrost ΔX [m]", value=106.066, format="%.4f",
                          help="Różnica współrzędnych X: X₂ − X₁")
    dy = c2.number_input("Przyrost ΔY [m]", value=106.066, format="%.4f",
                          help="Różnica współrzędnych Y: Y₂ − Y₁")

    if st.button("🔢 Oblicz", type="primary", use_container_width=True):
        try:
            d, az = prostokatne_na_biegunowe(dx, dy)
            st.success(f"d = {d:.4f} m   |   A = {dms(az)}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Odległość d", f"{d:.4f} m")
            c2.metric("Azymut [°]",  f"{az:.6f}°")
            c3.metric("A [D°M'S\"]", dms(az))
        except ValueError as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 6 – WCIĘCIE LINIOWE
# ═══════════════════════════════════════════════════════════════
elif funkcja.startswith("📍"):
    st.subheader("📍 Wcięcie liniowe")
    st.caption("Wyznaczenie punktu P z dwóch punktów osnowy A, B i odległości")

    c1, c2 = st.columns(2)
    xA = c1.number_input("XA [m]", value=0.0,   format="%.4f",
                          help="Współrzędna X punktu osnowy A")
    yA = c2.number_input("YA [m]", value=0.0,   format="%.4f",
                          help="Współrzędna Y punktu osnowy A")
    xB = c1.number_input("XB [m]", value=100.0, format="%.4f",
                          help="Współrzędna X punktu osnowy B")
    yB = c2.number_input("YB [m]", value=0.0,   format="%.4f",
                          help="Współrzędna Y punktu osnowy B")
    dA = c1.number_input("dA – odległość A→P [m]", value=70.0, format="%.4f",
                          help="Odległość zmierzona od punktu A do punktu P")
    dB = c2.number_input("dB – odległość B→P [m]", value=60.0, format="%.4f",
                          help="Odległość zmierzona od punktu B do punktu P")

    if st.button("🔢 Oblicz wcięcie", type="primary",
                 use_container_width=True):
        try:
            rozw = wciecie_liniowe(xA, yA, xB, yB, dA, dB)
            st.success(
                f"**Rozwiązanie 1:**  X = {rozw[0][0]:.4f} m,  Y = {rozw[0][1]:.4f} m"
            )
            st.warning(
                f"**Rozwiązanie 2:**  X = {rozw[1][0]:.4f} m,  Y = {rozw[1][1]:.4f} m"
            )
            st.caption(
                "Wybierz rozwiązanie zgodne z lokalizacją mierzonego punktu w terenie."
            )
            with st.expander("📌 Schemat geometryczny wcięcia"):
                st.pyplot(rysuj_wciecie(xA, yA, xB, yB, dA, dB, rozw))
        except ValueError as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════════════════
# FUNKCJA 7 – PRZELICZANIE UKŁADÓW + MAPA OSM
# ═══════════════════════════════════════════════════════════════
elif funkcja.startswith("🗺️"):
    st.subheader("🗺️ Przeliczanie układów współrzędnych")

    c1, c2 = st.columns(2)
    uklad_z  = c1.selectbox("Z układu:",  list(UKLADY.keys()), index=0)
    uklad_na = c2.selectbox("Na układ:", list(UKLADY.keys()), index=1)

    # Podpowiedź zakresu
    if "WGS84" in uklad_z:
        st.info(
            "📌 Dla WGS84 podaj współrzędne **geograficzne** w stopniach dziesiętnych.\n\n"
            "Polska: szerokość φ = 49–55°N, długość λ = 14–24°E"
        )
        c1, c2 = st.columns(2)
        x_in = c1.number_input(
            "Szerokość geogr. φ [°N]", value=52.2297,
            format="%.6f", min_value=49.0, max_value=55.0,
            help="Np. Warszawa: 52.2297")
        y_in = c2.number_input(
            "Długość geogr. λ [°E]",   value=21.0122,
            format="%.6f", min_value=14.0, max_value=25.0,
            help="Np. Warszawa: 21.0122")
    else:
        st.info("📌 Podaj współrzędne w **metrach** (układ płaski prostokątny).")
        c1, c2 = st.columns(2)
        x_in = c1.number_input("X [m]", value=479952.0, format="%.3f",
                                help="Współrzędna X w metrach")
        y_in = c2.number_input("Y [m]", value=637099.0, format="%.3f",
                                help="Współrzędna Y w metrach")

    if st.button("🔢 Przelicz", type="primary", use_container_width=True):
        if uklad_z == uklad_na:
            st.warning("Wybrane układy są identyczne – brak przeliczenia.")
        else:
            try:
                x_out, y_out = przelicz_uklad(x_in, y_in, uklad_z, uklad_na)
                st.success(f"**{uklad_z}  →  {uklad_na}**")

                if "WGS84" in uklad_na:
                    c1, c2 = st.columns(2)
                    c1.metric("Szerokość φ [°N]", f"{x_out:.6f}°")
                    c2.metric("Długość λ [°E]",   f"{y_out:.6f}°")
                    st.info(f"Współrzędne GPS:  **{x_out:.6f} N,  {y_out:.6f} E**")
                    lat, lon = x_out, y_out
                else:
                    c1, c2 = st.columns(2)
                    c1.metric("X [m]", f"{x_out:.3f}")
                    c2.metric("Y [m]", f"{y_out:.3f}")
                    # przelicz na WGS84 do mapy
                    t_wgs = Transformer.from_crs(
                        UKLADY[uklad_na], "EPSG:4326", always_xy=False
                    )
                    lat, lon = t_wgs.transform(x_out, y_out)

                # ── MAPA OSM (folium) ─────────────────────────
                st.subheader("📍 Lokalizacja punktu na mapie")
                m = folium.Map(
                    location=[lat, lon],
                    zoom_start=14,
                    tiles="OpenStreetMap"
                )
                folium.Marker(
                    location=[lat, lon],
                    popup=(
                        f"<b>Wyznaczony punkt</b><br>"
                        f"φ = {lat:.6f}°N<br>"
                        f"λ = {lon:.6f}°E<br>"
                        f"Układ: {uklad_na}"
                    ),
                    icon=folium.Icon(color="red", icon="crosshairs",
                                     prefix="fa")
                ).add_to(m)
                folium.Circle(
                    location=[lat, lon],
                    radius=50,
                    color="#3b82f6",
                    fill=True, fill_opacity=0.15
                ).add_to(m)
                st_folium(m, width=None, height=380)

                # schemat stref
                with st.expander("ℹ️ Schemat stref PUWG 2000"):
                    st.pyplot(rysuj_strefy_2000())

            except Exception as e:
                st.error(f"Błąd przeliczenia: {e}")
