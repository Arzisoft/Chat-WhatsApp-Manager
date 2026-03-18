"""
Import & Analyze page — Modern, professional UI.
Supports WhatsApp exports and QR code import.
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv('.env.txt')

from core.database import (
    init_db, upsert_chat, insert_messages, save_analysis,
    save_financial_mentions, get_analysis, get_all_chats,
    save_transcription, get_voice_notes, copy_media_files, get_media_dir,
    save_contact_info, save_project_info, save_concrete_orders, save_action_items,
)
from core.parser import parse_file, scan_export_folders
from core.analyzer import analyze_chat
from core.models import ParsedChat, ParsedMessage
from components.brand import apply_brand, page_header
from components.theme import get_colors
from components.ui_components import alert_box, hero_banner

init_db()

st.set_page_config(page_title="Import Chats | Sales Intelligence", page_icon="[IMPORT]", layout="wide")
apply_brand()

page_header("Import & Analyze Chats", "Add WhatsApp conversations to your intelligence hub")

# ── API key validation ────────────────────────────────────────────────────────
api_key = st.session_state.get('api_key') or os.getenv('GEMINI_API_KEY', '').strip()

with st.sidebar:
    if not api_key:
        st.warning("API key needed for analysis")
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        if api_key:
            st.session_state['api_key'] = api_key
            st.success("API key loaded")
    else:
        st.success("API key configured [OK]")

colors = get_colors()

# ── Import Method Selection ───────────────────────────────────────────────────
st.markdown("### Choose Import Method")
import_method = st.radio(
    "How would you like to import chats?",
    ["📁 Upload WhatsApp Export Folder", "📱 WhatsApp Web QR Code", "📋 Paste Chat Text"],
    horizontal=True,
    index=0
)

st.divider()

if import_method == "📁 Upload WhatsApp Export Folder":
    st.markdown("### Step 1: Export from WhatsApp")
    st.markdown("""
    1. Open WhatsApp on your phone
    2. Select a chat or group
    3. Tap menu (⋮) → More → Export Chat
    4. Choose **With Media** to include images, audio, video
    5. Save the exported .txt file and its media folder to your computer
    """)
    
    st.markdown("### Step 2: Import Here")
    
    folder_path = st.text_input(
        "WhatsApp Export Folder Path",
        placeholder="C:\\Users\\YourName\\Downloads\\WhatsApp Chat with John Doe...",
        help="Path to the folder containing _chat.txt and media files"
    )
    
    if folder_path and st.button("[IMPORT] Import & Analyze", use_container_width=True, type="primary"):
        try:
            with st.spinner("Scanning folder..."):
                chats_found = scan_export_folders(folder_path)
            
            if not chats_found:
                alert_box("No WhatsApp chats found in that folder. Check the path.", alert_type="danger")
                st.stop()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, chat in enumerate(chats_found):
                status_text.text(f"Processing: {chat['filename']} ({idx+1}/{len(chats_found)})")
                
                # Upsert chat record
                chat_id = upsert_chat(
                    filename=chat['filename'],
                    chat_name=chat.get('chat_name'),
                    contact_name=chat.get('contact_name'),
                    raw_text=chat['raw_text']
                )
                
                # Insert messages
                insert_messages(chat_id, chat['messages'])
                
                # Run analysis if API key available
                if api_key:
                    if _run_analysis(chat_id, chat['raw_text'], chat.get('chat_name', chat['filename'])):
                        status_text.text(f"[OK] Analyzed: {chat['filename']}")
                    else:
                        status_text.text(f"⚠ Analysis skipped: {chat['filename']}")
                else:
                    status_text.text(f"→ Imported (no API key for analysis): {chat['filename']}")
                
                # Copy media
                if chat.get('media_folder'):
                    copy_media_files(chat_id, chat['media_folder'], get_media_dir())
                
                progress_bar.progress((idx+1) / len(chats_found))
            
            st.success(f"[OK] Imported {len(chats_found)} chat(s) successfully!")
            st.balloons()
            
            # Offer navigation
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("[DASHBOARD] View Dashboard", use_container_width=True):
                    st.switch_page("pages/app.py")
            with col2:
                if st.button("[CHAT] Chat Details", use_container_width=True):
                    st.switch_page("pages/2_Chat_Detail.py")
            with col3:
                if st.button("[ALERT] Risk Flags", use_container_width=True):
                    st.switch_page("pages/5_Risk_Flags.py")
        
        except Exception as e:
            alert_box(f"Error: {str(e)}", alert_type="danger")

elif import_method == "📱 WhatsApp Web QR Code":
    st.markdown("### WhatsApp Web Connection")
    st.info(
        "Scan the QR code below with your phone to authorize access to your WhatsApp chats. "
        "Your phone must remain connected while importing."
    )
    st.markdown("_QR code feature coming soon._")

elif import_method == "📋 Paste Chat Text":
    st.markdown("### Paste Chat Text")
    st.markdown("""
    You can manually paste a WhatsApp chat export as text.
    This is useful if you don't have access to the export folder.
    """)
    
    chat_name = st.text_input("Chat name (optional)", placeholder="Chat with John Doe")
    chat_text = st.text_area(
        "Paste chat text here",
        placeholder="[2/14/2026, 3:45 PM] John: Hi, do you have...",
        height=300
    )
    
    if chat_text and st.button("[IMPORT] Analyze", use_container_width=True, type="primary"):
        try:
            with st.spinner("Analyzing chat..."):
                chat_id = upsert_chat(
                    filename=chat_name or "Manual Import",
                    chat_name=chat_name,
                    raw_text=chat_text
                )
                
                if api_key:
                    if _run_analysis(chat_id, chat_text, chat_name or "Manual Import"):
                        st.success("[OK] Chat analyzed successfully!")
                    else:
                        st.warning("Chat imported but analysis failed.")
                else:
                    st.info("Chat imported. Add an API key to enable analysis.")
        
        except Exception as e:
            alert_box(f"Error: {str(e)}", alert_type="danger")

# ── Help section ──────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Frequently Asked Questions")

with st.expander("How do I export a WhatsApp chat?"):
    st.markdown("""
    **iPhone:**
    1. Open WhatsApp → Chats
    2. Swipe left on the chat you want to export
    3. Tap "More" (three dots) → "Export Chat"
    4. Choose "With Media" for images/audio/video
    5. Send via email or cloud storage

    **Android:**
    1. Open WhatsApp → Long press on the chat
    2. Tap menu (three dots) → "More" → "Export Chat"
    3. Choose "With Media"
    4. Save and transfer to your computer
    """)

with st.expander("What file formats are supported?"):
    st.markdown("""
    - WhatsApp `.txt` exports (iOS & Android)
    - Media files: images (JPG, PNG), audio (OPUS, M4A, AAC), video (MP4)
    - Voice note transcription: Arabic and English
    - Document text extraction
    """)

with st.expander("Is my data secure?"):
    st.markdown("""
    - All data is processed locally on your server
    - No data is sent to external services without your consent
    - API calls to Gemini use standard encryption
    - Media files are stored in your local database
    """)

with st.expander("Why do I need an API key?"):
    st.markdown("""
    The platform uses Gemini API to:
    - Extract contacts, companies, and roles
    - Identify deal stages and urgency levels
    - Extract concrete orders and specifications
    - Generate chat summaries
    
    [Get a Gemini API Key](https://makersuite.google.com/app/apikey)
    """)

# ── Helper function ───────────────────────────────────────────────────────────
def _run_analysis(chat_id: int, raw_text: str, chat_name: str) -> bool:
    """Run AI analysis on imported chat."""
    try:
        result = analyze_chat(raw_text=raw_text, chat_name=chat_name, api_key=api_key)
        save_analysis(chat_id, result)
        save_financial_mentions(chat_id, result.get('financial_mentions', []))
        save_contact_info(chat_id, result.get('contact', {}))
        save_project_info(chat_id, result.get('project', {}))
        save_concrete_orders(chat_id, result.get('concrete_orders', []))
        save_action_items(chat_id, result.get('action_items', []))
        return True
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        return False


