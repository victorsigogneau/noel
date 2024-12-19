import streamlit as st
from openai import OpenAI
import os 
api_key_OAI = os.environ['OPENAI_KEY']
# Configuration de l'API OpenAI
client = OpenAI(api_key=api_key_OAI)

# Informations sur le cadeau
correct_answers = {
    "type": "hotel",
    "region": "Pays de la loire",
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

def check_similarity(user_input, correct_answer, context):
    prompt = f"""
    Compare ces deux réponses dans le contexte de {context} :
    Réponse 1 : {user_input}
    Réponse 2 : {correct_answer}

    Ces réponses signifient-elles plus ou moins la même chose ou contient le mot  ? Réponds uniquement par OUI ou NON.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu dois comparer deux réponses et répondre uniquement par OUI ou NON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=10
        )
        return "OUI" in response.choices[0].message.content.strip().upper()
    except Exception as e:
        st.error(f"Erreur lors de la vérification de similarité : {e}")
        return False

def ask_model(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu es un assistant ludique qui donne des indices créatifs."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=256
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Erreur lors de l'appel à l'API OpenAI : {e}"

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

    # Champ de saisie utilisateur
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
        else:
            model_response = ask_model(
                f"L'utilisateur a proposé '{user_input}'. Donne un indice créatif et ludique pour deviner {st.session_state.step} : {correct_answers[st.session_state.step]}. Assure-toi de ne pas donner directement la réponse."
            )
            st.error("Non, essayez encore...")
            st.info(f"💡 {model_response}")

# Résumé final
if st.session_state.step == "done":
    st.balloons()
    st.success("🎉 Félicitations ! Vous avez deviné le cadeau ! 🎁")
    st.write("Récapitulatif de vos réponses :")
    st.image("https://github.com/victorsigogneau/noel/blob/main/reveal.PNG?raw=true", caption="Chateau des tourelles")

    if st.button("Recommencer le jeu", use_container_width=True):
        st.session_state.step = "type"
        st.session_state.guesses = {}
        st.session_state.history = []
        st.session_state.current_input = ""
        st.rerun()
