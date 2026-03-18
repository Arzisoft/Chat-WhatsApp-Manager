# ChatChaos Improvements Roadmap

## Priority: MUST HAVE (Before Production)

### 1. WhatsApp Bridge Reliability
**Status:** IN PROGRESS  
**Files affected:** `bridge/server.js`

- [ ] Auto-reconnection logic with exponential backoff
- [ ] Health check endpoint (`/health`)
- [ ] Heartbeat monitoring
- [ ] Error recovery for Puppeteer crashes
- [ ] Manual restart button in Streamlit UI

**Effort:** 2-3 hours  
**Impact:** HIGH (prevents loss of chat access)

---

### 2. User Authentication & Security
**Status:** PENDING  
**Files affected:** `app.py`, `pages/*`, new `auth/` module

Requirements:
- [ ] OAuth2 authentication (Google / GitHub)
- [ ] User session management
- [ ] Role-based access control (Admin, Operator, Viewer)
- [ ] API key encryption (move from .env.txt to AWS Secrets)
- [ ] Audit logging (who accessed what, when)
- [ ] Rate limiting per user

**Effort:** 4-6 hours  
**Impact:** CRITICAL (data security, compliance)

---

### 3. Gemini API Rate Limiting & Queue System
**Status:** PENDING  
**Files affected:** `core/analyzer.py`, new `core/queue.py`

Requirements:
- [ ] Job queue for async extraction (Bull or similar)
- [ ] Rate limit handling (429 retry logic)
- [ ] Exponential backoff
- [ ] Progress tracking for bulk imports
- [ ] Dead letter queue for failed extractions
- [ ] Cost tracking (API spend)

**Effort:** 3-4 hours  
**Impact:** HIGH (prevents API throttling, enables bulk operations)

---

### 4. Better Error Handling & User Messages
**Status:** PENDING  
**Files affected:** All Python modules, `app.py`, `pages/*`

Requirements:
- [ ] Try-catch blocks around API calls
- [ ] User-friendly error messages
- [ ] Error logging to file
- [ ] Circuit breaker pattern for failing services
- [ ] Retry logic with backoff
- [ ] Health status dashboard

**Effort:** 2-3 hours  
**Impact:** MEDIUM (improves UX, easier debugging)

---

## Phase 1 Execution Order

1. **Bridge Reliability** (start immediately)
2. **API Rate Limiting** (parallel with bridge)
3. **Error Handling** (parallel with bridge)
4. **User Auth** (after design is integrated)

---

## Implementation Details

### Phase 1.1: Bridge Reliability

**File:** `bridge/server.js`

```javascript
// ADD: Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: state, 
        uptime: process.uptime(),
        timestamp: new Date(),
        qr_ready: qrImage ? true : false
    });
});

// ADD: Auto-reconnection on disconnect
client.on('disconnected', (reason) => {
    state = 'disconnected';
    console.log(`[bridge] Disconnected (${reason}), retrying in 5s...`);
    
    setTimeout(() => {
        console.log('[bridge] Attempting reconnect...');
        client.initialize().catch(err => {
            console.error('[bridge] Reconnect failed:', err);
        });
    }, 5000);
});

// ADD: Heartbeat monitoring
setInterval(() => {
    if (state === 'ready') {
        client.getWWeb()
            .then(() => {
                console.log('[bridge] Heartbeat OK');
            })
            .catch(err => {
                console.error('[bridge] Heartbeat failed, reinitializing...');
                client.initialize();
            });
    }
}, 60000); // Every 60 seconds

// ADD: Global error handler
process.on('uncaughtException', (error) => {
    console.error('[bridge] Uncaught exception:', error);
    console.log('[bridge] Attempting graceful restart...');
    
    setTimeout(() => {
        process.exit(1);
    }, 2000);
});
```

**Streamlit Integration:**

```python
# In app.py sidebar
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Bridge Status"):
            try:
                response = requests.get('http://localhost:3000/health', timeout=2)
                data = response.json()
                if data['status'] == 'ready':
                    st.success(f"Bridge Online (uptime: {int(data['uptime'])}s)")
                else:
                    st.warning(f"Bridge Status: {data['status']}")
            except:
                st.error("Bridge Offline")
    
    with col2:
        if st.button(" Restart Bridge"):
            os.system("pkill -f 'node server.js'")
            st.success("Bridge restarting...")
```

---

### Phase 1.2: API Rate Limiting

**New File:** `core/queue.py`

