# ChatChaos System - Quick Start Guide

## Current Status

[DONE] **Backend:** Production-ready  
[DONE] **Infrastructure:** Resilient with auto-recovery  
[DONE] **Error Handling:** Comprehensive with circuit breakers  
[DONE] **Analytics:** Complete metrics engine  
[PENDING] **Frontend:** React/NextJS design in progress

---

## What's Included Now

### Core Components
- **WhatsApp Bridge** (Node.js)  Lives at `bridge/server.js`
- **Python Backend** (core logic)  All modules in `core/`
- **Streamlit UI** (temporary)  `app.py` and `pages/`
- **Database** (SQLite)  Will be created in `data/`

### New Infrastructure (This Session)
1. **Bridge Reliability**  Auto-reconnect, health checks, manual restart
2. **API Rate Limiting**  Job queue with priority system
3. **Error Handling**  Custom exceptions, circuit breakers, logging
4. **Analytics**  KPIs, trends, sentiment, risks, actions
5. **System Health**  Monitoring + Streamlit integration

---

## Startup Instructions

### Option 1: Using PowerShell Script (Recommended)

```powershell
cd "E:\Client Products\ChatChaos-WhatsApp-Manager"
.\RUN_SYSTEM.ps1
```

**Interactive menu:**
1. Start Bridge Only
2. Start Streamlit Only
3. Start React/NextJS Only
4. Start Bridge + Streamlit
5. Start Everything (when React ready)
6. System Health Check
7. Open Dashboard
8. Exit

### Option 2: Manual Startup

**Terminal 1  Start the Bridge:**
```bash
cd "E:\Client Products\ChatChaos-WhatsApp-Manager\bridge"
npm start
```

**Terminal 2  Start Streamlit:**
```bash
cd "E:\Client Products\ChatChaos-WhatsApp-Manager"
streamlit run app.py
```

**Terminal 3  Start React (when ready):**
```bash
cd "E:\Client Products\ChatChaos-WhatsApp-Manager\ui-redesign"
npm start
```

---

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Streamlit Dashboard** | http://localhost:8501 | Current UI (temporary) |
| **React Dashboard** | http://localhost:3000 | New modern UI (coming soon) |
| **Bridge API** | http://localhost:3001 | WhatsApp connection |
| **Health Check** | http://localhost:3001/health | System status |

---

## Configuration

### Environment Variables (.env.txt or .env)

```
GEMINI_API_KEY=your_api_key_here
```

### Optional Settings

**Bridge (bridge/.env):**
```
PORT=3001
NODE_ENV=production
```

**Python (app.py):**
- API key loading is automatic from `.env.txt` or `.env`
- Database path: `data/assistant.db` (auto-created)
- Logs path: `logs/` (auto-created)

---

## System Architecture

```

          WhatsApp Web Browser           
        (WhatsApp Bridge Auth)           

                   
        
          WhatsApp Bridge    
          (Node.js/Express)  
          Port 3001          
        
                   
        REST API (JSON)
                   
    
                                
                                
 Parser        Analyzer        Database
(Messages)   (Gemini AI)      (SQLite)
                                
    
            
    
      Analytics &   
      Error Handler 
      Rate Limiter  
    
            
    
                              
                              
 Streamlit UI            React/NextJS UI
 (Legacy)              (Modern - Coming)
 Port 8501             Port 3000
```

---

## Key Features Ready Now

### Bridge Reliability
- [DONE] Auto-reconnection with exponential backoff
- [DONE] Health check endpoint with full metrics
- [DONE] Heartbeat monitoring every 60 seconds
- [DONE] Manual restart button in UI
- [DONE] Graceful shutdown handling

### API Rate Limiting
- [DONE] Token bucket rate limiter
- [DONE] Job queue with priority (HIGH/NORMAL/LOW)
- [DONE] Exponential backoff retry (max 3 attempts)
- [DONE] Rate limit metrics visible to users
- [DONE] Dead letter queue for failed jobs

### Error Handling
- [DONE] Custom exception types for different errors
- [DONE] Circuit breakers for failing APIs
- [DONE] User-friendly error messages
- [DONE] Structured logging to `logs/error.log`
- [DONE] Automatic recovery strategies

### Analytics
- [DONE] Chat statistics (total, active, messages)
- [DONE] KPI metrics (hot leads, follow-ups, risks)
- [DONE] Pipeline breakdown (by mix grade, region)
- [DONE] Trend analysis over time
- [DONE] Sentiment distribution
- [DONE] Risk analysis (overdue, silent, stalled)
- [DONE] Action item summaries

### System Health
- [DONE] Real-time service status monitoring
- [DONE] Recommendations engine
- [DONE] Health dashboard in Streamlit sidebar
- [DONE] REST API for health checks

---

## What's Coming Next

### 1. React/NextJS Design (In Progress)
- Modern 3-column chat interface
- Full theme system (light/dark/system)
- Real-time updates via WebSocket
- Health status widget
- Queue progress tracking
- Analytics dashboard integration

**Timeline:** Design team building now (Claude Code session active)

### 2. User Authentication (After Design)
- OAuth2 login (Google/GitHub)
- Session management
- Role-based access control
- Audit logging

