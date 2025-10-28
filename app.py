import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- Konfiguracja strony ---
st.set_page_config(
    page_title="Wizualizator Aliasingu i DFT",
    page_icon="📡",
    layout="wide"
)

# --- Panel Boczny (Kontrolki) ---
st.sidebar.title("Parametry")

# Ustawienia domyślne jak w zadaniu
dc_offset = st.sidebar.slider(
    "Składowa Stała (V_DC)", -5.0, 5.0, 0.0, 0.1,
    help="Stałe przesunięcie napięcia (odpowiada prążkowi 0 Hz)."
)
amplitude = st.sidebar.slider(
    "Amplituda (A)", 0.0, 10.0, 5.0, 0.1,
    help="Amplituda sygnału zmiennego (AC)."
)
signal_shape = st.sidebar.selectbox(
    "Kształt Sygnału",
    ("sine", "square", "triangle", "sawtooth"),
    index=0,
    help="Forma fali sygnału wejściowego."
)
signal_freq = st.sidebar.slider(
    "Częstotliwość Sygnału (f_sig)", 1, 2000, 120, 1,
    help="Rzeczywista częstotliwość sygnału analogowego."
)
sampling_freq = st.sidebar.slider(
    "Częstotliwość Próbkowania (f_s)", 1, 2000, 100, 1,
    help="Jak często sygnał jest mierzony (próbkowany)."
)

# --- Główny Panel Wizualizacje) ---
st.title("Interaktywny Wizualizator Sygnałów i DFT")
st.markdown("""
Eksperymentuj z parametrami sygnału i próbkowania, aby zobaczyć, 
jak składowa stała i aliasing wpływają na widmo częstotliwości (wynik DFT).
""")

# --- Funkcje Pomocnicze ---
def get_signal_value(t, shape, freq, amp, dc):
    """Oblicza wartość sygnału w danym punkcie czasu."""
    omega = 2 * np.pi * freq
    value = 0
    if shape == 'sine':
        value = np.sin(omega * t)
    elif shape == 'square':
        value = np.sign(np.sin(omega * t))
    elif shape == 'triangle':
        # Aproksymacja sygnału trójkątnego
        value = (2 / np.pi) * np.arcsin(np.sin(omega * t))
    elif shape == 'sawtooth':
        # Aproksymacja sygnału piłokształtnego
        value = 2 * (t * freq - np.floor(0.5 + t * freq))
    
    return dc + amp * value

# --- Wykres 1: Dziedzina Czasu ---
st.header("Wykres sygnału w dziedzinie czasu")

# Ustawienia osi czasu
T_DISPLAY = 0.1  
V_MAX = 15       # Maksymalny zakres napięcia +/- 15V
N_ANALOG = 10000  # Liczba punktów dla "gładkiego" sygnału

# Wektory czasu i wartości
t_analog = np.linspace(0, T_DISPLAY, N_ANALOG) # Symulacja sygnału ciągłęgo
v_analog = get_signal_value(t_analog, signal_shape, signal_freq, amplitude, dc_offset)

# Próbki cyfrowe
dt_sample = 1 / sampling_freq # okres próbkowania
n_samples = int(T_DISPLAY * sampling_freq) + 1
t_sample = np.linspace(0, T_DISPLAY, n_samples) # Czasy próbek cyfrowych
v_sample = get_signal_value(t_sample, signal_shape, signal_freq, amplitude, dc_offset)

# Tworzenie wykresu Plotly
fig_time = go.Figure()

# 1. Sygnał analogowy (ciągły)
fig_time.add_trace(go.Scatter(
    x=t_analog, 
    y=v_analog, 
    mode='lines', 
    name='Sygnał analogowy',
    line=dict(color='blue', width=2)
))

# 2. Próbki cyfrowe
fig_time.add_trace(go.Scatter(
    x=t_sample, 
    y=v_sample, 
    mode='markers', 
    name='Próbki cyfrowe',
    marker=dict(color='yellow', size=8, symbol='circle')
))

