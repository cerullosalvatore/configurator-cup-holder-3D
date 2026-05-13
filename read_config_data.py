import requests
import json
import streamlit as st

# Configura i tuoi ID e Chiavi
ACCESS_KEY = st.secrets["ONSHAPE_ACCESS_KEY"]
SECRET_KEY = st.secrets["ONSHAPE_SECRET_KEY"]
DID = st.secrets["ONSHAPE_DID"]
WID = st.secrets["ONSHAPE_WID"]
EID = st.secrets["ONSHAPE_EID"]


def fetch_and_save_config():
    auth = (ACCESS_KEY, SECRET_KEY)
    url = f"https://cad.onshape.com/api/elements/d/{DID}/w/{WID}/e/{EID}/configuration"

    res = requests.get(url, auth=auth)
    res.raise_for_status()
    data = res.json()

    mapping = []
    for param in data.get("configurationParameters", []):
        p_id = param["typeName"]
        p_name = param["message"]["parameterName"]

        # Estraiamo solo i dati necessari
        if "rangeAndDefault" in param["message"]:
            constraints = param["message"]["rangeAndDefault"]["message"]
            mapping.append({
                "typeName": p_id,
                "parameterName": p_name,  # Qui puoi rinominarlo manualmente dopo nel JSON
                "minValue": float(constraints["minValue"]),
                "maxValue": float(constraints["maxValue"]),
                "defaultValue": float(constraints["defaultValue"]),
                "appLabel": "TODO",
                "appCategory": "TODO"
            })

    with open("config_map.json", "w") as f:
        json.dump(mapping, f, indent=4)
    print("Mappatura salvata in config_map.json")


if __name__ == "__main__":
    fetch_and_save_config()