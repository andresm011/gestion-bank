# Gestion Bank Web

Mini app web para gestionar bank de apuestas con tipsters cargados desde `tipsters.json`.

## Ejecutar en local

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Arranca la app:

```bash
streamlit run app.py
```

## Publicar en web (rapido con Streamlit Cloud)

1. Sube esta carpeta a un repositorio en GitHub.
2. Entra en [Streamlit Cloud](https://share.streamlit.io/).
3. Crea una nueva app seleccionando:
   - repositorio
   - rama
   - archivo principal: `app.py`
4. Deploy.

Cada vez que actualices `tipsters.json` y hagas push, la web se actualiza.
