import streamlit as st
import pandas as pd
import streamlit_shortcuts as ss

# Constants
DATA_PATH = "/Users/francois.weber/perso/tmp/dico-fr.parquet"

def load_and_sample_words():
    """Load the parquet file and sample N_WORDS words."""
    df = pd.read_parquet(DATA_PATH)
    return df.sample(frac=1).reset_index(drop=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'words_df' not in st.session_state:
        st.session_state.words_df = load_and_sample_words()
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'known_words' not in st.session_state:
        st.session_state.known_words = []
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
    Elle permet de sélectionner les mots que vous connaissez et ceux que vous ne connaissez pas.
    """)
    
    # Filter option for optional categories
    st.markdown("### Options de filtrage")
    st.session_state.keep_optional = st.checkbox("Conserver les catégories optionnelles", value=st.session_state.keep_optional)

    
    # Display current word
    if st.session_state.current_index < len(st.session_state.words_df):
        found_next_word = False
        increment = 1
        while not found_next_word:
            current_word = st.session_state.words_df.iloc[st.session_state.current_index + increment]
            if st.session_state.keep_optional or not current_word.optional_category:
                found_next_word = True
            else:
                increment += 1
        
        # Word card
        st.markdown("---")
        st.markdown(f"# {current_word['word']}")
        st.markdown(f"*{current_word['pos_title']}*")
        
        # Buttons for known/unknown
        col1, col2 = st.columns(2)
        with col1:
            if ss.shortcut_button("❌ Unknown", use_container_width=True, shortcut="arrowleft", hint=False):
                st.session_state.unknown_words.append(current_word)
                st.session_state.current_index += 1
                st.rerun()
        
        with col2:
            if ss.shortcut_button("✅ Known", use_container_width=True, shortcut="arrowright", hint=False):
                st.session_state.known_words.append(current_word)
                st.session_state.current_index += 1
                st.rerun()
        
        # Keyboard shortcuts
        st.markdown("---")
        st.markdown("**Raccourcis clavier:**")
        st.markdown("- ⬅️ si *inconnu*")
        st.markdown("- ➡️ si *connu*")
        
    if n_tot_words:=(len(st.session_state.known_words) + len(st.session_state.unknown_words)) > 0:
        # Show results
        n_known_words = len(st.session_state.known_words)
        n_unknown_words = len(st.session_state.unknown_words)
        n_tot_words = n_known_words + n_unknown_words
        
        st.metric(label="Fraction connue", value=f"{n_known_words} / {n_tot_words}")
        
        st.success(f"🎉 Vous avez terminé avec {n_known_words} mots connus et {n_unknown_words} mots inconnus sur {n_tot_words} mots.")
        
if __name__ == "__main__":
    main()
