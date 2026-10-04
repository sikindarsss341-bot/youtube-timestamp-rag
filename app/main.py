import os
import sys

# Ensure UTF-8 output encoding on Windows to prevent UnicodeEncodeError on emojis in backend prints
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

class SafeStreamWrapper:
    """Wraps stream to safely handle UnicodeEncodeError on Windows systems."""
    def __init__(self, target):
        self._target = target
    def write(self, s):
        try:
            return self._target.write(s)
        except (UnicodeEncodeError, Exception):
            enc = getattr(self._target, "encoding", "utf-8") or "utf-8"
            try:
                return self._target.write(s.encode(enc, errors="replace").decode(enc))
            except Exception:
                pass
    def flush(self):
        try:
            return self._target.flush()
        except Exception:
            pass
    def __getattr__(self, name):
        return getattr(self._target, name)

sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)

import streamlit as st

# Ensure project root and app directory are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import existing backend modules without changing any logic
try:
    from app.ingestion.youtube_transcript import extract_video_id, get_transcript
    from app.ingestion.chunking import create_chunks
    from app.retrieval.embeddings import create_embeddings
    from app.retrieval.vector_store import create_collection, create_payload_indexes, store_chunks
    from app.retrieval.retriever import search_chunks, get_neighbor_chunks
    from app.rag.generator import generate_answer
    from app.rag.crag import evaluate_retrieval
except ImportError:
    from ingestion.youtube_transcript import extract_video_id, get_transcript
    from ingestion.chunking import create_chunks
    from retrieval.embeddings import create_embeddings
    from retrieval.vector_store import create_collection, create_payload_indexes, store_chunks
    from retrieval.retriever import search_chunks, get_neighbor_chunks
    from rag.generator import generate_answer
    from rag.crag import evaluate_retrieval


# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Turn Videos Into Answers | YouTube Timestamp RAG",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
if "video_ready" not in st.session_state:
    st.session_state.video_ready = False
if "video_processed" not in st.session_state:
    st.session_state.video_processed = False
if "video_id" not in st.session_state:
    st.session_state.video_id = None
if "video_url" not in st.session_state:
    st.session_state.video_url = ""
if "chunks_count" not in st.session_state:
    st.session_state.chunks_count = 0
if "answer_data" not in st.session_state:
    st.session_state.answer_data = None

SAMPLE_VIDEO_URL = "https://youtu.be/_HQ2H_0Ayy0?si=X0foGNdimNQLhsWb"

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎥 YouTube Timestamp RAG")
    st.markdown(
        "Ask questions about YouTube videos and jump directly to the relevant moments."
    )
    st.markdown("---")

    st.markdown("### How it works")
    st.markdown(
        """
        1. **Paste a YouTube link**  
        2. **Process the transcript**  
        3. **Ask a question**  
        4. **Get an answer with timestamps**
        """
    )
    st.markdown("---")

    st.markdown("### Theme")
    theme_choice = st.radio(
        "Appearance",
        options=["🌙 Dark Mode", "☀️ Light Mode"],
        index=0 if st.session_state.theme == "Dark" else 1,
        label_visibility="collapsed"
    )
    st.session_state.theme = "Dark" if "Dark" in theme_choice else "Light"

    is_video_ready = st.session_state.get("video_ready") or st.session_state.get("video_processed")
    if is_video_ready:
        st.markdown("---")
        st.markdown("### Active Video")
        st.markdown(f"**ID:** `{st.session_state.video_id}`")
        st.markdown(f"**Chunks:** `{st.session_state.chunks_count}`")
        if st.button("Reset Video", use_container_width=True):
            st.session_state.video_ready = False
            st.session_state.video_processed = False
            st.session_state.video_id = None
            st.session_state.video_url = ""
            st.session_state.chunks_count = 0
            st.session_state.answer_data = None
            st.rerun()

# -----------------------------------------------------------------------------
# Custom Theming CSS
# -----------------------------------------------------------------------------
is_dark = st.session_state.theme == "Dark"

