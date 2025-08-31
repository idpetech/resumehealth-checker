"""
User Sentiment Tracking System
Captures and analyzes user emotional responses to AI analysis
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class SentimentTracker:
    """Tracks user sentiment and feedback for prompt optimization"""
    
    def __init__(self, data_file: str = "analytics/sentiment_data.json"):
        self.data_file = data_file
        self.ensure_data_file_exists()
    
    def ensure_data_file_exists(self):
        """Create analytics directory and data file if they don't exist"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        
        if not os.path.exists(self.data_file):
            initial_data = {
                "metadata": {
                    "created": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0.0",
                    "description": "User sentiment tracking data"
                },
                "sessions": {},
                "feedback": []
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2)
    
    def track_session_start(self, session_id: str, product: str, user_agent: str = None) -> Dict[str, Any]:
        """Track when a user starts a session"""
        session_data = {
            "session_id": session_id,
            "product": product,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "user_agent": user_agent,
            "prompt_version": None,
            "analysis_completed": False,
            "sentiment_collected": False,
            "conversion_completed": False,
            "journey": []
        }
        
        self._save_session_data(session_id, session_data)
        logger.info(f"Session started: {session_id} for {product}")
        return session_data
    
    def track_analysis_completion(self, session_id: str, prompt_version: str, 
                                analysis_type: str, processing_time: float) -> bool:
        """Track when AI analysis is completed"""
        try:
            data = self._load_data()
            
            if session_id not in data["sessions"]:
                logger.warning(f"Session not found for analysis completion: {session_id}")
                return False
            
            session = data["sessions"][session_id]
            session.update({
                "prompt_version": prompt_version,
                "analysis_type": analysis_type,
                "analysis_completed": True,
                "analysis_completion_time": datetime.now(timezone.utc).isoformat(),
                "processing_time_seconds": processing_time
            })
            
            session["journey"].append({
                "event": "analysis_completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"analysis_type": analysis_type, "processing_time": processing_time}
            })
            
            self._save_data(data)
            logger.info(f"Analysis completed: {session_id} ({analysis_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking analysis completion: {e}")
            return False
    
    def track_sentiment(self, session_id: str, sentiment_score: int, 
                       sentiment_label: str, specific_feedback: str = None) -> bool:
        """Track user sentiment after seeing results"""
        try:
            data = self._load_data()
            
            # Update session data
            if session_id in data["sessions"]:
                session = data["sessions"][session_id]
                session.update({
                    "sentiment_collected": True,
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "sentiment_time": datetime.now(timezone.utc).isoformat()
                })
                
                session["journey"].append({
                    "event": "sentiment_collected",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "data": {
                        "sentiment_score": sentiment_score,
                        "sentiment_label": sentiment_label
                    }
                })
            
            # Add to feedback collection
            feedback_entry = {
                "feedback_id": str(uuid4()),
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "specific_feedback": specific_feedback,
                "product": data["sessions"].get(session_id, {}).get("product", "unknown"),
                "prompt_version": data["sessions"].get(session_id, {}).get("prompt_version", "unknown"),
                "analysis_type": data["sessions"].get(session_id, {}).get("analysis_type", "unknown")
            }
            
            data["feedback"].append(feedback_entry)
            self._save_data(data)
            
            logger.info(f"Sentiment tracked: {session_id} - {sentiment_label} ({sentiment_score}/5)")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking sentiment: {e}")
            return False
    
    def track_conversion(self, session_id: str, conversion_type: str = "payment") -> bool:
        """Track when user converts (makes payment)"""
        try:
            data = self._load_data()
            
            if session_id not in data["sessions"]:
                logger.warning(f"Session not found for conversion: {session_id}")
                return False
            
            session = data["sessions"][session_id]
            session.update({
                "conversion_completed": True,
                "conversion_type": conversion_type,
                "conversion_time": datetime.now(timezone.utc).isoformat()
            })
            
            session["journey"].append({
                "event": "conversion_completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"conversion_type": conversion_type}
            })
            
            self._save_data(data)
            logger.info(f"Conversion tracked: {session_id} ({conversion_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking conversion: {e}")
            return False
    
    def get_sentiment_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get sentiment analytics for the last N days"""
        try:
            data = self._load_data()
            
            # Filter recent feedback
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
            recent_feedback = [
                f for f in data["feedback"]
                if datetime.fromisoformat(f["timestamp"].replace('Z', '+00:00')).timestamp() > cutoff_date
            ]
            
            if not recent_feedback:
                return {"error": "No recent feedback data"}
            
            # Calculate metrics
            total_responses = len(recent_feedback)
            avg_sentiment = sum(f["sentiment_score"] for f in recent_feedback) / total_responses
            
            # Sentiment distribution
            sentiment_distribution = {}
            for feedback in recent_feedback:
                label = feedback["sentiment_label"]
                sentiment_distribution[label] = sentiment_distribution.get(label, 0) + 1
            
            # Product breakdown
            product_sentiment = {}
            for feedback in recent_feedback:
                product = feedback["product"]
                if product not in product_sentiment:
                    product_sentiment[product] = {"total": 0, "scores": []}
                product_sentiment[product]["total"] += 1
                product_sentiment[product]["scores"].append(feedback["sentiment_score"])
            
            # Calculate averages
            for product in product_sentiment:
                scores = product_sentiment[product]["scores"]
                product_sentiment[product]["avg_sentiment"] = sum(scores) / len(scores)
            
            # Prompt version analysis
            prompt_performance = {}
            for feedback in recent_feedback:
                version = feedback["prompt_version"]
                if version not in prompt_performance:
                    prompt_performance[version] = {"responses": 0, "total_score": 0}
                prompt_performance[version]["responses"] += 1
                prompt_performance[version]["total_score"] += feedback["sentiment_score"]
            
            for version in prompt_performance:
                perf = prompt_performance[version]
                perf["avg_sentiment"] = perf["total_score"] / perf["responses"]
            
            return {
                "period_days": days,
                "total_responses": total_responses,
                "average_sentiment": round(avg_sentiment, 2),
                "sentiment_distribution": sentiment_distribution,
                "product_sentiment": product_sentiment,
                "prompt_performance": prompt_performance,
                "positive_rate": len([f for f in recent_feedback if f["sentiment_score"] >= 4]) / total_responses * 100
            }
            
        except Exception as e:
            logger.error(f"Error generating sentiment analytics: {e}")
            return {"error": str(e)}
    
    def get_conversion_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get conversion analytics correlated with sentiment"""
        try:
            data = self._load_data()
            
            # Get recent sessions with sentiment data
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days * 24 * 60 * 60)
            recent_sessions = [
                s for s in data["sessions"].values()
                if datetime.fromisoformat(s["start_time"].replace('Z', '+00:00')).timestamp() > cutoff_date
                and s.get("sentiment_collected", False)
            ]
            
            if not recent_sessions:
                return {"error": "No recent session data with sentiment"}
            
            # Calculate conversion rates by sentiment
            sentiment_conversion = {}
            for session in recent_sessions:
                sentiment = session.get("sentiment_label", "unknown")
                if sentiment not in sentiment_conversion:
                    sentiment_conversion[sentiment] = {"total": 0, "converted": 0}
                
                sentiment_conversion[sentiment]["total"] += 1
                if session.get("conversion_completed", False):
                    sentiment_conversion[sentiment]["converted"] += 1
            
            # Calculate conversion rates
            for sentiment in sentiment_conversion:
                data_point = sentiment_conversion[sentiment]
                data_point["conversion_rate"] = (data_point["converted"] / data_point["total"]) * 100 if data_point["total"] > 0 else 0
            
            total_sessions = len(recent_sessions)
            total_conversions = len([s for s in recent_sessions if s.get("conversion_completed", False)])
            overall_conversion_rate = (total_conversions / total_sessions) * 100 if total_sessions > 0 else 0
            
            return {
                "period_days": days,
                "total_sessions": total_sessions,
                "total_conversions": total_conversions,
                "overall_conversion_rate": round(overall_conversion_rate, 2),
                "sentiment_conversion_breakdown": sentiment_conversion
            }
            
        except Exception as e:
            logger.error(f"Error generating conversion analytics: {e}")
            return {"error": str(e)}
    
    def _save_session_data(self, session_id: str, session_data: Dict[str, Any]):
        """Save session data to file"""
        try:
            data = self._load_data()
            data["sessions"][session_id] = session_data
            self._save_data(data)
        except Exception as e:
            logger.error(f"Error saving session data: {e}")
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from file"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sentiment data: {e}")
            return {"sessions": {}, "feedback": []}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save data to file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving sentiment data: {e}")


# Global instance for use throughout the application
sentiment_tracker = SentimentTracker()

# Convenience functions
def track_session_start(session_id: str, product: str, user_agent: str = None):
    """Global function to start session tracking"""
    return sentiment_tracker.track_session_start(session_id, product, user_agent)

def track_analysis_completion(session_id: str, prompt_version: str, analysis_type: str, processing_time: float):
    """Global function to track analysis completion"""
    return sentiment_tracker.track_analysis_completion(session_id, prompt_version, analysis_type, processing_time)

def track_sentiment(session_id: str, sentiment_score: int, sentiment_label: str, specific_feedback: str = None):
    """Global function to track sentiment"""
    return sentiment_tracker.track_sentiment(session_id, sentiment_score, sentiment_label, specific_feedback)

def track_conversion(session_id: str, conversion_type: str = "payment"):
    """Global function to track conversion"""
    return sentiment_tracker.track_conversion(session_id, conversion_type)

def get_sentiment_analytics(days: int = 7):
    """Global function to get sentiment analytics"""
    return sentiment_tracker.get_sentiment_analytics(days)

def get_conversion_analytics(days: int = 7):
    """Global function to get conversion analytics"""
    return sentiment_tracker.get_conversion_analytics(days)