```python
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        now = datetime.now().timestamp()
        window_start = now - self.window_seconds
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside window
        self.requests[key] = [
            t for t in self.requests[key] 
            if t > window_start
        ]
        
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_retry_after(self, key: str) -> int:
        """Returns seconds until next request allowed"""
        if not self.requests.get(key):
            return 0
        
        oldest = min(self.requests[key])
        retry_at = oldest + self.window_seconds
        return max(0, int(retry_at - datetime.now().timestamp()) + 1)

class ExtractionQueue:
    def __init__(self):
        self.queue: List[Dict] = []
        self.active_jobs: Dict[str, str] = {}  # job_id -> status
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
    
    def add_job(self, chat_id: int, text: str, priority: str = "normal") -> str:
        """Add extraction job to queue"""
        job_id = f"job_{chat_id}_{datetime.now().timestamp()}"
        
        job = {
            "job_id": job_id,
            "chat_id": chat_id,
            "text": text,
            "priority": priority,  # "high", "normal", "low"
            "created_at": datetime.now().isoformat(),
            "status": "queued",
            "retries": 0,
            "max_retries": 3,
        }
        
        self.queue.append(job)
        self.active_jobs[job_id] = "queued"
        
        # Sort by priority
        priority_order = {"high": 0, "normal": 1, "low": 2}
        self.queue.sort(key=lambda x: priority_order.get(x["priority"], 1))
        
        return job_id
    
    async def process_queue(self, analyzer_func):
        """Process queue with rate limiting"""
        while self.queue:
            job = self.queue.pop(0)
            
            # Check rate limit
            if not self.rate_limiter.is_allowed("gemini"):
                retry_after = self.rate_limiter.get_retry_after("gemini")
                job["status"] = "rate_limited"
                self.queue.insert(0, job)  # Back to queue
                
                print(f"[queue] Rate limited, retry in {retry_after}s")
                await asyncio.sleep(retry_after)
                continue
            
            # Process job
            try:
                self.active_jobs[job["job_id"]] = "processing"
                result = analyzer_func(job["text"])
                
                job["status"] = "completed"
                job["result"] = result
                self.active_jobs[job["job_id"]] = "completed"
                
            except Exception as e:
                job["retries"] += 1
                
                if job["retries"] < job["max_retries"]:
                    job["status"] = "retrying"
                    self.queue.append(job)  # Back to queue
                    await asyncio.sleep(2 ** job["retries"])  # Exponential backoff
                else:
                    job["status"] = "failed"
                    job["error"] = str(e)
                    self.active_jobs[job["job_id"]] = "failed"
    
    def get_status(self, job_id: str) -> Dict:
        """Get job status"""
        return {
            "job_id": job_id,
            "status": self.active_jobs.get(job_id, "unknown"),
            "queue_length": len(self.queue),
        }
```

**Usage in analyzer.py:**

```python
from core.queue import ExtractionQueue

queue = ExtractionQueue()

async def bulk_extract(chats: List[str]):
    """Extract multiple chats with rate limiting"""
    for i, chat_text in enumerate(chats):
        priority = "high" if i < 5 else "normal"
        job_id = queue.add_job(i, chat_text, priority)
        print(f"Job {job_id} queued")
    
    await queue.process_queue(extract_from_text)
```

---

### Phase 1.3: Error Handling

**Update:** `core/analyzer.py`

```python
import logging
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(
    filename='logs/analyzer.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors"""
    pass

def safe_extract(text: str, max_retries: int = 3) -> Optional[Dict[Any, Any]]:
    """Extract with retry logic and error handling"""
    
    for attempt in range(max_retries):
        try:
            result = extract_from_text(text)
            logger.info(f"Extraction successful (attempt {attempt + 1})")
            return result
        
        except APIError as e:
            if "429" in str(e):  # Rate limit
                wait_time = 60 * (2 ** attempt)
                logger.warning(f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
                continue
            
            elif "500" in str(e):  # Server error
                wait_time = 5 * (2 ** attempt)
                logger.warning(f"Server error, retrying in {wait_time}s")
                time.sleep(wait_time)
                continue
            
            else:
                logger.error(f"Extraction failed: {e}")
                return None
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return None
    
    logger.error(f"Max retries ({max_retries}) exceeded")
    return None
```

---

### Phase 1.4: User Authentication (Post-Design)

**New File:** `auth/oauth.py`

```python
import streamlit as st
from authlib.integrations.requests_client import OAuth2Session

# OAuth2 configuration
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"

def init_oauth():
    """Initialize OAuth2 session"""
    if 'oauth_token' not in st.session_state:
        st.session_state.oauth_token = None
    if 'user' not in st.session_state:
        st.session_state.user = None

def login_with_google():
    """OAuth2 login flow"""
    client = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri="http://localhost:8501/callback",
        scope=['openid', 'profile', 'email']
    )
    
    # Redirect to Google
    uri, state = client.create_authorization_url('https://accounts.google.com/o/oauth2/auth')
    st.markdown(f"[Login with Google]({uri})")

def check_auth():
    """Check if user is authenticated"""
    if st.session_state.user is None:
        st.warning("Please log in to continue")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                if st.button(" Google Login"):
                    login_with_google()
            with col2:
                if st.button(" Manual API Key"):
                    st.session_state.auth_method = "api_key"
        return False
    return True
```

---

## Timeline

- **Week 1:** Bridge reliability + API rate limiting
- **Week 2:** Error handling + logging
- **Week 3:** User authentication (after design integration)
- **Week 4:** Audit logging + security hardening

---

## Success Criteria

- [ ] Bridge stays online for 30 days without manual restart
- [ ] API rate limits handled gracefully (no user-facing errors)
- [ ] All errors logged with actionable messages
- [ ] Users can log in with Google OAuth
- [ ] Audit trail shows all data access
- [ ] System passes security audit

