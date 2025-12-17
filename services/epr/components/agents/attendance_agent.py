"""
Attendance Agent - Tracks employee attendance and check-in/out times
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class AttendanceAgent:
    """Manages employee attendance tracking"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def mark_attendance(self, employee_id: str, status: str, check_in_time: Optional[str] = None, 
                       check_out_time: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark attendance for an employee
        
        Args:
            employee_id: Employee ID
            status: "present" or "absent"
            check_in_time: Check-in time (ISO format)
            check_out_time: Check-out time (ISO format)
            notes: Optional notes
        """
        if status not in ["present", "absent"]:
            return {"success": False, "error": "Status must be 'present' or 'absent'"}
        
        attendance_data = self.data_manager.load_data("attendance") or []
        
        # Get today's date
        today = date.today().isoformat()
        
        # Check if attendance already marked for today
        existing = next((a for a in attendance_data 
                        if a.get("employee_id") == employee_id and a.get("date") == today), None)
        
        if existing:
            # Update existing record
            existing["status"] = status
            if check_in_time:
                existing["check_in_time"] = check_in_time
            if check_out_time:
                existing["check_out_time"] = check_out_time
            if notes:
                existing["notes"] = notes
            existing["updated_at"] = datetime.now().isoformat()
        else:
            # Create new record
            attendance_record = {
                "id": str(len(attendance_data) + 1),
                "employee_id": employee_id,
                "date": today,
                "status": status,
                "check_in_time": check_in_time or datetime.now().isoformat() if status == "present" else None,
                "check_out_time": check_out_time,
                "notes": notes,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            attendance_data.append(attendance_record)
        
        self.data_manager.save_data("attendance", attendance_data)
        return {"success": True}
    
    def get_employee_attendance(self, employee_id: str, start_date: Optional[str] = None, 
                               end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get attendance records for an employee"""
        attendance_data = self.data_manager.load_data("attendance") or []
        
        employee_records = [a for a in attendance_data if a.get("employee_id") == employee_id]
        
        if start_date:
            employee_records = [a for a in employee_records if a.get("date") >= start_date]
        if end_date:
            employee_records = [a for a in employee_records if a.get("date") <= end_date]
        
        return sorted(employee_records, key=lambda x: x.get("date", ""), reverse=True)
    
    def calculate_attendance_percentage(self, employee_id: str, days: int = 30) -> float:
        """Calculate attendance percentage for last N days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        attendance_records = self.get_employee_attendance(
            employee_id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
        
        if not attendance_records:
            return 0.0
        
        present_count = len([a for a in attendance_records if a.get("status") == "present"])
        total_days = len(attendance_records)
        
        return (present_count / total_days * 100) if total_days > 0 else 0.0
    
    def get_today_attendance(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get today's attendance record for an employee"""
        today = date.today().isoformat()
        attendance_data = self.data_manager.load_data("attendance") or []
        
        return next((a for a in attendance_data 
                    if a.get("employee_id") == employee_id and a.get("date") == today), None)