### 3. Security Hardening (Post-Launch)
- API key encryption
- Database encryption at rest
- GDPR compliance
- Data retention policies

---

## Troubleshooting

### Bridge Won't Start
```bash
# Check if port 3001 is in use
netstat -ano | findstr :3001

# Kill the process if needed
taskkill /PID <PID> /F
```

### Streamlit Not Loading
```bash
# Clear cache and restart
rm -r ~/.streamlit/cache
streamlit run app.py --logger.level=debug
```

### API Key Not Found
```bash
# Ensure .env.txt exists in project root
echo "GEMINI_API_KEY=your_key" > .env.txt
```

### Database Locked
```bash
# Remove lock files and restart
rm data/assistant.db-shm
rm data/assistant.db-wal
```

---

## Development Notes

### Adding New Features
1. **Backend:** Add to `core/` modules
2. **Error handling:** Use `@safe_operation()` decorator
3. **Logging:** Use `ErrorLogger.log_error()`
4. **Monitoring:** Update `SystemHealth` class
5. **Analytics:** Add to `ChatAnalytics` class

### Using the Rate Limiter
```python
from core.rate_limiter import extraction_queue

# Add job
job_id = extraction_queue.add_job(
    chat_id=123,
    text="Message text",
    priority="high"  # or "normal", "low"
)

# Check status
status = extraction_queue.get_job_status(job_id)
print(status)

# Get result
result = extraction_queue.get_completed_result(job_id)
```

### Using Error Handling
```python
from core.error_handler import safe_operation, ChatChaosError

@safe_operation("my_operation", retries=3, backoff_factor=2.0)
def my_function():
    # Your code here
    pass

# Or manually
try:
    result = my_function()
except ChatChaosError as e:
    print(f"User message: {e.user_message}")
    print(f"Recovery: {e.recovery_suggestion}")
```

### Using Analytics
```python
from core.analytics import ChatAnalytics, ExportAnalytics

# Get specific metrics
kpis = ChatAnalytics.get_kpi_metrics()
print(kpis["hot_leads"], kpis["pending_followups"])

# Get complete report
report = ExportAnalytics.get_full_report()
```

---

## File Structure

```
ChatChaos-WhatsApp-Manager/
 app.py                      # Main Streamlit app
 bridge/                     # WhatsApp Bridge (Node.js)
    server.js              # Express server + whatsapp-web.js
    package.json
    .wwebjs_auth/          # Auth tokens (persistent)
 core/                       # Python backend
    analyzer.py            # Gemini AI extraction
    database.py            # SQLite operations
    parser.py              # WhatsApp .txt parser
    transcriber.py         # Voice transcription
    rate_limiter.py        # Job queue + rate limiting  NEW
    error_handler.py       # Error handling + circuit breakers  NEW
    analytics.py           # KPIs & trends  NEW
    system_health.py       # Health monitoring  NEW
 pages/                      # Streamlit pages
    1_Upload.py
    2_Chat_Detail.py
    3_Area_Overview.py
    4_Followups.py
    5_Risk_Flags.py
    6_Map.py
 components/                 # UI components
    colors.py
    theme.py
    ui_components.py
    brand.py
 data/                       # Database & files
    (auto-created)
 logs/                       # Log files
    error.log              # Error logging
 ui-redesign/               # React/NextJS (coming)
    (in progress)
 .streamlit/                # Streamlit config
 requirements.txt           # Python dependencies
 package.json               # Node dependencies
 README.md                  # Documentation
 COMPLETION_STATUS.md       # Phase 1 completion  NEW
 IMPROVEMENTS_ROADMAP.md    # Full roadmap
 RUN_SYSTEM.ps1            # Startup script  NEW
 STARTUP_GUIDE.md          # This file  NEW
```

---

## When React Design Arrives

1. **Design team completes build**  `ui-redesign/` folder appears
2. **Run system startup:**
   ```powershell
   .\RUN_SYSTEM.ps1
   ```
3. **Select option 5**  Start Everything
4. **See all three services running:**
   - Bridge on :3001
   - Streamlit on :8501
   - React on :3000
5. **Demo the system**  Open http://localhost:3000

---

## Next Steps

1. [PENDING] **Wait for React design completion**
   - Claude Code is building the full application
   - Estimated: 1-2 hours remaining

2. [DONE] **When design arrives:**
   ```powershell
   .\RUN_SYSTEM.ps1
   # Choose option 5: Start Everything
   ```

3. [DONE] **View live system:**
   - React modern UI: http://localhost:3000
   - Analytics dashboard: http://localhost:3000/analytics
   - Bridge health: http://localhost:3001/health

4.  **After demo:**
   - Integrate additional improvements
   - Add user authentication
   - Deploy to production

---

## Questions?

Refer to:
- **Architecture:** `README.md`
- **Improvements:** `IMPROVEMENTS_ROADMAP.md`
- **Completion:** `COMPLETION_STATUS.md`
- **Code examples:** See `core/` modules with docstrings

**Support contacts:**
- Bridge issues  Check `bridge/server.js` for logging
- API issues  Check `logs/error.log`
- UI issues  Browser console (F12) + `logs/error.log`

---

**Status:** Ready for React integration  
**Last Updated:** March 18, 2026  
**Version:** 1.0 (Infrastructure Complete)

