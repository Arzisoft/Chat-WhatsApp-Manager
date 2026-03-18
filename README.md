# ChatChaos WhatsApp Management System

Professional WhatsApp chat analysis and business intelligence platform for managing conversations, reservations, and customer interactions.

---

## Quick Start

### 1. Start the WhatsApp Bridge (Node.js)
```bash
cd bridge
npm start
```

### 2. Start Streamlit Dashboard
```bash
streamlit run app.py
```

**Access:** http://localhost:8501

---

## Architecture Overview

### Three-Component System

**1. WhatsApp Bridge (Node.js)**
- Location: `bridge/`
- Purpose: Live chat access via WhatsApp Web
- Auth: QR code (persistent LocalAuth)
- Exposes REST API: `/status`, `/chats`, `/messages/:chat_id`

**2. Python Backend**
- Location: `core/`
- Modules:
  - `parser.py`  Parse WhatsApp .txt exports (iOS/Android)
  - `transcriber.py`  Voice note transcription (Gemini)
  - `analyzer.py`  AI extraction (Gemini 2.5 Flash)
  - `database.py`  SQLite persistence
  - `whatsapp_connector.py`  Bridge communication

**3. Streamlit Frontend**
- Location: `pages/` + `app.py`
- 7 pages: Landing, Import, Dashboard, Chat Detail, Area Overview, Follow-Ups, Risk Flags, Map

---

## Pages

| Page | File | Purpose |
|------|------|---------|
| **Landing / Dashboard** | `app.py` | KPI overview, pipeline, all chats |
| **Import & Analyze** | `pages/1_Upload.py` | Upload .txt or scan QR  analyze  store |
| **Chat Detail** | `pages/2_Chat_Detail.py` | Full conversation, AI summary, contact info |
| **Area Overview** | `pages/3_Area_Overview.py` | Chats grouped by region |
| **Follow-Ups** | `pages/4_Followups.py` | Priority action list |
| **Risk Flags** | `pages/5_Risk_Flags.py` | Silent deals, overdue payments, stalled negotiations |
| **Map** | `pages/6_Map.py` | Interactive region map |

---

## AI Extraction (Gemini)

Automatically extracts from messages:

- **Leads:** Contact name, phone, email, company, role
- **Deal metadata:** Status, relationship stage, urgency
- **Project:** Type (residential/commercial), primary area
- **Concrete orders:** m estimate, mix grade (C20/C30/C40), delivery needed
- **Sentiment analysis**
- **Risk flags:** Overdue payment, silent period, stalled negotiation
- **Action items:** Follow-ups, suggested actions

---

## Database

SQLite database: `db/topcrete.db`

**Tables:**
- `chats`  Chat metadata + extraction results
- `messages`  Individual messages
- `extracted_fields`  AI-extracted intelligence
- `action_items`  Follow-ups and risks

---

## Theme System

**Light / Dark / System Mode**

Colors (Light Mode):
- Primary Blue: `#0057AD`
- Gold Accent: `#DAA520`
- Dark Navy: `#1a2a4a`
- Light Background: `#f5f8fc`

---

## Configuration

**Environment variables** (`.env.txt` or `.env`):
```
GEMINI_API_KEY=your_key_here
```

**Python dependencies:**
```
streamlit==1.55.0
google-genai==1.67.0
pandas==2.3.3
folium==0.20.0
streamlit-folium==0.26.2
python-dotenv==1.0.0
requests==2.31.0
```

**Node.js dependencies:**
```
express==4.18.2
whatsapp-web.js==1.23.0
qrcode==1.5.3
puppeteer==24.39.1
```

---

## Folder Structure

```
E:\Client Products\ChatChaos-WhatsApp-Manager\
 app.py                          # Main Streamlit app
 pages/                          # Streamlit pages
    1_Upload.py
    2_Chat_Detail.py
    3_Area_Overview.py
    4_Followups.py
    5_Risk_Flags.py
    6_Map.py
 components/                     # Reusable components
    colors.py
    theme.py
    ui_components.py
    brand_new.py
    geo.py
 core/                           # Python backend
    parser.py                   # Chat file parser
    transcriber.py              # Voice transcription
    analyzer.py                 # AI extraction
    database.py                 # SQLite
    whatsapp_connector.py       # Bridge API calls
 bridge/                         # Node.js WhatsApp bridge
    server.js
    package.json
    node_modules/
 db/                             # SQLite database
    topcrete.db
 .streamlit/                     # Streamlit config
    config.toml
 requirements.txt                # Python deps
 .env.txt                        # API keys
```

---

## Data Flow

```
WhatsApp Messages
       
WhatsApp Bridge (Node.js)
       
Parser (iOS/Android formats)
       
Transcriber (voice notes)
       
Analyzer (Gemini AI)
       
SQLite Database
       
Streamlit Dashboard
```

---

## Supported Message Formats

**iOS:**
- Plain: `[DD/MM/YYYY, HH:MM:SS] Sender: message`
- Media: `[YYYY-MM-DD, H:MM:SS AM/PM] Sender: <attached: file>`

**Android:**
- `DD/MM/YYYY, HH:MM - Sender: message`

---

## AI Model

**Gemini 2.5 Flash**

Extraction prompt uses:
- Structured JSON output
- Message truncation (head 30% + tail 70% for long chats)
- Fallback to None for unparseable fields

---

## Key Features

 Live WhatsApp chat access (QR auth)  
 .txt file import (iOS/Android)  
 Voice transcription (Arabic + English)  
 AI-powered extraction (7 data types)  
 SQLite persistence  
 Interactive dashboard (7 pages)  
 Risk flag detection  
 Follow-up prioritization  
 Lebanon region mapping  
 Theme system (light/dark/system)  

---

## Known Limitations

- Map markers show region centers (not actual project locations)
- No edit/update UI for extracted fields
- Voice transcription requires Gemini API + audio files

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python | 3.13.7 |
| Web UI | Streamlit | 1.55.0 |
| AI | Gemini 2.5 Flash | Latest |
| Maps | Folium | 0.20.0 |
| Data | Pandas | 2.3.3 |
| Storage | SQLite | Built-in |
| WhatsApp | whatsapp-web.js | 1.23.0 |
| Web Server | Express.js | 4.18.2 |
| Browser | Puppeteer | 24.39.1 |

---

## Testing

Verify before deployment:

- [ ] Landing page loads with all features
- [ ] QR code scan works (test with second device)
- [ ] File upload (.txt export) works
- [ ] Messages parse correctly (check database)
- [ ] Gemini extraction runs (check extracted_fields)
- [ ] Dashboard KPIs calculate correctly
- [ ] Pipeline breakdown shows mix grades + areas
- [ ] Light mode renders cleanly
- [ ] Dark mode renders cleanly
- [ ] Mobile responsive (375px  1440px)

---

## Troubleshooting

### Bridge not connecting
```bash
# Kill existing processes
pkill -f "node server.js"

# Restart bridge
cd bridge && npm start
```

### Streamlit won't start
```bash
# Clear cache
rm -rf ~/.streamlit/cache
streamlit run app.py --logger.level=error
```

### API key not loading
- Check `.env.txt` or `.env` exists
- Verify `GEMINI_API_KEY=...` is set
- Restart Streamlit

### Database locked
```bash
# Close all connections and restart
rm db/topcrete.db
streamlit run app.py
```

---

## License

Internal use only.

---

**Status:** Production-Ready  
**Last Updated:** March 2026  
**Tech Level:** Professional B2B SaaS

