import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from huggingface_hub import InferenceClient

# Configuration du client Hugging Face
client = InferenceClient(token="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")
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.2"

# Informations sur le cadeau
correct_answers = {
    "type": "Week-end ou nuit hotel",
    "region": "Pays de loire",
    "ville": "pornichet",
    "lieu": "Chateau des tourelles"
}

# Questions pour chaque étape
questions = {
    "type": "Quel type de cadeau est-ce ?",
    "region": "Dans quelle région se trouve le cadeau ?",
    "ville": "Dans quelle ville se trouve le cadeau ?",
    "lieu": "Quel est le lieu exact ?"
}

# Initialisation de la session
if "step" not in st.session_state:
    st.session_state.step = "type"
    st.session_state.guesses = {}
    st.session_state.history = []
    st.session_state.current_input = ""

# Titre
st.title("Devinez votre cadeau de Noël 🎄")

def format_prompt(message):
    system_prompt = "Tu es un assistant qui aide à vérifier si deux réponses sont similaires."
    formatted_prompt = f"<s>[INST] {system_prompt}\n\n{message} [/INST]"
    return formatted_prompt

def check_similarity(user_input, correct_answer, context):
    prompt = f"""
    Compare ces deux réponses dans le contexte de {context}:
    Réponse 1: {user_input}
    Réponse 2: {correct_answer}
    
    Ces réponses signifient-elles essentiellement la même chose? Réponds uniquement par OUI ou NON.
    """
    
    try:
        response = client.text_generation(
            format_prompt(prompt),
            model=MODEL_ID,
            max_new_tokens=10,
            temperature=0.1
        )
        return "OUI" in response.upper()
    except Exception as e:
        st.error(f"Erreur lors de la vérification de similarité: {e}")
        return False

def ask_model(prompt):
    try:
        formatted_prompt = format_prompt(prompt)
        response = client.text_generation(
            formatted_prompt,
            model=MODEL_ID,
            max_new_tokens=256,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.15
        )
        return response
    except Exception as e:
        return f"Erreur lors de l'appel à l'API Hugging Face : {e}"

# Fonction pour obtenir l'étape suivante
def get_next_step(current_step):
    steps = ["type", "region", "ville", "lieu", "done"]
    current_index = steps.index(current_step)
    return steps[current_index + 1] if current_index < len(steps) - 1 else "done"

# Affichage du progrès
if st.session_state.step != "done":
    steps = ["type", "region", "ville", "lieu"]
    current_step_index = steps.index(st.session_state.step)
    progress = (current_step_index) / (len(steps) - 1)
    st.progress(progress)

# Gestion des étapes
if st.session_state.step != "done":
    current_question = questions[st.session_state.step]
    st.subheader(f"Étape {steps.index(st.session_state.step) + 1} : {current_question}")
    
    # Création d'une colonne unique pour le champ de saisie
    col1 = st.columns(1)[0]
    with col1:
        user_input = st.text_input(
            "Votre réponse",
            key=f"input_{st.session_state.step}",
            value=st.session_state.current_input
        )
        
        if user_input:
            if check_similarity(user_input.lower(), correct_answers[st.session_state.step].lower(), f"{st.session_state.step}"):
                st.success("Correct ! ✨")
                st.session_state.guesses[st.session_state.step] = user_input
                st.session_state.step = get_next_step(st.session_state.step)
                st.session_state.current_input = ""  # Réinitialiser l'entrée
                st.rerun()
            # Recharger la page pour afficher la question suivante
            else:
                model_response = ask_model(
                    f"L'utilisateur a proposé '{user_input}'. Donne un indice sur {st.session_state.step}: {correct_answers[st.session_state.step]}. "
                    f"Pornichet : Pornichet [pɔʁniʃɛ] est une commune de l'Ouest de la France, située dans le département de la Loire-Atlantique, en région Pays de la Loire. Elle fait aussi partie de la Bretagne historique, située en pays Nantais, un des pays traditionnels de Bretagne."
                    f"""Chateau des tourelles : Le château des Tourelles est un édifice construit en 1868 sur le territoire de la commune de Pornichet, dans le département français de la Loire-Atlantique. Le château appartient depuis 2008 au groupe Phelippeau qui l'a converti en centre de thalassothérapie et en hôtel de luxe. """
                    f"Sois créatif et ludique dans ta réponse, mais ne révèle pas directement la réponse."
                )
                st.error("Non, essayez encore...")
                st.info(f"💡 Indice : {model_response}")

# Résumé final
if st.session_state.step == "done":
    st.balloons()
    st.success("🎉 Félicitations ! Vous avez deviné le cadeau ! 🎁")
    st.write("Récapitulatif de vos réponses :")
    st.image("reveal.png", caption="Chateau des tourelles")
    
    if st.button("Recommencer le jeu", use_container_width=True):
        st.session_state.step = "type"
        st.session_state.guesses = {}
        st.session_state.history = []
        st.session_state.current_input = ""
        st.rerun()
