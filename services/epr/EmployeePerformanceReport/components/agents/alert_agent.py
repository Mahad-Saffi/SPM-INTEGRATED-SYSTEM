"""
Alert Agent - Proactive performance alerts and monitoring
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
from components.agents.notification_agent import NotificationAgent


class AlertAgent:
    """Proactive performance alert and monitoring agent"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent,
                 notification_agent: Optional[NotificationAgent] = None):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
        self.notification_agent = notification_agent
        self.default_thresholds = {
            "performance_score": 60.0,
            "completion_rate": 70.0,
            "on_time_rate": 80.0,
            "missed_deadlines": 2,
            "low_productivity_days": 3
        }
    
    def detect_all_alerts(self, manager_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect all performance alerts"""
        alerts = []
        employees = self.data_manager.load_data("employees") or []
        tasks = self.data_manager.load_data("tasks") or []
        
        # Get alert configurations
        alert_configs = self._get_alert_configurations(manager_id)
        
        for employee in employees:
            employee_id = employee.get("id")
            if not employee_id:
                continue
            
            # Check performance alerts
            perf_alerts = self._check_performance_alerts(employee_id, alert_configs)
            alerts.extend(perf_alerts)
            
            # Check deadline alerts
            deadline_alerts = self._check_deadline_alerts(employee_id, tasks, alert_configs)
            alerts.extend(deadline_alerts)
            
            # Check productivity alerts
            productivity_alerts = self._check_productivity_alerts(employee_id, tasks, alert_configs)
            alerts.extend(productivity_alerts)
        
        # Sort by severity and timestamp
        alerts.sort(key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 2),
            x.get("created_at", "")
        ), reverse=True)
        
        return alerts
    
    def _check_performance_alerts(self, employee_id: str, configs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for performance-related alerts"""
        alerts = []
        # Don't save, just read existing performance data
        evaluation = self.performance_agent.evaluate_employee(employee_id, save=False)
        
        thresholds = configs.get("thresholds", self.default_thresholds)
        
        # Low performance score
        perf_score = evaluation.get("performance_score", 0)
        if perf_score < thresholds.get("performance_score", 60.0):
            alerts.append({
                "id": self._generate_alert_id(),
                "employee_id": employee_id,
                "type": "low_performance",
                "title": "Low Performance Score",
                "description": f"Employee performance score ({perf_score:.1f}) is below threshold ({thresholds.get('performance_score', 60.0)})",
                "severity": "high" if perf_score < 40 else "medium",
                "metric": "performance_score",
                "current_value": perf_score,
                "threshold": thresholds.get("performance_score", 60.0),
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "acknowledged": False
            })
        
        # Low completion rate
        completion_rate = evaluation.get("completion_rate", 0)
        if completion_rate < thresholds.get("completion_rate", 70.0):
            alerts.append({
                "id": self._generate_alert_id(),
                "employee_id": employee_id,
                "type": "low_completion_rate",
                "title": "Low Task Completion Rate",
                "description": f"Task completion rate ({completion_rate:.1f}%) is below threshold ({thresholds.get('completion_rate', 70.0)}%)",
                "severity": "high" if completion_rate < 50 else "medium",
                "metric": "completion_rate",
                "current_value": completion_rate,
                "threshold": thresholds.get("completion_rate", 70.0),
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "acknowledged": False
            })
        
        # Low on-time rate
        on_time_rate = evaluation.get("on_time_rate", 0)
        if on_time_rate < thresholds.get("on_time_rate", 80.0):
            alerts.append({
                "id": self._generate_alert_id(),
                "employee_id": employee_id,
                "type": "low_on_time_rate",
                "title": "Low On-Time Completion Rate",
                "description": f"On-time completion rate ({on_time_rate:.1f}%) is below threshold ({thresholds.get('on_time_rate', 80.0)}%)",
                "severity": "medium",
                "metric": "on_time_rate",
                "current_value": on_time_rate,
                "threshold": thresholds.get("on_time_rate", 80.0),
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "acknowledged": False
            })
        
        return alerts
    
    def _check_deadline_alerts(self, employee_id: str, tasks: List[Dict[str, Any]], 
                               configs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for missed deadline alerts"""
        alerts = []
        employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
        
        thresholds = configs.get("thresholds", self.default_thresholds)
        max_missed = thresholds.get("missed_deadlines", 2)
        
        # Count missed deadlines
        missed_count = 0
        overdue_tasks = []
        now = datetime.now()
        
        for task in employee_tasks:
            if task.get("status") != "completed" and task.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    if due_date < now:
                        missed_count += 1
                        overdue_tasks.append(task)
                except:
                    pass
        
        if missed_count >= max_missed:
            alerts.append({
                "id": self._generate_alert_id(),
                "employee_id": employee_id,
                "type": "missed_deadlines",
                "title": "Multiple Missed Deadlines",
                "description": f"Employee has {missed_count} overdue task(s). Threshold: {max_missed}",
                "severity": "high" if missed_count >= max_missed * 2 else "medium",
                "metric": "missed_deadlines",
                "current_value": missed_count,
                "threshold": max_missed,
                "overdue_tasks": [t.get("id") for t in overdue_tasks[:5]],  # Limit to 5
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "acknowledged": False
            })
        
        return alerts
    
    def _check_productivity_alerts(self, employee_id: str, tasks: List[Dict[str, Any]],
                                   configs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for low productivity and high workload alerts"""
        alerts = []
        employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
        
        thresholds = configs.get("thresholds", self.default_thresholds)
        low_prod_days = thresholds.get("low_productivity_days", 3)
        
        # Check for high workload (more than 10 active tasks)
        active_tasks = [t for t in employee_tasks if t.get("status") in ["pending", "in_progress"]]
        if len(active_tasks) > 10:
            alerts.append({
                "id": self._generate_alert_id(),
                "employee_id": employee_id,
                "type": "high_workload",
                "title": "High Workload Detected",
                "description": f"Employee has {len(active_tasks)} active tasks assigned. This may indicate overwork.",
                "severity": "high" if len(active_tasks) > 15 else "medium",
                "metric": "workload",
                "current_value": len(active_tasks),
                "threshold": 10,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "acknowledged": False
            })
        
        # Check tasks completed in last N days
        now = datetime.now()
        days_ago = now - timedelta(days=low_prod_days)
        
        recent_completed = 0
        for task in employee_tasks:
            if task.get("status") == "completed" and task.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(task["completed_at"])
                    if completed_at >= days_ago:
                        recent_completed += 1
                except:
                    pass
        
        # If very few tasks completed recently, alert
        if recent_completed < 2:  # Less than 2 tasks in last N days
            alerts.append({
                "id": self._generate_alert_id(),
                "employee_id": employee_id,
                "type": "low_productivity",
                "title": "Low Productivity Detected",
                "description": f"Only {recent_completed} task(s) completed in the last {low_prod_days} days",
                "severity": "medium",
                "metric": "productivity",
                "current_value": recent_completed,
                "threshold": 2,
                "period_days": low_prod_days,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "acknowledged": False
            })
        
        return alerts
    
    def create_alert_configuration(self, manager_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update alert configuration"""
        configs = self.data_manager.load_data("alert_configurations") or []
        
        # Remove existing config for this manager
        configs = [c for c in configs if c.get("manager_id") != manager_id]
        
        config = {
            "manager_id": manager_id,
            "thresholds": config_data.get("thresholds", self.default_thresholds),
            "alert_types": config_data.get("alert_types", ["low_performance", "missed_deadlines", "low_productivity"]),
            "enabled": config_data.get("enabled", True),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        configs.append(config)
        self.data_manager.save_data("alert_configurations", configs)
        
        return {"success": True, "config": config}
    
    def _get_alert_configurations(self, manager_id: Optional[str] = None) -> Dict[str, Any]:
        """Get alert configurations"""
        configs = self.data_manager.load_data("alert_configurations") or []
        
        if manager_id:
            config = next((c for c in configs if c.get("manager_id") == manager_id), None)
            if config:
                return config
        
        # Return default configuration
        return {
            "thresholds": self.default_thresholds,
            "alert_types": ["low_performance", "missed_deadlines", "low_productivity"],
            "enabled": True
        }
    
    def acknowledge_alert(self, alert_id: str, manager_id: str) -> Dict[str, Any]:
        """Acknowledge an alert"""
        alerts = self.data_manager.load_data("alerts") or []
        
        for alert in alerts:
            if alert.get("id") == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = manager_id
                alert["acknowledged_at"] = datetime.now().isoformat()
                alert["status"] = "acknowledged"
                self.data_manager.save_data("alerts", alerts)
                
                return {"success": True, "alert": alert}
        
        return {"success": False, "error": "Alert not found"}
    
    def resolve_alert(self, alert_id: str, manager_id: str, resolution_notes: Optional[str] = None) -> Dict[str, Any]:
        """Resolve an alert"""
        alerts = self.data_manager.load_data("alerts") or []
        
        for alert in alerts:
            if alert.get("id") == alert_id:
                alert["status"] = "resolved"
                alert["resolved_by"] = manager_id
                alert["resolved_at"] = datetime.now().isoformat()
                if resolution_notes:
                    alert["resolution_notes"] = resolution_notes
                self.data_manager.save_data("alerts", alerts)
                
                return {"success": True, "alert": alert}
        
        return {"success": False, "error": "Alert not found"}
    
    def save_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """Save alerts to storage"""
        existing_alerts = self.data_manager.load_data("alerts") or []
        existing_ids = {a.get("id") for a in existing_alerts}
        
        # Add new alerts and update existing ones
        for alert in alerts:
            if alert.get("id") in existing_ids:
                # Update existing alert
                for i, existing in enumerate(existing_alerts):
                    if existing.get("id") == alert.get("id"):
                        existing_alerts[i] = alert
                        break
            else:
                # Add new alert
                existing_alerts.append(alert)
                # Send notifications to managers/owners when alerts are created
                if self.notification_agent:
                    employee = next(
                        (e for e in (self.data_manager.load_data("employees") or []) 
                         if e.get("id") == alert.get("employee_id")),
                        None
                    )
                    employee_name = employee.get("name", "Employee") if employee else "Employee"
                    
                    # Send notification to employee if high severity
                    if alert.get("severity") == "high" and employee:
                        self.notification_agent.send_notification(
                            recipient=alert.get("employee_id"),
                            title=f"Performance Alert: {alert.get('title')}",
                            message=alert.get("description", ""),
                            notification_type="performance_alert",
                            priority="high"
                        )
                    
                    # Always send notification to all managers/owners
                    managers = self.notification_agent.get_managers_and_owners()
                    alert_type = alert.get("type", "")
                    
                    # Determine notification type based on alert type
                    if alert_type == "low_performance" or alert_type == "low_completion_rate" or alert_type == "low_on_time_rate":
                        notification_title = f"Low Performance Alert: {employee_name}"
                        notification_type = "low_performance"
                    elif alert_type == "missed_deadlines":
                        notification_title = f"Missed Deadlines Alert: {employee_name}"
                        notification_type = "missed_deadlines"
                    elif alert_type == "high_workload":
                        notification_title = f"High Workload Alert: {employee_name}"
                        notification_type = "high_workload"
                    else:
                        notification_title = f"Performance Alert: {employee_name}"
                        notification_type = "performance_alert"
                    
                    for manager_id in managers:
                        self.notification_agent.send_notification(
                            recipient=manager_id,
                            title=notification_title,
                            message=f"{employee_name}: {alert.get('description', '')}",
                            notification_type=notification_type,
                            priority="high" if alert.get("severity") == "high" else "normal"
                        )
        
        self.data_manager.save_data("alerts", existing_alerts)
        return True
    
    def get_active_alerts(self, manager_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        alerts = self.data_manager.load_data("alerts") or []
        
        # Filter active alerts
        active = [a for a in alerts if a.get("status") == "active"]
        
        # If manager_id provided, filter by manager's employees (if applicable)
        if manager_id:
            # For now, return all active alerts
            # In a real system, you'd filter by manager's team
            pass
        
        return active
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        alerts = self.data_manager.load_data("alerts") or []
        return f"alert_{len(alerts) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

