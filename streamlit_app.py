import streamlit as st
import os
import json
import time
from dotenv import load_dotenv
from core.orchestrator import VideoOrchestrator

load_dotenv()

# Set page config
st.set_page_config(
    page_title="AI Video Auto Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Cyberpunk/Modern look
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #ff0055;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        background-color: #262730;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎥 AI Shorts Generator")
st.caption("Powered by Claude, Gemini, Stability & FFMPEG")

# Sidebar for Configuration
with st.sidebar:
    st.header("Settings")
    
    # Check Environment
    # Roteiro precisa de Claude OU Gemini; imagens precisam de Stability.
    llm_keys = ["ANTHROPIC_API_KEY", "GEMINI_API_KEY"]
    for key in llm_keys + ["STABILITY_API_KEY"]:
        if os.getenv(key):
             st.success(f"{key} Loaded")
        else:
             st.warning(f"{key} Missing")
    has_llm = any(os.getenv(k) for k in llm_keys) or bool(os.getenv("GOOGLE_CLOUD_PROJECT"))
    all_keys_ok = has_llm and bool(os.getenv("STABILITY_API_KEY"))
    if not has_llm:
        st.error("Set ANTHROPIC_API_KEY and/or GEMINI_API_KEY")
    
    st.divider()
    if st.button("Check FFMPEG"):
        import subprocess
        try:
             res = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
             if res.returncode == 0:
                 st.success("FFMPEG Found!")
             else:
                 st.error("FFMPEG Error")
        except:
             st.error("FFMPEG Not Found")

# Main Area
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Create New Video")
    
    tab1, tab2 = st.tabs(["Manual Input", "Google Sheets"])
    
    final_topic = None
    
    with tab1:
        manual_topic = st.text_input("Enter Video Topic", placeholder="e.g., The calmness of a rainy night in Tokyo")
        if manual_topic:
            final_topic = manual_topic
            
    with tab2:
        st.info("Paste a Public Google Sheet URL (Anyone with link can view).")
        sheet_url = st.text_input("Google Sheet URL", value="https://docs.google.com/spreadsheets/d/1mo_Dqo3nSYbPFLwBAJP56BWtkYAuSJLCM61Ywoq0cFk/edit?usp=sharing")
        
        if st.button("Load Prompts"):
            try:
                from services.sheets import SheetsService
                sheets_service = SheetsService()
                prompts = sheets_service.get_prompts_from_sheet(sheet_url)
                if prompts:
                    st.session_state['sheet_prompts'] = prompts
                    st.success(f"Loaded {len(prompts)} prompts.")
                else:
                    st.error("No prompts found or couldn't read sheet.")
            except ImportError:
                 st.error("Sheets Service not found (Check restart).")
                 
        prompts = st.session_state.get('sheet_prompts', [])
        if prompts:
            selected_prompt = st.selectbox("Select a Topic", prompts)
            if selected_prompt:
                final_topic = selected_prompt

    if st.button("🚀 Generate Video", disabled=not all_keys_ok):
        if not final_topic:
            st.warning("Please enter or select a topic.")
        else:
            status_container = st.status("Initializing workflow...", expanded=True)
            
            try:
                orchestrator = VideoOrchestrator()
                
                status_container.write(f"✍️ Generating Script for: '{final_topic[:40]}...'")
                
                try:
                    orchestrator.start_pipeline(final_topic)
                except Exception as e:
                     st.error(f"Pipeline Failed: {e}")
                     status_container.update(state="error")
                     # Re-raise to catch below or just stop
                     raise e
                
                # After it returns, check state
                with open("state.json", "r") as f:
                    state = json.load(f)
                
                if state.get("status") == "completed":
                    status_container.update(label="✅ Generation Complete!", state="complete", expanded=False)
                    st.success("Video Generated Successfully!")
                    st.session_state['latest_video'] = state.get("final_path")
                else:
                    status_container.update(label="❌ Generation Failed", state="error")
                    st.error("Something went wrong. Check console logs.")
                    
            except Exception as e:
                status_container.update(label="❌ Error", state="error")
                st.error(f"An error occurred: {e}")

with col2:
    st.subheader("Preview")
    
    # Check if we have a generated video in session or state
    video_path = st.session_state.get('latest_video')
    
    # Also check if there is a completed state on disk from previous run
    if not video_path and os.path.exists("state.json"):
         with open("state.json", "r") as f:
            state = json.load(f)
            if state.get("status") == "completed":
                video_path = state.get("final_path")

    if video_path and os.path.exists(video_path):
        st.video(video_path)
        
        # Details
        with open("state.json", "r") as f:
            state = json.load(f)
        
        with st.expander("View Script"):
            st.write(state.get("script", "No script found."))
    else:
        st.info("No video generated yet.")
