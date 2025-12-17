"""
Notification Agent - Multi-channel notification system
"""
import os
import smtplib
from datetime import datetime
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from components.managers.data_manager import DataManager


class NotificationAgent:
    """Multi-channel notification agent"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def send_notification(self, recipient: str, title: str, message: str,
                         notification_type: str = "info", priority: str = "normal") -> Dict[str, Any]:
        """Send notification"""
        notification = {
            "id": self._generate_notification_id(),
            "recipient": recipient,
            "title": title,
            "message": message,
            "type": notification_type,
            "priority": priority,
            "status": "sent",
            "created_at": datetime.now().isoformat(),
            "read": False
        }
        
        # Save notification
        notifications = self.data_manager.load_data("notifications") or []
        notifications.append(notification)
        self.data_manager.save_data("notifications", notifications)
        
        # Try to send email if configured
        if notification_type in ["task_assignment", "deadline_reminder", "feedback"]:
            self.send_email(recipient, title, message)
        
        return {"success": True, "notification": notification}
    
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send email notification (SMTP-ready)"""
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not all([smtp_host, smtp_user, smtp_password]):
            print("SMTP not configured, skipping email send")
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            server = smtplib.SMTP(smtp_host, int(smtp_port))
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_task_reminder(self, task: Dict[str, Any]) -> bool:
        """Send task deadline reminder"""
        if not task.get("assigned_to") or not task.get("due_date"):
            return False
        
        try:
            due_date = datetime.fromisoformat(task["due_date"])
            days_remaining = (due_date - datetime.now()).days
            
            if days_remaining <= 1:
                self.send_notification(
                    recipient=task["assigned_to"],
                    title="Task Deadline Reminder",
                    message=f"Task '{task.get('title')}' is due {'today' if days_remaining == 0 else 'tomorrow'}",
                    notification_type="deadline_reminder",
                    priority="high"
                )
                return True
        except:
            pass
        
        return False
    
    def get_notifications(self, recipient: Optional[str] = None, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications"""
        notifications = self.data_manager.load_data("notifications") or []
        
        if recipient:
            notifications = [n for n in notifications if n.get("recipient") == recipient]
        
        if unread_only:
            notifications = [n for n in notifications if not n.get("read", False)]
        
        # Sort by created_at descending
        notifications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return notifications
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        notifications = self.data_manager.load_data("notifications") or []
        
        for notification in notifications:
            if notification.get("id") == notification_id:
                notification["read"] = True
                notification["read_at"] = datetime.now().isoformat()
                self.data_manager.save_data("notifications", notifications)
                return True
        
        return False
    
    def get_managers_and_owners(self) -> List[str]:
        """Get all manager and owner employee IDs"""
        employees = self.data_manager.load_data("employees") or []
        users = self.data_manager.load_data("users") or []
        
        manager_emails = [u.get("email") for u in users if u.get("role") in ["manager", "owner"]]
        manager_ids = [e.get("id") for e in employees if e.get("email") in manager_emails]
        
        return manager_ids
    
    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        notifications = self.data_manager.load_data("notifications") or []
        return str(len(notifications) + 1)

