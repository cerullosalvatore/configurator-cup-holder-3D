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

        # Prepariamo le credenziali
        auth = (ACCESS_KEY.strip(), SECRET_KEY.strip())

        # URL di esportazione diretta (Endpoint Sincrono)
        url = f"https://cad.onshape.com/api/partstudios/d/{DID}/w/{WID}/e/{EID}/stl"

        # Parametri della richiesta
        params = {
            "mode": "binary",
            "units": "millimeter",
            "configuration": config_string,
            "partIds": "JID"
        }

        # Header fondamentali per forzare il download binario
        headers = {
            "Accept": "application/octet-stream"
        }

        with st.spinner("Generating and downloading..."):
            try:
                # Una sola chiamata GET.
                # Usiamo stream=True per gestire meglio i file binari pesanti
                res = requests.get(url, params=params, auth=auth, headers=headers, stream=True)

                if res.status_code == 200:
                    # Leggiamo il contenuto
                    stl_body = res.content

                    if len(stl_body) < 500:
                        st.error("The server responded, but the file appears to be empty or corrupt.")
                        st.write(res.text)
                    else:
                        st.success(f"✅ Ready! ({len(stl_body) / 1024:.1f} KB)")
                        st.download_button(
                            label="💾 Download STL",
                            data=stl_body,
                            file_name="cup_holder.stl",
                            mime="application/sla"
                        )

                # Gestione specifica del 401 causato dai redirect regionali
                elif res.status_code == 401:
                    # Forza il server regionale se quello principale fallisce
                    url_eu = url.replace("cad.onshape.com", "cad-euw1.onshape.com")
                    res_eu = requests.get(url_eu, params=params, auth=auth, headers=headers)

                    if res_eu.status_code == 200:
                        st.download_button("💾 Download STL", res_eu.content, "cup_holder.stl")
                    else:
                        st.error("Authorization Error (401). Please check your API keys.")

                else:
                    st.error(f"Error: {res.status_code}")
                    st.json(res.text)

            except Exception as e:
                st.error(f"Connection error: {e}")

with col2:
    st.image("images/schema.png")