if is_dark:
    bg_main = "#0B0F17"
    bg_card = "#131B2B"
    border_color = "rgba(255, 255, 255, 0.08)"
    sidebar_bg = "#0B0F17"
    text_primary = "#F8FAFC"
    text_secondary = "#94A3B8"
    text_muted = "#64748B"
    
    # Secondary Button
    btn_bg = "#1E293B"
    btn_border = "#334155"
    btn_text = "#F8FAFC"
    btn_hover_bg = "#2563EB"
    btn_hover_border = "#3B82F6"
    btn_hover_text = "#FFFFFF"
    btn_focus_bg = "#1D4ED8"
    btn_focus_text = "#FFFFFF"
    
    # Input
    input_bg = "#131B2B"
    input_border = "rgba(255, 255, 255, 0.15)"
    
    # Code badge
    code_bg = "#1E293B"
    code_border = "#334155"
    code_text = "#38BDF8"
    
    # Table zebra
    table_zebra = "rgba(255, 255, 255, 0.03)"
    
    chip_bg = "#1E293B"
    chip_border = "#334155"
    chip_text = "#60A5FA"
    chip_hover_bg = "#2563EB"
    chip_hover_text = "#FFFFFF"
    accent_color = "#3B82F6"
    accent_hover = "#2563EB"
    success_bg = "rgba(16, 185, 129, 0.12)"
    success_border = "rgba(16, 185, 129, 0.3)"
    success_text = "#34D399"
else:
    # Bright / Light Theme
    bg_main = "#F8FAFC"
    bg_card = "#FFFFFF"
    border_color = "#E2E8F0"
    sidebar_bg = "#FFFFFF"
    text_primary = "#0F172A"       # Crisp dark slate-900
    text_secondary = "#475569"     # Slate-600
    text_muted = "#64748B"         # Slate-500
    
    # Secondary Button (Clean white button with slate border and dark legible text)
    btn_bg = "#FFFFFF"
    btn_border = "#CBD5E1"
    btn_text = "#0F172A"
    btn_hover_bg = "#F1F5F9"
    btn_hover_border = "#2563EB"
    btn_hover_text = "#1D4ED8"
    btn_focus_bg = "#EFF6FF"
    btn_focus_text = "#1D4ED8"
    
    # Input
    input_bg = "#FFFFFF"
    input_border = "#CBD5E1"
    
    # Code badge
    code_bg = "#F1F5F9"
    code_border = "#E2E8F0"
    code_text = "#0284C7"
    
    # Table zebra
    table_zebra = "#F8FAFC"
    
    chip_bg = "#EFF6FF"
    chip_border = "#BFDBFE"
    chip_text = "#1D4ED8"
    chip_hover_bg = "#1D4ED8"
    chip_hover_text = "#FFFFFF"
    accent_color = "#2563EB"
    accent_hover = "#1D4ED8"
    success_bg = "rgba(16, 185, 129, 0.1)"
    success_border = "rgba(16, 185, 129, 0.3)"
    success_text = "#047857"

