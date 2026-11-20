# Just for you — Streamlit surprise site

## Project files

- `main.py` — Streamlit app entry point
- `requirements.txt` — Python dependencies
- `assets/eyes.jpg` — hero image
- `assets/photos/` — the five gallery photos used by the app

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run main.py
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Open https://share.streamlit.io/ and sign in with GitHub.
3. Choose **Create app**.
4. Select this repository, branch `main`, and entrypoint `main.py`.
5. Click **Deploy**.

Keep `main.py`, `requirements.txt`, and the `assets/` folder in the repository.
