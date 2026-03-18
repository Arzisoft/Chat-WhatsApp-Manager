CHATCHAOS WHATSAPP MANAGER - DEPLOYMENT GUIDE
==============================================

QUICK START
===========

1. ENVIRONMENT SETUP
   Create .env.txt in project root with:
   ```
   GEMINI_API_KEY=AIzaSy...
   ```

2. INSTALL DEPENDENCIES
   
   Backend (Python):
   ```bash
   pip install python-dotenv google-genai requests
   ```
   
   Frontend (Streamlit):
   ```bash
   pip install streamlit pillow
   ```
   
   Bridge (Node.js):
   ```bash
   cd bridge
   npm install
   ```

3. STARTUP CHECKS
   ```bash
   python startup_check.py
   ```
   Expected: 14/15+ checks passed

4. INITIALIZE DATABASE
   ```bash
   python -c "from core.database import init_db; init_db()"
   ```

5. RUN TESTS
   ```bash
   python tests/test_integration.py
   ```
   Expected: 57/57 tests passed

6. START BRIDGE (Terminal 1)
   ```bash
   cd bridge
   node server.js
   ```
   Visit http://localhost:3001/status and scan QR code

7. START FRONTEND (Terminal 2)
   ```bash
   streamlit run app.py
   ```
   Opens at http://localhost:8501

DETAILED DEPLOYMENT
===================

STEP 1: ENVIRONMENT CONFIGURATION
----------------------------------

Create .env.txt in project root:

```
# Gemini API Configuration
GEMINI_API_KEY=AIzaSy... (paste your actual key)

# Optional: Database path (defaults to data/assistant.db)
DB_PATH=data/assistant.db

# Optional: Bridge server URL (for Streamlit)
BRIDGE_URL=http://localhost:3001

# Optional: Log level (INFO, DEBUG, WARNING, ERROR)
LOG_LEVEL=INFO
```

Get GEMINI_API_KEY:
1. Go to https://ai.google.dev/
2. Click "Get API Key"
3. Create new API key for ChatChaos
4. Copy and paste into .env.txt

STEP 2: PYTHON DEPENDENCIES
----------------------------

Core requirements:
```
python-dotenv           # Load .env.txt
google-genai           # Gemini API client
requests               # HTTP requests for bridge
sqlite3                # Database (built-in)
```

For UI (Streamlit):
```
streamlit              # Web framework
pillow                 # Image processing
```

Installation:
```bash
pip install --upgrade pip
pip install python-dotenv google-genai requests
pip install streamlit pillow
```

Optional for development:
```bash
pip install pytest black flake8
```

STEP 3: NODE.JS BRIDGE SETUP
----------------------------