st.markdown(
    f"""
    <style>
    /* Global Container */
    .stApp {{
        background-color: {bg_main} !important;
        color: {text_primary} !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    /* Global Typography in Main Area */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
        color: {text_primary} !important;
    }}
    .stApp p, .stApp span, .stApp label {{
        color: {text_primary};
    }}

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        border-right: 1px solid {border_color} !important;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {text_primary} !important;
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] label {{
        color: {text_secondary} !important;
    }}
    section[data-testid="stSidebar"] strong {{
        color: {text_primary} !important;
    }}
    section[data-testid="stSidebar"] hr {{
        border-color: {border_color} !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label span {{
        color: {text_primary} !important;
    }}

    /* Hero Section */
    .hero-container {{
        text-align: center;
        padding: 2.5rem 1rem 1.5rem 1rem;
        margin-bottom: 1.5rem;
    }}
    .hero-title {{
        font-size: 2.75rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: {text_primary};
        margin-bottom: 0.75rem;
        line-height: 1.15;
    }}
    .hero-subtitle {{
        font-size: 1.15rem;
        color: {text_secondary};
        max-width: 680px;
        margin: 0 auto 0.75rem auto;
        line-height: 1.5;
        font-weight: 400;
    }}
    .hero-quote {{
        font-size: 0.95rem;
        font-style: italic;
        color: {text_muted};
        max-width: 580px;
        margin: 0 auto;
        padding-top: 0.25rem;
    }}

    /* Card Wrapper */
    .saas-card {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }}
    .saas-card-title {{
        font-size: 1.25rem;
        font-weight: 700;
        color: {text_primary};
        margin-bottom: 0.5rem;
    }}
    .saas-card-subtitle {{
        font-size: 0.95rem;
        color: {text_secondary};
        margin-bottom: 1rem;
    }}

    /* Success Banner */
    .status-banner {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        background-color: {success_bg};
        border: 1px solid {success_border};
        color: {success_text};
        padding: 0.75rem 1rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 1rem;
    }}

    /* Info Chips Grid */
    .info-grid {{
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 0.5rem;
    }}
    .info-chip {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background-color: {chip_bg};
        border: 1px solid {chip_border};
        color: {text_secondary};
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    .info-chip strong {{
        color: {text_primary};
    }}

    /* All Standard / Secondary Buttons (Quick Actions, Try Sample Video, Reset Video) */
    div.stButton > button,
    div.stButton > button:not([kind="primary"]) {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_border} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1rem !important;
        transition: all 0.15s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }}
    div.stButton > button p,
    div.stButton > button span,
    div.stButton > button div {{
        color: {btn_text} !important;
        font-weight: 600 !important;
    }}
    div.stButton > button:hover {{
        background-color: {btn_hover_bg} !important;
        border-color: {btn_hover_border} !important;
        color: {btn_hover_text} !important;
    }}
    div.stButton > button:hover p,
    div.stButton > button:hover span,
    div.stButton > button:hover div {{
        color: {btn_hover_text} !important;
    }}
    div.stButton > button:active,
    div.stButton > button:focus {{
        background-color: {btn_focus_bg} !important;
        border-color: {accent_color} !important;
        color: {btn_focus_text} !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25) !important;
    }}
    div.stButton > button:active p,
    div.stButton > button:focus p,
    div.stButton > button:active span,
    div.stButton > button:focus span {{
        color: {btn_focus_text} !important;
    }}

    /* Primary Action Buttons (Analyze Video, Ask Question submit button) */
    div.stButton > button[kind="primary"],
    div[data-testid="stFormSubmitButton"] > button {{
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #2563EB !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.55rem 1rem !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25) !important;
    }}
    div.stButton > button[kind="primary"] p,
    div.stButton > button[kind="primary"] span,
    div.stButton > button[kind="primary"] div,
    div[data-testid="stFormSubmitButton"] > button p,
    div[data-testid="stFormSubmitButton"] > button span,
    div[data-testid="stFormSubmitButton"] > button div {{
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }}
    div.stButton > button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {{
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
        color: #FFFFFF !important;
    }}

    /* Text Inputs (Video URL, Question) */
    div[data-baseweb="input"] {{
        background-color: {input_bg} !important;
        border: 1px solid {input_border} !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="input"]:focus-within {{
        border-color: {accent_color} !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }}
    div[data-baseweb="base-input"] input {{
        background-color: {input_bg} !important;
        color: {text_primary} !important;
        -webkit-text-fill-color: {text_primary} !important;
        font-size: 0.95rem !important;
    }}
    div[data-baseweb="base-input"] input::placeholder {{
        color: {text_muted} !important;
        -webkit-text-fill-color: {text_muted} !important;
    }}

    /* Form Container */
    div[data-testid="stForm"] {{
        border: 1px solid {border_color} !important;
        background-color: {bg_card} !important;
        border-radius: 12px !important;
        padding: 1.25rem !important;
    }}

    /* Code Snippets */
    code {{
        background-color: {code_bg} !important;
        color: {code_text} !important;
        border: 1px solid {code_border} !important;
        padding: 0.18rem 0.45rem !important;
        border-radius: 6px !important;
        font-size: 0.85rem !important;
    }}

    /* Answer Card */
    .answer-card {{
        background-color: {bg_card};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }}
    .answer-card-header {{
        font-size: 1.2rem;
        font-weight: 700;
        color: {text_primary};
        margin-bottom: 0.75rem;
    }}
    .answer-card-body {{
        font-size: 1rem;
        line-height: 1.65;
        color: {text_primary};
        white-space: pre-wrap;
    }}

    /* Clickable Timestamp Link Pill */
    .timestamp-container {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-top: 0.75rem;
    }}
    .timestamp-link {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background-color: {chip_bg};
        border: 1px solid {chip_border};
        color: {chip_text} !important;
        text-decoration: none !important;
        padding: 0.4rem 0.85rem;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
        transition: all 0.15s ease-in-out;
    }}
    .timestamp-link:hover {{
        background-color: {chip_hover_bg};
        color: {chip_hover_text} !important;
        border-color: {chip_hover_bg};
        text-decoration: none !important;
    }}

    /* Expander Container */
    div[data-testid="stExpander"] {{
        background-color: {bg_card} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stExpander"] details summary span,
    div[data-testid="stExpander"] details summary p {{
        color: {text_primary} !important;
        font-weight: 600 !important;
    }}

    /* Status Container */
    div[data-testid="stStatusWidget"] {{
        background-color: {bg_card} !important;
        border: 1px solid {border_color} !important;
        color: {text_primary} !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stStatusWidget"] * {{
        color: {text_primary} !important;
    }}

    /* Markdown Tables (used for Main Topics, Summaries) */
    table {{
        color: {text_primary} !important;
        border-collapse: collapse !important;
        width: 100% !important;
        margin: 1rem 0 !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }}
    th {{
        background-color: {chip_bg} !important;
        color: {text_primary} !important;
        border: 1px solid {border_color} !important;
        padding: 0.6rem 0.85rem !important;
        font-weight: 600 !important;
        text-align: left !important;
    }}
    td {{
        border: 1px solid {border_color} !important;
        padding: 0.55rem 0.85rem !important;
        color: {text_primary} !important;
    }}
    tr:nth-child(even) td {{
        background-color: {table_zebra} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# 1. Landing / Hero Section
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">Turn Videos Into Answers.</div>
        <div class="hero-subtitle">
            Stop watching for hours. Ask questions, find key moments, and get answers with exact timestamps.
        </div>
        <div class="hero-quote">
            "Your time is valuable — let your questions find the moment that matters."
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# Processing Helper (Uses existing backend logic 100%)
# -----------------------------------------------------------------------------
def process_youtube_video(url: str):
    """
    Runs existing flow:
    YouTube URL -> transcript -> timestamp chunks -> embeddings -> Qdrant
    """
    video_id = extract_video_id(url)
    if not video_id:
        st.error("Please enter a valid YouTube URL.")
        return

    progress_container = st.container()
    with progress_container:
        status_box = st.status("Analyzing video...", expanded=True)

        # 1. Fetch transcript
        try:
            status_box.write("Fetching transcript...")
            transcript = get_transcript(video_id)
            if not transcript:
                status_box.update(label="Transcript unavailable", state="error")
                st.error("We couldn't retrieve a transcript for this video.")
                return
        except Exception:
            status_box.update(label="Transcript unavailable", state="error")
            st.error("We couldn't retrieve a transcript for this video.")
            return

        # 2. Creating chunks
        try:
            status_box.write("Creating timestamp chunks...")
            chunks = create_chunks(transcript, chunk_duration=60)
            if not chunks:
                status_box.update(label="Chunking failed", state="error")
                st.error("We couldn't retrieve a transcript for this video.")
                return
        except Exception:
            status_box.update(label="Chunking failed", state="error")
            st.error("We couldn't retrieve a transcript for this video.")
            return

        # 3. Generating embeddings
        try:
            status_box.write("Generating embeddings...")
            texts = [chunk["text"] for chunk in chunks]
            embeddings = create_embeddings(texts)
        except Exception:
            status_box.update(label="Embeddings failed", state="error")
            st.error("Failed to create embeddings.")
            return

        # 4. Indexing video in Qdrant
        try:
            status_box.write("Indexing video...")
            create_collection()
            create_payload_indexes()
            store_chunks(chunks, embeddings, video_id)
        except Exception:
            status_box.update(label="Indexing failed", state="error")
            st.error("Failed to index the video.")
            return

        # 5. Video ready!
        status_box.write("Video ready!")
        status_box.update(label="✓ Video is ready", state="complete")

        # Update session state
        st.session_state.video_ready = True
        st.session_state.video_processed = True
        st.session_state.video_id = video_id
        st.session_state.video_url = url
        st.session_state.chunks_count = len(chunks)
        st.session_state.answer_data = None

        st.rerun()


# -----------------------------------------------------------------------------
# Question Answering Helper (Uses existing retrieval + CRAG + Groq logic 100%)
# -----------------------------------------------------------------------------
def run_question_answering(question: str, is_quick_action: bool = False):
    """
    Runs QA pipeline:
    - If is_quick_action: connects video chunks directly to Groq to generate video summary / key points.
    - Otherwise: runs existing search_chunks -> evaluate_retrieval (CRAG) -> get_neighbor_chunks -> generate_answer.
    """
    if not question.strip():
        return

    print(f"\n[QA DEBUG] Question: {question!r} (quick_action={is_quick_action})", flush=True)
    video_id = st.session_state.get("video_id") or "cORnEmFk4JM"
    st.session_state.video_id = video_id
    print(f"[QA DEBUG] Video ID in session_state: {video_id!r}", flush=True)

    with st.spinner("Finding relevant moments and generating answer..."):
        # Quick Actions: Connect video chunks directly to Groq
        if is_quick_action:
            try:
                from app.retrieval.vector_store import client, COLLECTION_NAME
                all_chunks = client.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter={
                        "must": [
                            {"key": "video_id", "match": {"value": video_id}}
                        ]
                    },
                    limit=100,
                    with_payload=True
                )[0]

                if not all_chunks:
                    all_chunks = client.scroll(
                        collection_name=COLLECTION_NAME,
                        limit=100,
                        with_payload=True
                    )[0]

                all_chunks.sort(key=lambda x: x.payload.get("chunk_index", 0))
                print(f"[QA DEBUG] Fetched {len(all_chunks)} chunks for quick action", flush=True)

                parts = []
                for c in all_chunks:
                    start_sec = int(c.payload.get("start", 0))
                    m = start_sec // 60
                    s = start_sec % 60
                    parts.append(f"[{m}:{s:02d}] " + c.payload.get("text", ""))

                context = "\n\n".join(parts)[:14000]
                prompt_text = question + " Include timestamps for the moments you mention."
                answer = generate_answer(prompt_text, context)

                import re
                matches = re.findall(r"\b(\d{1,2}:\d{2})\b", answer)
                seen = set()
                timestamps = []
                for m_str in matches:
                    if m_str not in seen:
                        seen.add(m_str)
                        mins, secs = map(int, m_str.split(":"))
                        total_sec = mins * 60 + secs
                        timestamps.append({
                            "label": m_str,
                            "url": f"https://www.youtube.com/watch?v={video_id}&t={total_sec}s",
                            "start": total_sec
                        })

                if not timestamps:
                    for c in all_chunks[:5]:
                        st_val = c.payload.get("start", 0)
                        mins = int(st_val // 60)
                        secs = int(st_val % 60)
                        lbl = f"{mins}:{secs:02d}"
                        if lbl not in seen:
                            seen.add(lbl)
                            timestamps.append({
                                "label": lbl,
                                "url": f"https://www.youtube.com/watch?v={video_id}&t={int(st_val)}s",
                                "start": st_val
                            })

                st.session_state.answer_data = {
                    "question": question,
                    "answer": answer,
                    "error": None,
                    "timestamps": timestamps,
                    "context_chunks": all_chunks[:6]
                }
                return
            except Exception as e:
                print(f"[QA DEBUG] Error in quick action: {e}", flush=True)
                st.session_state.answer_data = {
                    "question": question,
                    "answer": None,
                    "error": "Failed to generate video summary.",
                    "timestamps": [],
                    "context_chunks": []
                }
                return

        # 1. Search Qdrant for manual questions
        try:
            results = search_chunks(question)
            print(f"[QA DEBUG] search_chunks returned {len(results)} results", flush=True)
            for i, r in enumerate(results):
                print(f"   Result {i}: score={r.score:.4f}, start={r.payload.get('start')}, text={r.payload.get('text', '')[:60]!r}", flush=True)
        except Exception as e:
            print(f"[QA DEBUG] Error during search_chunks: {e}", flush=True)
            st.session_state.answer_data = {
                "question": question,
                "answer": None,
                "error": "Failed to search video context.",
                "timestamps": [],
                "context_chunks": []
            }
            return

        # 2. CRAG verification
        crag_passed = evaluate_retrieval(results)
        print(f"[QA DEBUG] CRAG evaluate_retrieval: {crag_passed}", flush=True)
        if not crag_passed:
            st.session_state.answer_data = {
                "question": question,
                "answer": None,
                "error": "I couldn't find relevant information in this video.",
                "timestamps": [],
                "context_chunks": []
            }
            return

        # 3. Retrieve neighbor chunks for context window
        try:
            all_context = []
            for result in results:
                neighbors = get_neighbor_chunks(result, window=1)
                for chunk in neighbors:
                    all_context.append(chunk)

            # Deduplicate and sort chunks chronologically
            unique_chunks = {chunk.id: chunk for chunk in all_context}
            context_chunks = list(unique_chunks.values())
            context_chunks.sort(key=lambda x: x.payload["chunk_index"])

            context = "\n\n".join(chunk.payload["text"] for chunk in context_chunks)
            print(f"[QA DEBUG] Built context with {len(context_chunks)} neighbor chunks", flush=True)
        except Exception as e:
            print(f"[QA DEBUG] Error retrieving neighbors: {e}", flush=True)
            st.session_state.answer_data = {
                "question": question,
                "answer": None,
                "error": "Failed to retrieve context windows.",
                "timestamps": [],
                "context_chunks": []
            }
            return

        # 4. Generate answer using existing Groq generator
        try:
            answer = generate_answer(question, context)
            print(f"[QA DEBUG] Answer generated: {answer[:80]}...", flush=True)
        except Exception as e:
            print(f"[QA DEBUG] Error generating answer: {e}", flush=True)
            st.session_state.answer_data = {
                "question": question,
                "answer": None,
                "error": "Failed to generate an answer.",
                "timestamps": [],
                "context_chunks": []
            }
            return

        # 5. Collect timestamps
        timestamps = []
        for result in results:
            start = result.payload["start"]
            minutes = int(start // 60)
            seconds = int(start % 60)
            formatted_time = f"{minutes}:{seconds:02d}"
            timestamp_url = f"https://www.youtube.com/watch?v={video_id}&t={int(start)}s"
            timestamps.append({
                "label": formatted_time,
                "url": timestamp_url,
                "start": start
            })

        st.session_state.answer_data = {
            "question": question,
            "answer": answer,
            "error": None,
            "timestamps": timestamps,
            "context_chunks": context_chunks
        }


# -----------------------------------------------------------------------------
# 2. YouTube Video Input & 3. Sample Video Section
# -----------------------------------------------------------------------------
col_main, _ = st.columns([1, 0.01])

with col_main:
    with st.container():
        st.markdown(
            """
            <div class="saas-card">
                <div class="saas-card-title">Analyze a YouTube Video</div>
                <div class="saas-card-subtitle">Paste your YouTube video link below to index its content.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        url_col, btn_col = st.columns([4, 1])
        with url_col:
            video_url_input = st.text_input(
                "Paste your YouTube video link",
                value=st.session_state.video_url if st.session_state.video_processed else "",
                placeholder="https://www.youtube.com/watch?v=...",
                label_visibility="collapsed"
            )
        with btn_col:
            analyze_clicked = st.button("Analyze Video", type="primary", use_container_width=True)

        if analyze_clicked:
            if video_url_input.strip():
                process_youtube_video(video_url_input.strip())
            else:
                st.error("Please enter a valid YouTube URL.")

        # Sample Video Section
        st.markdown(
            f"""
            <div style="margin-top: 0.75rem; margin-bottom: 0.5rem; font-size: 0.9rem; color: {text_secondary};">
                Want to try it first? Use our sample video: <code style="font-size: 0.85rem;">{SAMPLE_VIDEO_URL}</code>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Try Sample Video", use_container_width=False):
            process_youtube_video(SAMPLE_VIDEO_URL)


# -----------------------------------------------------------------------------
# 4. Workspace: Displayed Only After Video is Processed
# -----------------------------------------------------------------------------
if st.session_state.get("video_ready") or st.session_state.get("video_processed"):
    st.markdown("---")

    # 4 & 11. Video Ready Success Indicator + Information Card
    st.markdown(
        f"""
        <div class="status-banner">
            <span>✓ Video is ready</span>
        </div>
        <div class="info-grid">
            <div class="info-chip">✓ Video processed: <strong>{st.session_state.video_id}</strong></div>
            <div class="info-chip">✓ Number of transcript chunks: <strong>{st.session_state.chunks_count}</strong></div>
            <div class="info-chip">✓ Retrieval ready</div>
        </div>
        <div style="height: 1rem;"></div>
        """,
        unsafe_allow_html=True
    )

    # 5. Quick Actions Section
    st.markdown("### Quick Actions")
    st.markdown(
        f"<span style='color: {text_secondary}; font-size: 0.9rem;'>Click any prompt below to query key insights immediately:</span>",
        unsafe_allow_html=True
    )

    qa_col1, qa_col2, qa_col3 = st.columns(3)

    quick_actions = [
        ("Summarize this video", "Give me a concise summary of this video."),
        ("Key points", "What are the main key points discussed in this video?"),
        ("Main topics", "What are the main topics discussed in this video?"),
        ("Important moments", "What are the most important moments discussed in this video?"),
        ("Explain the video simply", "Explain the main content of this video in simple terms."),
        ("Give me the important timestamps", "What are the important moments in this video and their timestamps?")
    ]

    for idx, (label, question_prompt) in enumerate(quick_actions):
        target_col = [qa_col1, qa_col2, qa_col3][idx % 3]
        with target_col:
            if st.button(label, key=f"qa_btn_{idx}", use_container_width=True):
                run_question_answering(question_prompt, is_quick_action=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Question Input Form (Supports both clicking 'Ask Question' and pressing Enter)
    st.markdown("### Ask anything about this video")
    with st.form(key="question_form", clear_on_submit=False):
        q_input_col, q_btn_col = st.columns([4, 1])

        with q_input_col:
            user_question = st.text_input(
                "Question",
                placeholder="e.g. Who won the island in Beast Games?",
                label_visibility="collapsed",
                key="user_question_input"
            )

        with q_btn_col:
            ask_clicked = st.form_submit_button("Ask Question", type="primary", use_container_width=True)

        if ask_clicked:
            if user_question.strip():
                run_question_answering(user_question.strip(), is_quick_action=False)
            else:
                st.warning("Please enter a question.")

    # 6. Answer Section
    if st.session_state.answer_data:
        ans_data = st.session_state.answer_data
        st.markdown("---")
        st.markdown("### Answer")

        if ans_data.get("error"):
            st.info(ans_data["error"])
        else:
            # Clean Answer Card
            st.markdown(
                f"""
                <div style="font-size: 0.95rem; color: {text_secondary}; margin-top: 0.5rem; margin-bottom: 0.75rem; font-weight: 600;">
                    Question: <em>"{ans_data['question']}"</em>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(ans_data["answer"])

            # Relevant Clickable Timestamps
            if ans_data.get("timestamps"):
                st.markdown("#### Relevant Timestamps")
                st.markdown(
                    f"<span style='color: {text_secondary}; font-size: 0.85rem;'>Click a timestamp to jump directly to that point in the YouTube video:</span>",
                    unsafe_allow_html=True
                )

                timestamp_links_html = "".join([
                    f'<a href="{ts["url"]}" target="_blank" class="timestamp-link">'
                    f'▶ {ts["label"]} — Watch moment</a>'
                    for ts in ans_data["timestamps"]
                ])

                st.markdown(
                    f'<div class="timestamp-container">{timestamp_links_html}</div>',
                    unsafe_allow_html=True
                )

            # 7. Video Context / Sources
            if ans_data.get("context_chunks"):
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                with st.expander("View Retrieved Context"):
                    st.caption("The following transcript chunks were retrieved and used to generate the answer:")
                    for idx, chunk in enumerate(ans_data["context_chunks"], 1):
                        start_time = chunk.payload.get("start", 0)
                        end_time = chunk.payload.get("end", 0)
                        c_idx = chunk.payload.get("chunk_index", idx)
                        st.markdown(f"**Chunk #{c_idx}** [{int(start_time // 60)}:{int(start_time % 60):02d} - {int(end_time // 60)}:{int(end_time % 60):02d}]")
                        st.text(chunk.payload.get("text", ""))
                        st.markdown("---")