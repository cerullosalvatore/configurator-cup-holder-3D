import json
import time

import requests
import streamlit as st


# Caricamento mappatura una tantum
@st.cache_data
def load_local_config():
    with open("config_map.json", "r") as f:
        return json.load(f)


config_data = load_local_config()

# --- CONFIGURATION ---
st.set_page_config(page_title="Cup Holder Configurator", page_icon="⚙️")
st.title("⚙️ Cup Holder Configurator")
st.subheader("Enter the cup dimensions below to automatically generate and export your custom holder")

# Credenziali dai Secrets di Streamlit
try:
    ACCESS_KEY = st.secrets["ONSHAPE_ACCESS_KEY"]
    SECRET_KEY = st.secrets["ONSHAPE_SECRET_KEY"]
except:
    st.error("Configura le API Keys nei Secrets di Streamlit!")
    st.stop()

# ID del tuo documento (prendili dall'URL del browser)
DID = st.secrets["ONSHAPE_DID"]
WID = st.secrets["ONSHAPE_WID"]
EID = st.secrets["ONSHAPE_EID"]
PARTID = "JID"

# Creiamo gli input dinamicamente
user_inputs = {}

# --- INTERFACCIA ---
col1, col2 = st.columns([1.2, 2])

with col1:
    st.header("Parameters")

    for param in config_data:
        # Recuperiamo i metadati del parametro
        p_id = param["typeName"]
        p_name = param["parameterName"]

        app_label = param["appLabel"]

        min_v = param['minValue']
        max_v = param['maxValue']
        def_v = param['defaultValue']

        # Genera automaticamente lo slider con i limiti del CAD
        user_inputs[p_name] = st.number_input(
            label=app_label,
            min_value=min_v,
            max_value=max_v,
            value=def_v,
            step=0.5
        )

    button = st.button("Generate stl")
    if button:
        config_parts = [f"{p_name}={p_val}+mm" for p_name, p_val in user_inputs.items()]
        config_string = ";".join(config_parts)

        # 1. Creiamo una sessione per gestire i redirect correttamente
        session = requests.Session()
        session.auth = (ACCESS_KEY.strip(), SECRET_KEY.strip())

        # 2. Endpoint diretto
        url = f"https://cad.onshape.com/api/partstudios/d/{DID}/w/{WID}/e/{EID}/stl"

        params = {
            "mode": "binary",
            "units": "millimeter",
            "configuration": config_string,
            "partIds": "JID"
        }

        # Header per dire a Onshape che vogliamo il file binario
        headers = {"Accept": "application/octet-stream"}

        with st.spinner("STL Generation..."):
            try:
                # Usiamo la sessione invece di requests.get
                res = session.get(url, params=params, headers=headers, allow_redirects=True)

                if res.status_code == 200:
                    # Se il contenuto è troppo piccolo, Onshape ha mandato un errore mascherato
                    if len(res.content) < 500:
                        st.error("The generated file is too small. Check the part ID (JID).")
                        st.write(res.text)
                    else:
                        st.success(f"✅ STL Generated ({len(res.content) / 1024:.1f} KB)")
                        st.download_button(
                            label="💾 Download STL",
                            data=res.content,
                            file_name="cup_holder.stl",
                            mime="application/sla"
                        )
                elif res.status_code == 401:
                    #st.error("Errore 401: Problema di autorizzazione durante il redirect.")
                    #st.info("Sto tentando il metodo alternativo senza redirect...")

                    # Tentativo disperato: prendiamo manualmente l'URL del redirect
                    res_no_redir = session.get(url, params=params, headers=headers, allow_redirects=False)
                    if res_no_redir.status_code == 307:
                        new_url = res_no_redir.headers['Location']
                        res_final = session.get(new_url, auth=session.auth)  # Riautentichiamo manualmente
                        if res_final.status_code == 200:
                            st.download_button("💾 Download STL", res_final.content, "cup_holder.stl")
                else:
                    st.error(f"Error ({res.status_code})")
                    st.write(res.text)

            except Exception as e:
                st.error(f"Connection error: {e}")

with col2:
    st.image("images/schema.png")
