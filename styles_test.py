import streamlit as st
import pandas as pd

# Set page config for a cleaner design environment
st.set_page_config(page_title="Custom Operator Card Design", layout="wide")

st.title("Operator Card Design Playground")

# Custom CSS for the operator card
st.markdown("""
    <style>
    /* Main Card Container */
    .op-card {
        background-color: #ffffff;
        padding: 0px;
    }
    
    /* Operator Title */
    .op-title {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
    }
    
    /* Labels (Total, Takeoff, Landing) */
    .op-label {
        font-size: 10px !important;
        color: #6b7280 !important;
        text-transform: uppercase !important;
        margin-bottom: 0px !important;
        font-weight: 500 !important;
    }
    
    /* Value for Total */
    .op-value-total {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #000000 !important;
        margin-top: -5px !important;
    }
    
    /* Value for Takeoff/Landing */
    .op-value-sub {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #000000 !important;
        margin-top: -5px !important;
    }
    
    /* Alignment for containers */
    .stElementContainer div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 0px;
    }
    </style>
    """, unsafe_allow_html=True)

cols = st.columns([1,2])

with cols[0]:
    st.write("Styled Operator Card")
    # Using a container for the outer border
    with st.container(border=True):
        # Operator Title
        st.markdown('<p class="op-title">OPERATOR TITLE</p>', unsafe_allow_html=True)
        
        # Total Section
        with st.container(border=True):
            st.markdown('<p class="op-label">TOTAL</p>', unsafe_allow_html=True)
            st.markdown('<p class="op-value-total">100</p>', unsafe_allow_html=True)
            
        # Breakdown Section
        breakdown_cols = st.columns(2)
        
        with breakdown_cols[0]:
            with st.container(border=True):
                st.markdown('<p class="op-label">TAKEOFF</p>', unsafe_allow_html=True)
                st.markdown('<p class="op-value-sub">100</p>', unsafe_allow_html=True)
            
        with breakdown_cols[1]:
            with st.container(border=True):
                st.markdown('<p class="op-label">LANDING</p>', unsafe_allow_html=True)
                st.markdown('<p class="op-value-sub">100</p>', unsafe_allow_html=True)
    st.write("Styled Operator Card")
    # Using a container for the outer border
    with st.container(border=True):
        # Operator Title
        st.markdown('<p class="op-title">OPERATOR TITLE</p>', unsafe_allow_html=True)
        
        # Total Section
        with st.container(border=True):
            st.markdown('<p class="op-label">TOTAL</p>', unsafe_allow_html=True)
            st.markdown('<p class="op-value-total">100</p>', unsafe_allow_html=True)
            
        # Breakdown Section
        breakdown_cols = st.columns(2)
        
        with breakdown_cols[0]:
            with st.container(border=True):
                st.markdown('<p class="op-label">TAKEOFF</p>', unsafe_allow_html=True)
                st.markdown('<p class="op-value-sub">100</p>', unsafe_allow_html=True)
            
        with breakdown_cols[1]:
            with st.container(border=True):
                st.markdown('<p class="op-label">LANDING</p>', unsafe_allow_html=True)
                st.markdown('<p class="op-value-sub">100</p>', unsafe_allow_html=True)

with cols[1]:
    st.write("Rest of the dashboard")