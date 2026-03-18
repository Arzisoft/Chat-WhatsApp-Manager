"""
Analytics module for ChatChaos.
Provides insights into chat performance, operator metrics, and sales pipeline.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from core.database import get_connection

class ChatAnalytics:
    """Analytics for chat data"""
    
    @staticmethod
    def get_chat_stats() -> Dict[str, Any]:
        """Get overall chat statistics"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Total chats
            cursor.execute("SELECT COUNT(*) as count FROM chats")
            total_chats = cursor.fetchone()['count']
            
            # Active chats (modified in last 7 days)
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE datetime(date_last_msg) > datetime('now', '-7 days')
            """)
            active_chats = cursor.fetchone()['count']
            
            # Total messages
            cursor.execute("SELECT COUNT(*) as count FROM messages")
            total_messages = cursor.fetchone()['count']
            
            # Average messages per chat
            avg_messages = total_messages / total_chats if total_chats > 0 else 0
            
            # Chats by status
            cursor.execute("""
                SELECT status, COUNT(*) as count FROM chats
                GROUP BY status
            """)
            status_breakdown = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return {
                "total_chats": total_chats,
                "active_chats": active_chats,
                "total_messages": total_messages,
                "avg_messages_per_chat": round(avg_messages, 2),
                "status_breakdown": status_breakdown,
            }
    
    @staticmethod
    def get_kpi_metrics() -> Dict[str, Any]:
        """Get KPI metrics"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Hot leads (high urgency)
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE urgency_level = 'high' OR urgency_level = 'critical'
            """)
            hot_leads = cursor.fetchone()['count']
            
            # Pending follow-ups
            cursor.execute("""
                SELECT COUNT(*) as count FROM action_items
                WHERE completed = 0 AND action_type = 'followup'
            """)
            pending_followups = cursor.fetchone()['count']
            
            # Risk flags
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE overdue_payment = 1 OR days_silent > 7
            """)
            risk_flags = cursor.fetchone()['count']
            
            # Revenue pipeline (m³ of concrete)
            cursor.execute("""
                SELECT SUM(total_m3_estimate) as total FROM chats
                WHERE total_m3_estimate IS NOT NULL
            """)
            result = cursor.fetchone()
            revenue_pipeline = result['total'] or 0
            
            return {
                "hot_leads": hot_leads,
                "pending_followups": pending_followups,
                "risk_flags": risk_flags,
                "revenue_pipeline_m3": round(revenue_pipeline, 2),
            }
    
    @staticmethod
    def get_pipeline_breakdown() -> Dict[str, Any]:
        """Get pipeline breakdown by mix grade and area"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # By mix grade
            cursor.execute("""
                SELECT mix_grade, COUNT(*) as count, SUM(total_m3_estimate) as m3
                FROM chats
                WHERE mix_grade IS NOT NULL
                GROUP BY mix_grade
                ORDER BY m3 DESC
            """)
            by_mix = {
                row['mix_grade']: {
                    'count': row['count'],
                    'm3': row['m3'] or 0
                }
                for row in cursor.fetchall()
            }
            
            # By area
            cursor.execute("""
                SELECT primary_area, COUNT(*) as count, SUM(total_m3_estimate) as m3
                FROM chats
                WHERE primary_area IS NOT NULL
                GROUP BY primary_area
                ORDER BY m3 DESC
                LIMIT 10
            """)
            by_area = {
                row['primary_area']: {
                    'count': row['count'],
                    'm3': row['m3'] or 0
                }
                for row in cursor.fetchall()
            }
            
            return {
                "by_mix_grade": by_mix,
                "by_area": by_area,
            }
    
    @staticmethod
    def get_trend_analysis(days: int = 30) -> Dict[str, Any]:
        """Analyze trends over time"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Chats added per day
            cursor.execute(f"""
                SELECT 
                    DATE(imported_at) as date,
                    COUNT(*) as count
                FROM chats
                WHERE datetime(imported_at) > datetime('now', '-{days} days')
                GROUP BY DATE(imported_at)
                ORDER BY date
            """)
            
            daily_counts = defaultdict(int)
            for row in cursor.fetchall():
                daily_counts[row['date']] = row['count']
            
            # Calculate trend
            dates = sorted(daily_counts.keys())
            if len(dates) >= 2:
                first_half_avg = sum(
                    daily_counts[d] for d in dates[:len(dates)//2]
                ) / max(1, len(dates)//2)
                second_half_avg = sum(
                    daily_counts[d] for d in dates[len(dates)//2:]
                ) / max(1, len(dates) - len(dates)//2)
                trend_direction = "up" if second_half_avg > first_half_avg else "down"
                trend_percent = (
                    ((second_half_avg - first_half_avg) / first_half_avg * 100)
                    if first_half_avg > 0 else 0
                )
            else:
                trend_direction = "flat"
                trend_percent = 0
            
            return {
                "daily_counts": dict(daily_counts),
                "trend_direction": trend_direction,
                "trend_percent": round(trend_percent, 2),
                "period_days": days,
            }
    
    @staticmethod
    def get_sentiment_summary() -> Dict[str, int]:
        """Get sentiment distribution"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sentiment, COUNT(*) as count FROM chats
                WHERE sentiment IS NOT NULL
                GROUP BY sentiment
            """)
            
            return {
                row['sentiment']: row['count']
                for row in cursor.fetchall()
            }
    
    @staticmethod
    def get_risk_analysis() -> Dict[str, Any]:
        """Analyze risk indicators"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Overdue payments
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE overdue_payment = 1
            """)
            overdue = cursor.fetchone()['count']
            
            # Silent leads (no activity > 7 days)
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE days_silent > 7
            """)
            silent = cursor.fetchone()['count']
            
            # Stalled negotiations
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE relationship_stage = 'negotiating' 
                AND days_silent > 5
            """)
            stalled = cursor.fetchone()['count']
            
            # At-risk deals
            cursor.execute("""
                SELECT COUNT(*) as count FROM chats
                WHERE relationship_stage IN ('warm', 'negotiating')
                AND (overdue_payment = 1 OR days_silent > 7)
            """)
            at_risk = cursor.fetchone()['count']
            
            return {
                "overdue_payments": overdue,
                "silent_leads": silent,
                "stalled_negotiations": stalled,
                "at_risk_deals": at_risk,
            }
    
    @staticmethod
    def get_action_items_summary() -> Dict[str, Any]:
        """Summarize pending action items"""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # By priority
            cursor.execute("""
                SELECT priority, COUNT(*) as count FROM action_items
                WHERE completed = 0
                GROUP BY priority
            """)
            by_priority = {
                row['priority']: row['count']
                for row in cursor.fetchall()
            }
            
            # Overdue actions
            cursor.execute("""
                SELECT COUNT(*) as count FROM action_items
                WHERE completed = 0 
                AND due_date IS NOT NULL
                AND DATE(due_date) < DATE('now')
            """)
            overdue_actions = cursor.fetchone()['count']
            
            return {
                "by_priority": by_priority,
                "overdue_actions": overdue_actions,
                "total_pending": sum(by_priority.values()),
            }

class OperatorMetrics:
    """Metrics for individual operators"""
    
    @staticmethod
    def get_operator_performance(operator_id: str, days: int = 30) -> Dict[str, Any]:
        """Get operator performance metrics"""
        # This is a placeholder - would need operator_id in database schema
        return {
            "operator_id": operator_id,
            "chats_handled": 0,
            "avg_resolution_time": 0,
            "customer_satisfaction": 0,
            "followups_completed": 0,
        }

class ExportAnalytics:
    """Export analytics data"""
    
    @staticmethod
    def get_full_report() -> Dict[str, Any]:
        """Get complete analytics report"""
        return {
            "generated_at": datetime.now().isoformat(),
            "chat_stats": ChatAnalytics.get_chat_stats(),
            "kpi_metrics": ChatAnalytics.get_kpi_metrics(),
            "pipeline": ChatAnalytics.get_pipeline_breakdown(),
            "trends": ChatAnalytics.get_trend_analysis(),
            "sentiment": ChatAnalytics.get_sentiment_summary(),
            "risks": ChatAnalytics.get_risk_analysis(),
            "actions": ChatAnalytics.get_action_items_summary(),
        }
