import json

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

        auth = (ACCESS_KEY.strip(), SECRET_KEY.strip())

        # Usiamo l'endpoint del PartStudio (più stabile di quello della singola parte)
        url = f"https://cad.onshape.com/api/parts/d/{DID}/w/{WID}/e/{EID}/partid/JID/stl"
        params = {
            "mode": "binary",
            "units": "millimeter",
            "configuration": config_string,
            "scale": 1
        }

        headers = {"Accept": "application/octet-stream"}

        with st.spinner("Downloading file..."):
            # 1. Chiamata con allow_redirects=False per evitare il 401 sul secondo server
            res = requests.get(url, params=params, auth=auth, headers=headers, allow_redirects=False)

            if res.status_code == 307:
                # Recuperiamo l'URL di redirect fornito da Onshape
                redirect_url = res.headers['Location']

                st.success("✅ Model configured!")

                # Pulsante nativo di Streamlit che punta all'URL di download
                # Si comporta come un normale st.button ma apre il link
                st.link_button(
                    label="💾 Download STL",
                    url=redirect_url,
                    help="Click to download the stl file",
                    type="primary"  # Lo rende colorato (solitamente rosso/arancio o blu a seconda del tema)
                )

            else:
                st.error(f"Error: {res.status_code}")
                st.write(res.text)

with col2:
    st.image("images/schema.png")
