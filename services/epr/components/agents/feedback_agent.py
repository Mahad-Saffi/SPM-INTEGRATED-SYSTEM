"""
Feedback Agent - Structured feedback management
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.notification_agent import NotificationAgent


class FeedbackAgent:
    """Structured feedback management agent"""
    
    def __init__(self, data_manager: DataManager, notification_agent: Optional[NotificationAgent] = None):
        self.data_manager = data_manager
        self.notification_agent = notification_agent
    
    def create_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured feedback"""
        if not feedback_data.get("employee_id") or not feedback_data.get("given_by"):
            return {"success": False, "error": "Employee ID and given_by are required"}
        
        # Prepare feedback data for API
        api_feedback_data = {
            "employee_id": feedback_data["employee_id"],
            "reviewer_id": feedback_data["given_by"],
            "project_id": feedback_data.get("project_id"),
            "feedback_type": feedback_data.get("type", "general"),
            "rating": feedback_data.get("rating", 3.0),
            "feedback_text": feedback_data.get("content", feedback_data.get("title", "")),
            "is_anonymous": feedback_data.get("is_anonymous", False)
        }
        
        # Use HybridDataManager's create_feedback method (uses API if available)
        if hasattr(self.data_manager, 'create_feedback'):
            feedback = self.data_manager.create_feedback(api_feedback_data)
            # Add compatibility fields
            if "given_by" not in feedback:
                feedback["given_by"] = feedback.get("reviewer_id", feedback_data["given_by"])
            if "title" not in feedback:
                feedback["title"] = feedback_data.get("title", "")
            if "category" not in feedback:
                feedback["category"] = feedback_data.get("category", "performance")
        else:
            # Fallback to old method
            feedbacks = self.data_manager.load_data("feedback") or []
            feedback = {
                "id": str(len(feedbacks) + 1),
                "employee_id": feedback_data["employee_id"],
                "given_by": feedback_data["given_by"],
                "type": feedback_data.get("type", "general"),
                "category": feedback_data.get("category", "performance"),
                "title": feedback_data.get("title", ""),
                "content": feedback_data.get("content", ""),
                "strengths": feedback_data.get("strengths", []),
                "areas_for_improvement": feedback_data.get("areas_for_improvement", []),
                "action_items": feedback_data.get("action_items", []),
                "status": "pending_response",
                "employee_response": None,
                "communications": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            feedbacks.append(feedback)
            self.data_manager.save_data("feedback", feedbacks)
        
        # Notify employee
        if self.notification_agent:
            self.notification_agent.send_notification(
                recipient=feedback_data["employee_id"],
                title="New Feedback Received",
                message=f"You have received new feedback: {feedback.get('title', 'Feedback')}",
                notification_type="feedback"
            )
        
        return {"success": True, "feedback": feedback}
    
    def respond_to_feedback(self, feedback_id: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Employee response to feedback"""
        feedbacks = self.data_manager.load_data("feedback") or []
        
        for feedback in feedbacks:
            if feedback.get("id") == feedback_id:
                feedback["employee_response"] = {
                    "response": response_data.get("response", ""),
                    "acknowledged": response_data.get("acknowledged", False),
                    "action_plan": response_data.get("action_plan", ""),
                    "responded_at": datetime.now().isoformat()
                }
                feedback["status"] = "responded"
                feedback["updated_at"] = datetime.now().isoformat()
                
                self.data_manager.save_data("feedback", feedbacks)
                
                # Notify feedback giver
                if self.notification_agent:
                    self.notification_agent.send_notification(
                        recipient=feedback.get("given_by"),
                        title="Feedback Response Received",
                        message=f"Employee has responded to your feedback: {feedback.get('title', 'Feedback')}",
                        notification_type="feedback_response"
                    )
                
                return {"success": True, "feedback": feedback}
        
        return {"success": False, "error": "Feedback not found"}
    
    def get_feedbacks_for_employee(self, employee_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get feedbacks for an employee"""
        feedbacks = self.data_manager.load_data("feedback") or []
        # Convert employee_id to string for comparison (handle both string and int IDs)
        employee_id_str = str(employee_id)
        emp_feedbacks = [f for f in feedbacks if str(f.get("employee_id", "")) == employee_id_str]
        
        if status:
            emp_feedbacks = [f for f in emp_feedbacks if f.get("status") == status]
        
        # Sort by created_at descending
        emp_feedbacks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return emp_feedbacks
    
    def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific feedback"""
        feedbacks = self.data_manager.load_data("feedback") or []
        for feedback in feedbacks:
            if feedback.get("id") == feedback_id:
                return feedback
        return None
    
    def update_feedback_status(self, feedback_id: str, status: str) -> bool:
        """Update feedback status"""
        feedbacks = self.data_manager.load_data("feedback") or []
        
        for feedback in feedbacks:
            if feedback.get("id") == feedback_id:
                feedback["status"] = status
                feedback["updated_at"] = datetime.now().isoformat()
                self.data_manager.save_data("feedback", feedbacks)
                return True
        
        return False
    
    def get_all_feedbacks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all feedbacks with optional filters"""
        feedbacks = self.data_manager.load_data("feedback") or []
        
        if not filters:
            return feedbacks
        
        filtered_feedbacks = feedbacks
        if filters.get("status"):
            filtered_feedbacks = [f for f in filtered_feedbacks if f.get("status") == filters["status"]]
        if filters.get("employee_id"):
            filtered_feedbacks = [f for f in filtered_feedbacks if f.get("employee_id") == filters["employee_id"]]
        if filters.get("given_by"):
            filtered_feedbacks = [f for f in filtered_feedbacks if f.get("given_by") == filters["given_by"]]
        if filters.get("category"):
            filtered_feedbacks = [f for f in filtered_feedbacks if f.get("category") == filters["category"]]
        
        return filtered_feedbacks
    
    def add_communication(self, feedback_id: str, sender_id: str, message: str, sender_role: str = "employee") -> Dict[str, Any]:
        """Add a communication message to feedback thread"""
        feedbacks = self.data_manager.load_data("feedback") or []
        
        for feedback in feedbacks:
            if feedback.get("id") == feedback_id:
                if "communications" not in feedback:
                    feedback["communications"] = []
                
                communication = {
                    "id": str(len(feedback["communications"]) + 1),
                    "sender_id": sender_id,
                    "sender_role": sender_role,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                feedback["communications"].append(communication)
                feedback["updated_at"] = datetime.now().isoformat()
                self.data_manager.save_data("feedback", feedbacks)
                
                # Notify the other party
                if self.notification_agent:
                    if sender_role == "employee":
                        # Employee sent message, notify manager
                        self.notification_agent.send_notification(
                            recipient=feedback.get("given_by"),
                            title="New Message on Feedback",
                            message=f"Employee has a question about feedback: {feedback.get('title', 'Feedback')}",
                            notification_type="feedback_communication"
                        )
                    else:
                        # Manager sent message, notify employee
                        self.notification_agent.send_notification(
                            recipient=feedback.get("employee_id"),
                            title="Manager Responded to Your Question",
                            message=f"Manager has responded to your question about: {feedback.get('title', 'Feedback')}",
                            notification_type="feedback_communication"
                        )
                
                return {"success": True, "communication": communication, "feedback": feedback}
        
        return {"success": False, "error": "Feedback not found"}
    
    def get_communications(self, feedback_id: str) -> List[Dict[str, Any]]:
        """Get all communications for a feedback"""
        feedback = self.get_feedback(feedback_id)
        if feedback:
            return feedback.get("communications", [])
        return []

