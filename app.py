import streamlit as st
import json
import random
import time

# Configuración de página
st.set_page_config(page_title="Simulador UNAM 2026", layout="wide")

# Cargar datos (asumiendo que guardaste el JSON como data.json)
@st.cache_data
def load_data():
    with open("data.json", encoding="utf-8") as f:
        return json.load(f)

data = load_data()

# Inicializar estado de sesión
if 'exam_active' not in st.session_state:
    st.session_state.exam_active = False
if 'current_questions' not in st.session_state:
    st.session_state.current_questions = []
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0

# Barra lateral
st.sidebar.title("📚 Temario UNAM 2026")
modo = st.sidebar.radio("Modo:", ["Estudiar Temario", "Simulador de Examen"])

if modo == "Estudiar Temario":
    st.header("📖 Contenido Temático")
    materia_sel = st.selectbox("Selecciona una materia", [m['nombre'] for m in data['materias']])
    
    for m in data['materias']:
        if m['nombre'] == materia_sel:
            for tema in m['temas']:
                with st.expander(f"**{tema['titulo']}**"):
                    st.markdown(f"**Resumen:** {tema.get('resumen', 'No disponible')}")
                    if tema.get('definiciones'):
                        st.subheader("Definiciones Clave")
                        for d in tema['definiciones']:
                            st.markdown(f"- **{d['termino']}:** {d['definicion']}")
                    if tema.get('flashcards'):
                        st.subheader("Flashcards")
                        for fc in tema['flashcards']:
                            st.info(f"❓ {fc['front']} \n\n ✅ {fc['back']}")

elif modo == "Simulador de Examen":
    if not st.session_state.exam_active:
        st.header("📋 Iniciar Examen")
        st.write(f"Tiempo límite: **{data['simulator']['exam_template']['time_minutes']} minutos**")
        st.write(f"Total de preguntas: **{data['simulator']['exam_template']['total_questions']}**")
        
        if st.button("🚀 Iniciar Examen", type="primary"):
            # Lógica para seleccionar preguntas aleatorias según distribución
            selected_qs = []
            bank = data['simulator']['question_bank']
            for mat, count in data['simulator']['exam_template']['distribution'].items():
                pool = [q for q in bank if q['materia'] == mat]
                selected_qs.extend(random.sample(pool, min(count, len(pool))))
            
            random.shuffle(selected_qs)
            st.session_state.current_questions = selected_qs
            st.session_state.answers = {q['id']: None for q in selected_qs}
            st.session_state.exam_active = True
            st.session_state.start_time = time.time()
            st.rerun()

    else:
        # Lógica del Examen Activo
        elapsed = time.time() - st.session_state.start_time
        remaining = data['simulator']['exam_template']['time_minutes'] * 60 - elapsed
        
        if remaining <= 0:
            st.warning("¡TIEMPO TERMINADO!")
            remaining = 0

        # Mostrar temporizador
        mins, secs = divmod(int(remaining), 60)
        st.metric("⏳ Tiempo Restante", f"{mins:02d}:{secs:02d}")
        
        # Barra de progreso
        answered_count = sum(1 for v in st.session_state.answers.values() if v is not None)
        st.progress(answered_count / len(st.session_state.current_questions))

        # Mostrar preguntas (paginadas de 5 en 5 para simplicidad)
        # En una app real usarías tabs o un selector de número
        for i, q in enumerate(st.session_state.current_questions):
            st.markdown(f"**{i+1}. [{q['materia']}] {q['enunciado']}**")
            cols = st.columns(5)
            for idx, opt in enumerate(q['opciones']):
                with cols[idx]:
                    # Botones de selección
                    if cols[idx].button(f"{chr(65+idx)}) {opt}", key=f"{q['id']}_{idx}"):
                        st.session_state.answers[q['id']] = idx
                        st.rerun()
            
            # Indicar selección actual
            if st.session_state.answers[q['id']] is not None:
                st.info(f"Tu respuesta: {q['opciones'][st.session_state.answers[q['id']]]}")
            st.divider()

        # Botón para terminar
        if st.button("Terminar y Calificar"):
            score = 0
            for q in st.session_state.current_questions:
                if st.session_state.answers[q['id']] == q['correct_index']:
                    score += 1
            
            st.success(f"Tu calificación: {score} / {len(st.session_state.current_questions)}")
            st.session_state.exam_active = False