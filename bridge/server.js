/**
 * TopCrete WhatsApp Bridge
 * Uses whatsapp-web.js (no Selenium scraping) to provide a clean REST API
 * for the Streamlit app to consume.
 *
 * Endpoints:
 *   GET  /status            → { status, qr_image }
 *   GET  /chats             → [ { id, name, is_group, timestamp, unread } ]
 *   GET  /messages/:chat_id → [ { id, timestamp, from, body, type, is_media } ]
 *   POST /disconnect        → { ok }
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode  = require('qrcode');

const app = express();
app.use(express.json());

// ── State ─────────────────────────────────────────────────────────────────────
let state    = 'connecting';   // connecting | qr | ready | disconnected
let qrImage  = null;           // base64 PNG data-URL of current QR
let uptime   = Date.now();     // Track bridge uptime
let reconnectAttempts = 0;     // Reconnection attempt counter
let lastHeartbeat = Date.now(); // Last successful heartbeat
const MAX_RECONNECT_ATTEMPTS = 5;
const HEARTBEAT_INTERVAL = 60000; // 60 seconds

// ── WhatsApp client ───────────────────────────────────────────────────────────
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './.wwebjs_auth' }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
        ],
    },
});

client.on('qr', async (qr) => {
    state    = 'qr';
    qrImage  = await qrcode.toDataURL(qr);
    console.log('[bridge] QR ready — scan with WhatsApp');
});

client.on('ready', () => {
    state   = 'ready';
    qrImage = null;
    console.log('[bridge] WhatsApp connected and ready');
});

client.on('authenticated', () => {
    state = 'authenticated';
    console.log('[bridge] Authenticated — loading chats...');
});

client.on('auth_failure', (msg) => {
    state = 'auth_failure';
    console.error('[bridge] Auth failed:', msg);
});

client.on('disconnected', (reason) => {
    state   = 'disconnected';
    qrImage = null;
    console.log('[bridge] Disconnected:', reason);
    
    // Auto-reconnect with exponential backoff
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        const waitTime = Math.min(5000 * Math.pow(2, reconnectAttempts), 30000);
        reconnectAttempts++;
        console.log(`[bridge] Reconnecting in ${waitTime}ms (attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        setTimeout(() => {
            client.initialize().catch(err => {
                console.error('[bridge] Reconnection failed:', err.message);
            });
        }, waitTime);
    } else {
        console.error('[bridge] Max reconnection attempts reached. Manual restart required.');
        state = 'error_max_reconnects';
    }
});

// Global error handler
process.on('uncaughtException', (error) => {
    console.error('[bridge] Uncaught exception:', error);
    console.log('[bridge] Attempting graceful restart...');
    setTimeout(() => {
        process.exit(1);
    }, 2000);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('[bridge] Unhandled rejection:', reason);
});

client.initialize().catch(err => {
    console.error('[bridge] Init error:', err.message);
    state = 'error';
});

// ── REST API ──────────────────────────────────────────────────────────────────

// Health check endpoint (detailed)
app.get('/health', (req, res) => {
    const currentTime = Date.now();
    res.json({
        status: state,
        uptime_ms: currentTime - uptime,
        uptime_seconds: Math.floor((currentTime - uptime) / 1000),
        last_heartbeat_ms: currentTime - lastHeartbeat,
        reconnect_attempts: reconnectAttempts,
        max_reconnect_attempts: MAX_RECONNECT_ATTEMPTS,
        timestamp: new Date().toISOString(),
        qr_ready: qrImage ? true : false,
    });
});

// Status + QR (legacy endpoint)
app.get('/status', (req, res) => {
    res.json({ status: state, qr_image: qrImage });
});

// List chats (max 100)
app.get('/chats', async (req, res) => {
    if (state !== 'ready') {
        return res.status(503).json({ error: `Not ready (state: ${state})` });
    }
    try {
        const chats = await client.getChats();
        const result = await Promise.all(chats.map(async c => {
            let wa_name = null, wa_status = null, wa_about = null;
            try {
                const contact = await c.getContact();
                wa_name   = contact.pushname || contact.name || null;
                wa_about  = contact.statusMute ? null : (await contact.getAbout()) || null;
            } catch (_) {}
            return {
                id:            c.id._serialized,
                name:          c.name || wa_name || c.id.user,
                wa_name,
                wa_about,
                is_group:      c.isGroup,
                is_archived:   c.archived ?? false,
                timestamp:     c.timestamp,
                unread:        c.unreadCount,
                last_body:     c.lastMessage?.body   || '',
                last_type:     c.lastMessage?.type   || '',
                last_from_me:  c.lastMessage?.fromMe ?? null,
                msg_count:     c.msgs?.length        ?? null,
            };
        }));
        res.json(result);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Fetch messages for a chat
app.get('/messages/:chat_id', async (req, res) => {
    if (state !== 'ready') {
        return res.status(503).json({ error: `Not ready (state: ${state})` });
    }
    const limit = parseInt(req.query.limit || '99999');
    try {
        const chat     = await client.getChatById(req.params.chat_id);
        const messages = await chat.fetchMessages({ limit });
        const result   = messages.map(m => ({
            id:           m.id._serialized,
            timestamp:    m.timestamp,
            from:         m.author || m.from || '',
            body:         m.body   || '',
            type:         m.type,
            is_media:     m.hasMedia,
            is_voice:     m.type === 'ptt',
        }));
        res.json(result);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Download media for a message (voice notes, images, etc.)
app.get('/media/:message_id', async (req, res) => {
    if (state !== 'ready') {
        return res.status(503).json({ error: `Not ready (state: ${state})` });
    }
    try {
        const msg   = await client.getMessageById(req.params.message_id);
        if (!msg || !msg.hasMedia) {
            return res.status(404).json({ error: 'No media on this message' });
        }
        const media = await msg.downloadMedia();
        res.json({
            data:     media.data,       // base64
            mimetype: media.mimetype,
            filename: media.filename || `voice_${req.params.message_id}.ogg`,
        });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Disconnect / logout
app.post('/disconnect', async (req, res) => {
    try {
        await client.destroy();
        state   = 'disconnected';
        qrImage = null;
        res.json({ ok: true });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Manual restart endpoint
app.post('/restart', async (req, res) => {
    try {
        console.log('[bridge] Manual restart requested');
        await client.destroy();
        state = 'connecting';
        qrImage = null;
        reconnectAttempts = 0;
        
        setTimeout(() => {
            client.initialize().catch(err => {
                console.error('[bridge] Restart initialization failed:', err.message);
            });
        }, 1000);
        
        res.json({ ok: true, message: 'Bridge restarting...' });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// ── Heartbeat monitoring ──────────────────────────────────────────────────────
setInterval(() => {
    if (state === 'ready') {
        client.getWWeb()
            .then(() => {
                lastHeartbeat = Date.now();
                console.log('[bridge] Heartbeat OK');
            })
            .catch(err => {
                console.error('[bridge] Heartbeat failed:', err.message);
                console.log('[bridge] Attempting to reinitialize...');
                client.initialize().catch(e => {
                    console.error('[bridge] Reinitialization failed:', e.message);
                });
            });
    }
}, HEARTBEAT_INTERVAL);

// ── Start server ──────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3001;
const server = app.listen(PORT, () => {
    console.log(`[bridge] API running → http://localhost:${PORT}`);
    console.log('[bridge] Initialising WhatsApp client...');
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('[bridge] SIGTERM signal, shutting down gracefully...');
    server.close(() => {
        console.log('[bridge] HTTP server closed');
        client.destroy().then(() => {
            console.log('[bridge] WhatsApp client destroyed');
            process.exit(0);
        }).catch(err => {
            console.error('[bridge] Error destroying client:', err.message);
            process.exit(1);
        });
    });
});

console.log('[bridge] Ready for graceful shutdown (SIGTERM)');
