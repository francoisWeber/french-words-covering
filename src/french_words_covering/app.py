import streamlit as st
import pandas as pd
import streamlit_shortcuts as ss
from pathlib import Path
import openai
import os

# Constants
DATA_PATH = Path(__file__).parent.parent.parent / "dico-fr.parquet"

def load_and_sample_words():
    """Load the parquet file and sample N_WORDS words."""
    df = pd.read_parquet(DATA_PATH)
    df = df[~df.optional_category]
    return df.sample(frac=1).reset_index(drop=True)

def validate_definition_with_llm(word, pos, user_definition):
    """Validate user's definition using OpenAI API."""
    try:
        # Use session state API key if available, otherwise fall back to environment variable
        api_key = st.session_state.get('openai_api_key') or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.error("Clé API OpenAI manquante. Veuillez configurer votre clé API.")
            return None
            
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""
        Tu es un expert en français. Évalue si la définition fournie correspond au mot français donné.
        
        Mot: {word} ({pos})
        Définition fournie: {user_definition}
        
        Réponds uniquement par "CORRECT" si la définition est correcte et correspond bien au mot, 
        ou "INCORRECT" si la définition est fausse ou ne correspond pas au mot.
        
        Sois strict mais juste. Une définition partiellement correcte ou approximative doit être considérée comme INCORRECT.
        """
        
        response = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip().upper()
        return result == "CORRECT"
        
    except Exception as e:
        st.error(f"Erreur lors de la validation: {str(e)}")
        return None

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
    if 'show_definition_challenge' not in st.session_state:
        st.session_state.show_definition_challenge = False
    if 'definition_result' not in st.session_state:
        st.session_state.definition_result = None
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'show_api_key_input' not in st.session_state:
        st.session_state.show_api_key_input = False

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
    - **Défiez ma définition** : Testez votre connaissance en proposant une définition
    """)
    
    # OpenAI API Key Configuration
    st.markdown("---")
    st.markdown("### 🔑 Configuration OpenAI")
    
    # Check if API key is available
    api_key_available = bool(st.session_state.get('openai_api_key') or os.getenv("OPENAI_API_KEY"))
    
    if api_key_available:
        st.success("✅ Clé API OpenAI configurée")
        if st.button("🔧 Modifier la clé API", use_container_width=True):
            st.session_state.show_api_key_input = True
            st.rerun()
    else:
        st.warning("⚠️ Clé API OpenAI manquante. La fonction 'Défiez ma définition' ne sera pas disponible.")
        if st.button("🔑 Configurer la clé API", use_container_width=True):
            st.session_state.show_api_key_input = True
            st.rerun()
    
    # API Key Input Section
    if st.session_state.show_api_key_input:
        st.markdown("#### Configuration de la clé API")
        
        new_api_key = st.text_input(
            "Entrez votre clé API OpenAI :",
            value=st.session_state.openai_api_key,
            type="password",
            placeholder="sk-..."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Sauvegarder", use_container_width=True):
                if new_api_key.strip():
                    st.session_state.openai_api_key = new_api_key.strip()
                    st.session_state.show_api_key_input = False
                    st.success("Clé API sauvegardée avec succès !")
                    st.rerun()
                else:
                    st.error("Veuillez entrer une clé API valide.")
        
        with col2:
            if st.button("❌ Annuler", use_container_width=True):
                st.session_state.show_api_key_input = False
                st.rerun()
        
        st.info("💡 Votre clé API est stockée localement dans cette session et ne sera pas sauvegardée.")
    
    # Display current word
    if st.session_state.current_index < len(st.session_state.words_df):
        current_word = st.session_state.words_df.iloc[st.session_state.current_index]
        
        # Word card
        st.markdown("---")
        st.markdown(f"# {current_word['word']}")
        st.markdown(f"*{current_word['pos_title']}*")
        
        # Definition challenge section
        if st.session_state.show_definition_challenge:
            st.markdown("### 🎯 Défiez votre définition")
            
            if st.session_state.definition_result is None:
                user_definition = st.text_area(
                    "Proposez votre définition de ce mot :",
                    placeholder="Entrez votre définition ici...",
                    height=100
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Valider ma définition", use_container_width=True):
                        if user_definition.strip():
                            with st.spinner("Validation en cours..."):
                                is_correct = validate_definition_with_llm(
                                    current_word['word'], 
                                    current_word['pos_title'], 
                                    user_definition
                                )
                                if is_correct is not None:
                                    st.session_state.definition_result = is_correct
                                    # Automatically classify and move to next word
                                    if is_correct:
                                        st.session_state.passively_known_words.append(current_word)
                                        st.success("✅ Votre définition est correcte ! Ce mot est considéré comme **connu passivement**.")
                                    else:
                                        st.session_state.unknown_words.append(current_word)
                                        st.error("❌ Votre définition n'est pas correcte. Ce mot est considéré comme **inconnu**.")
                                    
                                    # Move to next word after a brief delay
                                    st.session_state.current_index += 1
                                    st.session_state.show_definition_challenge = False
                                    st.session_state.definition_result = None
                                    st.rerun()
                        else:
                            st.error("Veuillez entrer une définition.")
                
                with col2:
                    if st.button("❌ Annuler", use_container_width=True):
                        st.session_state.show_definition_challenge = False
                        st.session_state.definition_result = None
                        st.rerun()
        
        else:
            # Regular classification buttons
            col1, col2, col3, col4 = st.columns(4)
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
            
            with col4:
                if st.button("🎯 Défiez ma définition", use_container_width=True, disabled=not api_key_available):
                    st.session_state.show_definition_challenge = True
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