# 3. Linia składowej stałej (DC)
fig_time.add_shape(
    type='line',
    x0=0, y0=dc_offset, x1=T_DISPLAY, y1=dc_offset,
    line=dict(color='red', width=2, dash='dash'),
    name='V_DC'
)

# Ustawienia layoutu
fig_time.update_layout(
    xaxis_title='Czas (s)',
    yaxis_title='Napięcie (V)',
    yaxis_range=[-V_MAX, V_MAX],
    plot_bgcolor='#1f2937',  # bg-gray-800
    paper_bgcolor='#1f2937', # bg-gray-800
    font_color='#d1d5db'     # text-gray-300
)

st.plotly_chart(fig_time, use_container_width=True)


# --- Wykres 2: Dziedzina Częstotliwości ---
st.header("Widmo Częstotliwości (Idealne DFT)")

if sampling_freq <= 0:
    st.error("Częstotliwość próbkowania musi być większa od 0.")
else:
    f_nyquist = sampling_freq / 2
    
    if f_nyquist == 0:
        st.error("Częstotliwość Nyquista wynosi 0, nie można narysować widma.")
    else:
        # Obliczanie aliasu
        is_aliased = False
        
        # Używamy modulo do "zawinięcia" częstotliwości
        f_alias = signal_freq % sampling_freq
        
        # Odbicie lustrzane od częstotliwości Nyquista
        if f_alias > f_nyquist:
            f_alias = sampling_freq - f_alias
            
        if abs(f_alias - signal_freq) > 0.01: # Prosty test na aliasing
             is_aliased = True

        # Tworzenie wykresu (używamy słupkowego dla "prążków")
        fig_freq = go.Figure()

        # 1. Prążek DC (0 Hz)
        if dc_offset != 0:
            fig_freq.add_trace(go.Bar(
                x=[0],
                y=[dc_offset],
                name=f'Składowa Stała (${dc_offset:.1f} Hz)',
                marker_color='#34d399', # emerald-400
                width=max(1, f_nyquist * 0.02) # Szerokość słupka
            ))

        # 2. Prążek AC (sygnału lub jego aliasu)
        if amplitude > 0:
            fig_freq.add_trace(go.Bar(
                x=[f_alias],
                y=[amplitude],
                name=f'Sygnał AC ({f_alias:.1f} Hz)',
                marker_color='#60a5fa', # blue-400
                width=max(1, f_nyquist * 0.02)
            ))

        # 3. Linia Nyquista
        fig_freq.add_shape(
            type='line',
            x0=f_nyquist, y0=0, x1=f_nyquist, y1=max(amplitude, dc_offset, 1) ,
            line=dict(color='red', width=2, dash='dash'),
            name='f_Nyquist'
        )
        fig_freq.add_annotation(
            x=f_nyquist, y=max(amplitude, dc_offset, 1) * 1.1,
            text=f'f_N = {f_nyquist:.1f} Hz',
            showarrow=False, xshift=10, align="left",
            font=dict(color='red')
        )

        # Ustawienia layoutu
        fig_freq.update_layout(
            xaxis_title='Częstotliwość (Hz)',
            yaxis_title='Amplituda (V)',
            xaxis_range=[-0.5, f_nyquist + 5], # Pokazujemy trochę poza Nyquista
            yaxis_range=[0, V_MAX],
            plot_bgcolor='#1f2937',
            paper_bgcolor='#1f2937',
            font_color='#d1d5db',
            showlegend=True
        )
        
        st.plotly_chart(fig_freq, use_container_width=True)

        # Komunikat o aliasingu
        if is_aliased and amplitude > 0:
            st.warning(f"**Wystąpił Aliasing!** Sygnał o częstotliwości {signal_freq} Hz jest widoczny jako prążek **{f_alias:.1f} Hz**.")
        elif amplitude > 0:
            st.success(f"Próbkowanie poprawne. Sygnał {signal_freq} Hz jest widoczny poprawnie.")
