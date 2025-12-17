"""
Filtering Agent - Advanced filtering and sorting
"""
from datetime import datetime
from typing import Dict, Any, Optional, List


class FilteringAgent:
    """Advanced filtering and sorting agent"""
    
    def filter_reports(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to reports"""
        filtered_data = data
        
        # Status filter
        if filters.get("status"):
            filtered_data = [d for d in filtered_data if d.get("status") == filters["status"]]
        
        # Date range filter
        if filters.get("start_date") or filters.get("end_date"):
            filtered_data = self._filter_by_date_range(filtered_data, filters.get("start_date"), filters.get("end_date"))
        
        # Department filter
        if filters.get("department"):
            filtered_data = [d for d in filtered_data if d.get("department") == filters["department"]]
        
        # Employee filter
        if filters.get("employee_id"):
            filtered_data = [d for d in filtered_data if d.get("employee_id") == filters["employee_id"]]
        
        # Project filter
        if filters.get("project_id"):
            filtered_data = [d for d in filtered_data if d.get("project_id") == filters["project_id"]]
        
        # Priority filter
        if filters.get("priority"):
            filtered_data = [d for d in filtered_data if d.get("priority") == filters["priority"]]
        
        # Performance score range
        if filters.get("min_score") is not None:
            filtered_data = [d for d in filtered_data if d.get("performance_score", 0) >= filters["min_score"]]
        if filters.get("max_score") is not None:
            filtered_data = [d for d in filtered_data if d.get("performance_score", 100) <= filters["max_score"]]
        
        return filtered_data
    
    def sort_reports(self, data: List[Dict[str, Any]], sort_by: str, order: str = "asc") -> List[Dict[str, Any]]:
        """Sort reports by various criteria"""
        reverse = order.lower() == "desc"
        
        # Handle different sort fields
        if sort_by == "date" or sort_by == "created_at":
            sorted_data = sorted(data, key=lambda x: x.get("created_at", ""), reverse=reverse)
        elif sort_by == "performance_score" or sort_by == "score":
            sorted_data = sorted(data, key=lambda x: x.get("performance_score", 0), reverse=reverse)
        elif sort_by == "name":
            sorted_data = sorted(data, key=lambda x: x.get("name", ""), reverse=reverse)
        elif sort_by == "status":
            sorted_data = sorted(data, key=lambda x: x.get("status", ""), reverse=reverse)
        elif sort_by == "priority":
            priority_order = {"high": 3, "medium": 2, "low": 1}
            sorted_data = sorted(data, key=lambda x: priority_order.get(x.get("priority", "low"), 0), reverse=reverse)
        elif sort_by == "completion_rate":
            sorted_data = sorted(data, key=lambda x: x.get("completion_rate", 0), reverse=reverse)
        else:
            # Default sort by ID
            sorted_data = sorted(data, key=lambda x: x.get("id", ""), reverse=reverse)
        
        return sorted_data
    
    def _filter_by_date_range(self, data: List[Dict[str, Any]], start_date: Optional[str], end_date: Optional[str]) -> List[Dict[str, Any]]:
        """Filter data by date range"""
        filtered = data
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
                filtered = [d for d in filtered if self._get_date_from_record(d) >= start]
            except:
                pass
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
                filtered = [d for d in filtered if self._get_date_from_record(d) <= end]
            except:
                pass
        
        return filtered
    
    def _get_date_from_record(self, record: Dict[str, Any]) -> datetime:
        """Extract date from record"""
        # Try different date fields
        for field in ["created_at", "updated_at", "due_date", "deadline", "evaluated_at"]:
            if record.get(field):
                try:
                    return datetime.fromisoformat(record[field])
                except:
                    pass
        
        # Default to current date if no date found
        return datetime.now()

