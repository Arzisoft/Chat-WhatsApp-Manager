"""
System health monitoring for ChatChaos.
Provides real-time status of all critical services.
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
from core.error_handler import (
    check_gemini_health,
    check_database_health,
    check_bridge_health,
    ErrorLogger
)
from core.rate_limiter import extraction_queue

class SystemHealth:
    """Monitor system health"""
    
    @staticmethod
    def get_bridge_status() -> Dict[str, Any]:
        """Get WhatsApp bridge status"""
        try:
            response = requests.get('http://localhost:3001/health', timeout=5)
            data = response.json()
            return {
                "status": "online",
                "bridge_status": data.get('status'),
                "uptime_seconds": data.get('uptime_seconds'),
                "last_heartbeat_ms": data.get('last_heartbeat_ms'),
                "reconnect_attempts": data.get('reconnect_attempts'),
                "qr_ready": data.get('qr_ready'),
                "timestamp": datetime.now().isoformat(),
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "offline",
                "error": "Cannot connect to bridge",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    @staticmethod
    def get_api_status() -> Dict[str, Any]:
        """Get Gemini API status"""
        is_healthy = check_gemini_health()
        return {
            "status": "online" if is_healthy else "offline",
            "service": "Gemini 2.5 Flash",
            "healthy": is_healthy,
            "timestamp": datetime.now().isoformat(),
        }
    
    @staticmethod
    def get_database_status() -> Dict[str, Any]:
        """Get database status"""
        is_healthy = check_database_health()
        return {
            "status": "online" if is_healthy else "offline",
            "service": "SQLite",
            "healthy": is_healthy,
            "timestamp": datetime.now().isoformat(),
        }
    
    @staticmethod
    def get_queue_status() -> Dict[str, Any]:
        """Get job queue status"""
        queue_status = extraction_queue.get_queue_status()
        return {
            "queue_length": queue_status["queue_length"],
            "active_jobs": queue_status["active_jobs"],
            "completed_jobs": queue_status["completed_jobs"],
            "rate_limit": queue_status["rate_limit"],
            "timestamp": datetime.now().isoformat(),
        }
    
    @staticmethod
    def get_full_status() -> Dict[str, Any]:
        """Get complete system status"""
        bridge = SystemHealth.get_bridge_status()
        api = SystemHealth.get_api_status()
        db = SystemHealth.get_database_status()
        queue = SystemHealth.get_queue_status()
        
        # Determine overall health
        all_healthy = (
            bridge.get("status") == "online" and
            api.get("healthy") and
            db.get("healthy")
        )
        
        overall_status = "healthy" if all_healthy else (
            "degraded" if any([
                s.get("status") == "offline" for s in [bridge, api, db]
            ]) else "unknown"
        )
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "whatsapp_bridge": bridge,
                "gemini_api": api,
                "database": db,
                "job_queue": queue,
            },
            "recommendations": SystemHealth._get_recommendations(overall_status, {
                "bridge": bridge,
                "api": api,
                "db": db,
                "queue": queue,
            }),
        }
    
    @staticmethod
    def _get_recommendations(status: str, services: Dict[str, Any]) -> list:
        """Get recommendations based on status"""
        recommendations = []
        
        bridge = services["bridge"]
        api = services["api"]
        db = services["db"]
        queue = services["queue"]
        
        # Bridge issues
        if bridge.get("status") == "offline":
            recommendations.append({
                "severity": "critical",
                "message": "WhatsApp bridge is offline",
                "action": "Restart the bridge server (click 'Restart Bridge' button)",
            })
        elif (bridge.get("reconnect_attempts") or 0) > 2:
            recommendations.append({
                "severity": "warning",
                "message": "Bridge has reconnected multiple times",
                "action": "Monitor bridge stability; may need manual restart soon",
            })
        
        # API issues
        if not api.get("healthy"):
            recommendations.append({
                "severity": "critical",
                "message": "Gemini API is unavailable",
                "action": "Check API key configuration and network connectivity",
            })
        
        # Database issues
        if not db.get("healthy"):
            recommendations.append({
                "severity": "critical",
                "message": "Database is unavailable",
                "action": "Ensure database file is accessible and not locked",
            })
        
        # Queue issues
        queue_data = queue.get("rate_limit", {})
        if queue_data.get("remaining", 0) < 5:
            recommendations.append({
                "severity": "warning",
                "message": "Rate limit threshold approaching",
                "action": "Slow down API requests or wait for rate limit window to reset",
            })
        
        if (queue.get("queue_length") or 0) > 50:
            recommendations.append({
                "severity": "info",
                "message": f"Job queue has {queue.get('queue_length')} pending jobs",
                "action": "Queue is processing normally; no action needed",
            })
        
        return recommendations

class HealthCheckAPI:
    """REST API for health checks"""
    
    @staticmethod
    def register_endpoints(app):
        """Register health check endpoints with Flask/Streamlit app"""
        
        @app.route('/api/health/full', methods=['GET'])
        def health_full():
            return SystemHealth.get_full_status()
        
        @app.route('/api/health/bridge', methods=['GET'])
        def health_bridge():
            return SystemHealth.get_bridge_status()
        
        @app.route('/api/health/api', methods=['GET'])
        def health_api():
            return SystemHealth.get_api_status()
        
        @app.route('/api/health/database', methods=['GET'])
        def health_database():
            return SystemHealth.get_database_status()
        
        @app.route('/api/health/queue', methods=['GET'])
        def health_queue():
            return SystemHealth.get_queue_status()

# Helper function for Streamlit integration
def display_system_health_in_streamlit(st):
    """Display system health in Streamlit sidebar"""
    import streamlit as st
    
    try:
        status = SystemHealth.get_full_status()
        
        with st.sidebar:
            st.divider()
            st.subheader("System Health")
            
            # Overall status
            if status["overall_status"] == "healthy":
                st.success("✓ All Systems Operational")
            elif status["overall_status"] == "degraded":
                st.warning("⚠ Degraded Performance")
            else:
                st.error("✗ System Issues")
            
            # Service status
            with st.expander("Service Details"):
                services = status["services"]
                
                # Bridge
                bridge = services["whatsapp_bridge"]
                if bridge.get("status") == "online":
                    st.success(f"Bridge: Online ({bridge.get('uptime_seconds')}s uptime)")
                else:
                    st.error(f"Bridge: Offline")
                
                # API
                api = services["gemini_api"]
                st.success("API: Online") if api.get("healthy") else st.error("API: Offline")
                
                # Database
                db = services["database"]
                st.success("Database: Online") if db.get("healthy") else st.error("Database: Offline")
                
                # Queue
                queue = services["job_queue"]
                st.info(f"Queue: {queue.get('queue_length')} pending jobs")
            
            # Recommendations
            if status["recommendations"]:
                with st.expander("⚡ Recommendations"):
                    for rec in status["recommendations"]:
                        if rec["severity"] == "critical":
                            st.error(f"**{rec['message']}**\n{rec['action']}")
                        elif rec["severity"] == "warning":
                            st.warning(f"**{rec['message']}**\n{rec['action']}")
                        else:
                            st.info(f"**{rec['message']}**\n{rec['action']}")
    
    except Exception as e:
        st.sidebar.warning(f"Health check failed: {str(e)}")
