import streamlit as st
import pandas as pd
import streamlit_shortcuts as ss
from pathlib import Path

# Constants
DATA_PATH = Path(__file__).parent.parent.parent / "dico-fr.parquet"

def load_and_sample_words():
    """Load the parquet file and sample N_WORDS words."""
    df = pd.read_parquet(DATA_PATH)
    df = df[~df.optional_category]
    return df.sample(frac=1).reset_index(drop=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'words_df' not in st.session_state:
        st.session_state.words_df = load_and_sample_words()
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'actively_known_words' not in st.session_state:
        st.session_state.actively_known_words = []
    if 'passively_known_words' not in st.session_state:
        st.session_state.passively_known_words = []
    if 'unknown_words' not in st.session_state:
        st.session_state.unknown_words = []
    if 'keep_optional' not in st.session_state:
        st.session_state.keep_optional = False

def main():
    st.set_page_config(page_title="Estimation de la couverture du dictionnaire", layout="centered")
    
    # Initialize session state
    initialize_session_state()
    
    # Title
    st.title("Estimation de la couverture du dictionnaire")
    st.markdown("""
    Cette application permet d'estimer la couverture du dictionnaire en français.
    Elle permet de classer les mots selon votre niveau de connaissance :
    - **Inconnu** : Vous ne connaissez pas ce mot
    - **Connu passivement** : Vous reconnaissez ce mot mais ne l'utilisez pas activement
    - **Connu activement** : Vous pouvez utiliser ce mot dans vos conversations et écrits
    """)
    
    
    # Display current word
    if st.session_state.current_index < len(st.session_state.words_df):
        current_word = st.session_state.words_df.iloc[st.session_state.current_index]
        
        # Word card
        st.markdown("---")
        st.markdown(f"# {current_word['word']}")
        st.markdown(f"*{current_word['pos_title']}*")
        
        # Buttons for classification
        col1, col2, col3 = st.columns(3)
        with col1:
            if ss.shortcut_button("❌ Inconnu", use_container_width=True, shortcut="arrowleft", hint=False):
                st.session_state.unknown_words.append(current_word)
                st.session_state.current_index += 1
                st.rerun()
        
        with col2:
            if ss.shortcut_button("👁️ Connu passivement", use_container_width=True, shortcut="arrowdown", hint=False):
                st.session_state.passively_known_words.append(current_word)
                st.session_state.current_index += 1
                st.rerun()
        
        with col3:
            if ss.shortcut_button("✅ Connu activement", use_container_width=True, shortcut="arrowright", hint=False):
                st.session_state.actively_known_words.append(current_word)
                st.session_state.current_index += 1
                st.rerun()
        
        # Keyboard shortcuts
        st.markdown("**Raccourcis clavier:** ⬅️ *inconnu* - ⬇️ *connu passivement* - ➡️ *connu activement*" )
        
    if n_tot_words:=(len(st.session_state.actively_known_words) + len(st.session_state.passively_known_words) + len(st.session_state.unknown_words)) > 0:
        # Show results
        n_actively_known = len(st.session_state.actively_known_words)
        n_passively_known = len(st.session_state.passively_known_words)
        n_unknown = len(st.session_state.unknown_words)
        n_tot_words = n_actively_known + n_passively_known + n_unknown
        
        # Calculate fractions
        actively_known_frac = n_actively_known / n_tot_words
        passively_known_frac = n_passively_known / n_tot_words
        total_known_frac = (n_actively_known + n_passively_known) / n_tot_words
        
        # Display metrics
        cols = st.columns(3)
        with cols[0]:
            st.metric(label="Connus activement", value=f"{n_actively_known} / {n_tot_words}")
        with cols[1]:
            st.metric(label="Connus passivement", value=f"{n_passively_known} / {n_tot_words}")
        with cols[2]:
            st.metric(label="Inconnus", value=f"{n_unknown} / {n_tot_words}")
        
        # Estimations
        st.markdown("### Estimations du vocabulaire total")
        est_cols = st.columns(2)
        with est_cols[0]:
            st.metric(
                label="Mots connus activement (estimation)", 
                value=f"{int(actively_known_frac * len(st.session_state.words_df)):,}"
            )
        with est_cols[1]:
            st.metric(
                label="Mots connus au total (estimation)", 
                value=f"{int(total_known_frac * len(st.session_state.words_df)):,}"
            )
        
        st.success(f"🎉 Vous avez terminé avec {n_actively_known} mots connus activement, {n_passively_known} mots connus passivement et {n_unknown} mots inconnus sur {n_tot_words} mots évalués.")
        
if __name__ == "__main__":
    main()