Prerequisites:
- Node.js 14+ (https://nodejs.org/)
- Chromium/Chrome browser (Puppeteer will use system Chrome)
- WhatsApp account with active mobile device

Installation:
```bash
cd bridge
npm install
```

Dependencies:
- whatsapp-web.js: WhatsApp Web client
- express: HTTP server
- qrcode: QR code generation

STEP 4: DATABASE INITIALIZATION
--------------------------------

Run startup checks:
```bash
python startup_check.py
```

This will:
1. Create data/ directory
2. Create logs/ directory
3. Initialize SQLite database
4. Verify modules load correctly

Manual database init if needed:
```bash
python -c "from core.database import init_db; init_db()"
```

Database created at: data/assistant.db

STEP 5: SYSTEM VERIFICATION
----------------------------

Run all integration tests:
```bash
python tests/test_integration.py
```

Expected output:
```
============================================================
CHATCHAOS WHATSAPP MANAGER - INTEGRATION TESTS
============================================================

=== Testing Models ===
  [PASS] ParsedMessage creation
  ...
=== End-to-End Integration Test ===
  [PASS] E2E parse exports
  ...

============================================================
Test Summary: 57/57 passed
============================================================
```

All 57 tests must pass before proceeding.

STEP 6: BRIDGE STARTUP
---------------------

Start WhatsApp bridge:
```bash
cd bridge
node server.js
```

Expected output:
```
[bridge] API running → http://localhost:3001
[bridge] Initialising WhatsApp client...
[bridge] QR ready — scan with WhatsApp
```

Check bridge status:
```bash
curl http://localhost:3001/health
```

Response should include:
- status: "qr" or "ready"
- qr_ready: true (if needs scan)
- uptime_seconds: > 0

Scan QR Code:
1. Keep terminal open
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices
4. Click "Link a device"
5. Scan QR code from bridge console
6. Approve login on phone

Once authenticated:
- status changes to "ready"
- qr_image becomes null
- Can proceed with chat import

STEP 7: STREAMLIT FRONTEND
--------------------------

Start Streamlit app:
```bash
streamlit run app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Open browser to http://localhost:8501

Features available:
- Dashboard with KPI cards
- Chat import interface
- Analysis results
- Pipeline visualization
- Risk detection
- Action items tracking

PRODUCTION DEPLOYMENT
=====================

DOCKER CONTAINERIZATION
-----------------------

Backend Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN pip install streamlit google-genai

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

Bridge Dockerfile:
```dockerfile
FROM node:18-slim

WORKDIR /app
COPY bridge/ .
RUN npm install

EXPOSE 3001
CMD ["node", "server.js"]
```

Build and run:
```bash
docker build -t chatchaos-backend .
docker run -p 8501:8501 -v $(pwd)/data:/app/data -e GEMINI_API_KEY=... chatchaos-backend
```

CLOUD DEPLOYMENT
----------------

AWS Deployment:
1. Create EC2 instance (t3.small minimum)
2. Install Node.js and Python
3. Clone repository
4. Set environment variables in Systems Manager Parameter Store
5. Create RDS SQLite instance (or use local)
6. Deploy using CodeDeploy

GCP Deployment:
1. Create Cloud Run service
2. Upload Docker image to Container Registry
3. Set environment variables in Cloud Run configuration
4. Deploy with 2GB memory, 15min timeout

Azure Deployment:
1. Create Container Instance
2. Set environment variables
3. Mount persistent storage for data/
4. Expose ports 3001 (bridge) and 8501 (frontend)

MONITORING & LOGGING
====================

Health Checks
1. Bridge health: curl http://localhost:3001/health
2. Database: Errors logged to logs/error.log
3. API: Monitor rate limit usage

Log Files
- logs/error.log: All errors and warnings
- data/assistant.db: SQLite database

Metrics to Monitor
- API rate limit usage (max 30 req/min)
- Database query times
- Bridge reconnection attempts
- Queue length (should be < 50)

Performance Tuning
- Max connections: 10
- Query timeout: 30s
- Rate limit: 30 requests/60s
- Circuit breaker threshold: 5 failures

TROUBLESHOOTING
================

Issue: "No GEMINI_API_KEY found"
Solution: Create .env.txt with your API key

Issue: "Bridge connection refused"
Solution: Start bridge with: cd bridge && node server.js

Issue: "Database locked"
Solution: Close other processes, check file permissions

Issue: "Rate limit exceeded (429)"
Solution: System auto-retries with exponential backoff

Issue: "Memory usage increasing"
Solution: Check queue length, clear old jobs

MAINTENANCE
===========

Regular Tasks
1. Monitor logs/error.log weekly
2. Check database size (data/assistant.db)
3. Review rate limit usage
4. Verify bridge uptime

Database Maintenance
1. Backup data/assistant.db regularly
2. Run VACUUM to optimize (SQLite)
3. Archive old chat records

Version Updates
1. Test new Gemini API versions
2. Update whatsapp-web.js when available
3. Keep Python packages current

Scaling
1. Implement database clustering
2. Add Redis for caching
3. Deploy multiple bridges for load balancing

SECURITY CHECKLIST
==================

[ ] API key in .env.txt, never in code
[ ] Database file not world-readable
[ ] HTTPS for production deployment
[ ] Rate limiting enabled
[ ] Error logging doesn't expose secrets
[ ] Input validation on all user data
[ ] SQL injection prevention (parameterized queries)
[ ] XSS prevention in Streamlit
[ ] CORS headers configured
[ ] Authentication for admin functions

ROLLBACK PROCEDURE
==================

If deployment fails:
1. Stop current instance
2. Revert code to previous version: git checkout <commit>
3. Restore database backup: cp backup.db data/assistant.db
4. Run startup_check.py again
5. Restart services

Version control:
```bash
git tag -a v1.0.0 -m "Production release"
git push origin v1.0.0
```

SUPPORT & MONITORING
====================

Real-time Monitoring:
```bash
# Watch logs in real-time
tail -f logs/error.log

# Monitor bridge status
watch -n 5 'curl -s http://localhost:3001/health | python -m json.tool'

# Check database size
du -sh data/assistant.db
```

Get System Status:
```bash
python -c "from core.system_health import SystemHealth; import json; print(json.dumps(SystemHealth.get_full_status(), indent=2))"
```

NEXT STEPS
==========

After deployment:
1. Run startup_check.py to verify all systems
2. Run tests/test_integration.py to validate
3. Monitor logs/error.log for first 24 hours
4. Test with sample WhatsApp chats
5. Configure backups for data/assistant.db
6. Set up monitoring/alerting

Expected System Behavior:
- Bridge auto-reconnects on disconnect
- API retries with exponential backoff on rate limit
- Database transactions are atomic
- Errors logged with full context
- System recovers from transient failures
- Health checks every 60 seconds

Success Criteria:
- All 57 tests pass
- startup_check.py: 15/15 checks pass
- Bridge shows "ready" status
- No errors in logs for 1 hour
- Can import and analyze sample chat
- Dashboard displays KPIs correctly

---

For support or issues, consult:
1. BACKEND_COMPLETION_REPORT.md - Full technical details
2. logs/error.log - Detailed error logs
3. SYSTEM_AUDIT.md - Architecture overview
