"""
Streamlit entry point for YouTube Timestamp RAG.
Delegates directly to app/main.py.
"""
import os
import sys

# Ensure root directory and app directory are in sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, "app")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Sync Streamlit Cloud secrets to environment variables if present
try:
    import streamlit as st
    for k, v in st.secrets.items():
        if isinstance(v, str) and k not in os.environ:
            os.environ[k] = v
except Exception:
    pass

import runpy

if __name__ == "__main__":
    main_path = os.path.join(APP_DIR, "main.py")
    runpy.run_path(main_path, run_name="__main__")
