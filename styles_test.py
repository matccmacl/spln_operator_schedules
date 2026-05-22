import streamlit as st

st.set_page_config(page_title="Custom Operator Card Design", layout="wide")
st.title("Operator Card Design Playground")

st.markdown("""
    <style>
    .op-title {
        font-size: 16px !important;
        font-weight: 500 !important;
        color: #1f2937 !important;
        margin-bottom: 8px !important;
        text-transform: uppercase;
    }
    .op-label {
        font-size: 10px !important;
        color: #6b7280 !important;
        text-transform: uppercase !important;
        margin-bottom: 0px !important;
        font-weight: 700 !important;
    }
    .op-value-total {
        font-size: 24px !important;
        font-weight: 500 !important;
        color: #000000 !important;
        margin-top: -5px !important;
        margin-bottom: 0px !important;
    }
    .op-value-sub {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #000000 !important;
        margin-top: -5px !important;
        margin-bottom: 0px !important;
    }
    .stElementContainer div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 0px;
    }
    /* Flex row: always side-by-side, never collapses on mobile */
    .op-breakdown-row {
        display: flex;
        gap: 8px;
        margin-top: 4px;
    }
    .op-breakdown-cell {
        flex: 1 1 0;
        min-width: 0;
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 16px;
    }
    </style>
    """, unsafe_allow_html=True)


def operator_card(title, total, takeoffs, landings):
    """Renders an operator card. Breakdown row uses HTML flex to stay side-by-side on mobile."""
    with st.container(border=True):
        st.markdown(f'<p class="op-title">{title}</p>', unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown('<p class="op-label">TOTAL</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="op-value-total">{total:,}</p>', unsafe_allow_html=True)

        st.markdown(f"""
            <div class="op-breakdown-row">
                <div class="op-breakdown-cell">
                    <p class="op-label">TAKEOFF</p>
                    <p class="op-value-sub">{takeoffs:,}</p>
                </div>
                <div class="op-breakdown-cell">
                    <p class="op-label">LANDING</p>
                    <p class="op-value-sub">{landings:,}</p>
                </div>
            </div>
        """, unsafe_allow_html=True)


cols = st.columns([1, 2])

with cols[0]:
    operator_card("OPERATOR TITLE", 2000, 1000, 1000)
    operator_card("OPERATOR TITLE", 100, 50, 50)

with cols[1]:
    st.write("Rest of the dashboard")