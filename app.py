import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Aliasing and DFT Visualizer",
    page_icon="📡",
    layout="wide"
)

# --- Sidebar (Controls) ---
st.sidebar.title("Parameters")

# Default settings as in the task
dc_offset = st.sidebar.slider(
    "DC Offset (V_DC)", -5.0, 5.0, 0.0, 0.1,
    help="Constant voltage offset (corresponds to the 0 Hz bin)."
)
amplitude = st.sidebar.slider(
    "Amplitude (A)", 0.0, 10.0, 5.0, 0.1,
    help="Amplitude of the alternating (AC) signal."
)
signal_shape = st.sidebar.selectbox(
    "Signal Shape",
    ("sine", "square", "triangle", "sawtooth"),
    index=0,
    help="Waveform of the input signal."
)
signal_freq = st.sidebar.slider(
    "Signal Frequency (f_sig)", 1, 2000, 120, 1,
    help="Actual frequency of the analog signal."
)
sampling_freq = st.sidebar.slider(
    "Sampling Frequency (f_s)", 1, 2000, 100, 1,
    help="How often the signal is measured (sampled)."
)

# --- Main Panel (Visualizations) ---
st.title("Interactive Signal and DFT Visualizer")
st.markdown("""
Experiment with signal and sampling parameters to see 
how DC offset and aliasing affect the frequency spectrum (DFT result).
""")

# --- Helper Functions ---
def get_signal_value(t, shape, freq, amp, dc):
    """Calculates the signal value at a given time point."""
    omega = 2 * np.pi * freq
    value = 0
    if shape == 'sine':
        value = np.sin(omega * t)
    elif shape == 'square':
        value = np.sign(np.sin(omega * t))
    elif shape == 'triangle':
        # Approximation of a triangle signal
        value = (2 / np.pi) * np.arcsin(np.sin(omega * t))
    elif shape == 'sawtooth':
        # Approximation of a sawtooth signal
        value = 2 * (t * freq - np.floor(0.5 + t * freq))
    
    return dc + amp * value

# --- Plot 1: Time Domain ---
st.header("Signal Plot in Time Domain")

# Time axis settings
T_DISPLAY = 0.1  
V_MAX = 15       # Maximum voltage range +/- 15V
N_ANALOG = 10000  # Number of points for a "smooth" signal

# Time and value vectors
t_analog = np.linspace(0, T_DISPLAY, N_ANALOG) # Simulation of a continuous signal
v_analog = get_signal_value(t_analog, signal_shape, signal_freq, amplitude, dc_offset)

# Digital samples
dt_sample = 1 / sampling_freq # sampling period
n_samples = int(T_DISPLAY * sampling_freq) + 1
t_sample = np.linspace(0, T_DISPLAY, n_samples) # Digital sample times
v_sample = get_signal_value(t_sample, signal_shape, signal_freq, amplitude, dc_offset)

# Create Plotly figure
fig_time = go.Figure()

# 1. Analog signal (continuous)
fig_time.add_trace(go.Scatter(
    x=t_analog, 
    y=v_analog, 
    mode='lines', 
    name='Analog Signal',
    line=dict(color='blue', width=2)
))

# 2. Digital Samples
fig_time.add_trace(go.Scatter(
    x=t_sample, 
    y=v_sample, 
    mode='markers', 
    name='Digital Samples',
    marker=dict(color='yellow', size=8, symbol='circle')
))

# 3. DC Offset Line
fig_time.add_shape(
    type='line',
    x0=0, y0=dc_offset, x1=T_DISPLAY, y1=dc_offset,
    line=dict(color='red', width=2, dash='dash'),
    name='V_DC'
)

# Layout settings
fig_time.update_layout(
    xaxis_title='Time (s)',
    yaxis_title='Voltage (V)',
    yaxis_range=[-V_MAX, V_MAX],
    plot_bgcolor='#1f2937',  # bg-gray-800
    paper_bgcolor='#1f2937', # bg-gray-800
    font_color='#d1d5db'     # text-gray-300
)

st.plotly_chart(fig_time, use_container_width=True)


# --- Plot 2: Frequency Domain ---
st.header("Frequency Spectrum (Ideal DFT)")

if sampling_freq <= 0:
    st.error("Sampling frequency must be greater than 0.")
else:
    f_nyquist = sampling_freq / 2
    
    if f_nyquist == 0:
        st.error("Nyquist frequency is 0, cannot draw the spectrum.")
    else:
        # Calculating the alias
        is_aliased = False
        
        # We use modulo to "wrap" the frequency
        f_alias = signal_freq % sampling_freq
        
        # Mirror reflection from the Nyquist frequency
        if f_alias > f_nyquist:
            f_alias = sampling_freq - f_alias
            
        if abs(f_alias - signal_freq) > 0.01: # Simple test for aliasing
             is_aliased = True

        # Create plot (using bar for "bins")
        fig_freq = go.Figure()

        # 1. DC Bin (0 Hz)
        if dc_offset != 0:
            fig_freq.add_trace(go.Bar(
                x=[0],
                y=[dc_offset],
                name=f'DC Component ({dc_offset:.1f} V)', # Corrected unit to V
                marker_color='#34d399', # emerald-400
                width=max(1, f_nyquist * 0.02) # Bar width
            ))

        # 2. AC Bin (signal or its alias)
        if amplitude > 0:
            fig_freq.add_trace(go.Bar(
                x=[f_alias],
                y=[amplitude],
                name=f'AC Signal ({f_alias:.1f} Hz)',
                marker_color='#60a5fa', # blue-400
                width=max(1, f_nyquist * 0.02)
            ))

        # 3. Nyquist Line
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

        # Layout settings
        fig_freq.update_layout(
            xaxis_title='Frequency (Hz)',
            yaxis_title='Amplitude (V)',
            xaxis_range=[-0.5, f_nyquist + 5], # Show a bit beyond Nyquist
            yaxis_range=[0, V_MAX],
            plot_bgcolor='#1f2937',
            paper_bgcolor='#1f2937',
            font_color='#d1d5db',
            showlegend=True
        )
        
        st.plotly_chart(fig_freq, use_container_width=True)

        # Aliasing message
        if is_aliased and amplitude > 0:
            st.warning(f"**Aliasing Occurred!** A signal with frequency {signal_freq} Hz is visible as a bin at **{f_alias:.1f} Hz**.")
        elif amplitude > 0:
            st.success(f"Sampling correct. The {signal_freq} Hz signal is displayed correctly.")