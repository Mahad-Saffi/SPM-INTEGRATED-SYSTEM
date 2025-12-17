"""
Enhanced Performance Agent - Multi-metric performance evaluation
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class EnhancedPerformanceAgent:
    """Comprehensive performance evaluation agent"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def evaluate_employee(self, employee_id: str, save: bool = True) -> Dict[str, Any]:
        """Comprehensive performance evaluation
        
        Args:
            employee_id: Employee ID to evaluate
            save: Whether to save the evaluation (default True). Set to False to prevent recursive saves.
        """
        tasks = self.data_manager.load_data("tasks") or []
        projects = self.data_manager.load_data("projects") or []
        employees = self.data_manager.load_data("employees") or []
        
        # Get employee tasks
        employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
        
        # Calculate metrics
        total_tasks = len(employee_tasks)
        completed_tasks = len([t for t in employee_tasks if t.get("status") == "completed"])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate on-time completion
        on_time_tasks = 0
        for task in employee_tasks:
            if task.get("status") == "completed" and task.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    completed_at = datetime.fromisoformat(task.get("completed_at", datetime.now().isoformat()))
                    if completed_at <= due_date:
                        on_time_tasks += 1
                except:
                    pass
        
        on_time_rate = (on_time_tasks / completed_tasks * 100) if completed_tasks > 0 else 0
        
        # Calculate average task completion time
        avg_completion_time = self._calculate_avg_completion_time(employee_tasks)
        
        # Calculate priority handling
        high_priority_completed = len([t for t in employee_tasks 
                                      if t.get("priority") == "high" and t.get("status") == "completed"])
        
        # Calculate performance score
        performance_score = self._calculate_performance_score(
            completion_rate, on_time_rate, avg_completion_time, high_priority_completed, total_tasks
        )
        
        # Get rank (this will NOT trigger recursive evaluation anymore)
        rank = self._calculate_rank(employee_id, performance_score)
        
        # Calculate trend
        trend = self._calculate_trend(employee_id)
        
        evaluation = {
            "employee_id": employee_id,
            "performance_score": round(performance_score, 2),
            "completion_rate": round(completion_rate, 2),
            "on_time_rate": round(on_time_rate, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "average_completion_time": avg_completion_time,
            "high_priority_completed": high_priority_completed,
            "rank": rank,
            "trend": trend,
            "evaluated_at": datetime.now().isoformat()
        }
        
        # Only save if explicitly requested AND if no recent evaluation exists (prevent duplicates)
        # if save:
        #     self._save_evaluation(evaluation)
        print(evaluation)
        return evaluation
    
    def _calculate_performance_score(self, completion_rate: float, on_time_rate: float,
                                    avg_completion_time: float, high_priority_completed: int,
                                    total_tasks: int) -> float:
        """Calculate overall performance score"""
        # Weighted scoring
        score = 0
        score += (completion_rate * 0.4)  # 40% weight on completion
        score += (on_time_rate * 0.3)      # 30% weight on timeliness
        score += min(avg_completion_time / 7 * 100, 100) * 0.2  # 20% weight on speed (normalized)
        score += min((high_priority_completed / max(total_tasks, 1)) * 100, 100) * 0.1  # 10% weight on priority handling
        
        return min(score, 100)
    
    def _calculate_avg_completion_time(self, tasks: List[Dict[str, Any]]) -> float:
        """Calculate average task completion time in days"""
        completion_times = []
        for task in tasks:
            if task.get("status") == "completed" and task.get("created_at") and task.get("completed_at"):
                try:
                    created = datetime.fromisoformat(task["created_at"])
                    completed = datetime.fromisoformat(task["completed_at"])
                    days = (completed - created).days
                    completion_times.append(days)
                except:
                    pass
        
        return sum(completion_times) / len(completion_times) if completion_times else 0
    
    def _calculate_rank(self, employee_id: str, performance_score: float) -> int:
        """Calculate employee rank based on performance score - PREVENTS RECURSIVE EVALUATION"""
        employees = self.data_manager.load_data("employees") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        # Get all performance scores - DO NOT call evaluate_employee here to prevent recursion
        scores = []
        for emp in employees:
            emp_id = emp.get("id")
            if emp_id:
                # Get latest evaluation
                emp_perf = [p for p in performance_data if p.get("employee_id") == emp_id]
                if emp_perf:
                    scores.append(emp_perf[-1].get("performance_score", 0))
                else:
                    # Use 0 as default score instead of triggering recursive evaluation
                    # This prevents circular references and file corruption
                    scores.append(0)
        
        # Calculate rank
        scores.sort(reverse=True)
        try:
            rank = scores.index(performance_score) + 1
        except:
            rank = len(scores) + 1
        
        return rank
    
    def _calculate_trend(self, employee_id: str) -> str:
        """Calculate performance trend"""
        performance_data = self.data_manager.load_data("performances") or []
        emp_perf = [p for p in performance_data if p.get("employee_id") == employee_id]
        
        if len(emp_perf) < 2:
            return "stable"
        
        # Get last two evaluations
        recent = sorted(emp_perf, key=lambda x: x.get("evaluated_at", ""), reverse=True)[:2]
        score1 = recent[0].get("performance_score", 0)
        score2 = recent[1].get("performance_score", 0)
        
        diff = score1 - score2
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _save_evaluation(self, evaluation: Dict[str, Any]):
        """Save performance evaluation - with duplicate prevention and size limit"""
        # DEBUG: This should NOT be called if save is commented out
        print(f"🔴 DEBUG: _save_evaluation() called! This should not happen!")
        import traceback
        for line in traceback.format_stack()[-5:-1]:
            print(f"     {line.strip()}")
        
        performance_data = self.data_manager.load_data("performances") or []
        
        # Check if a recent evaluation exists (within last 5 seconds) to prevent rapid duplicates
        employee_id = evaluation.get("employee_id")
        try:
            current_time = datetime.fromisoformat(evaluation.get("evaluated_at", ""))
        except:
            current_time = datetime.now()
        
        # Remove any existing evaluations for this employee within the last 5 seconds
        filtered_data = []
        for p in performance_data:
            try:
                p_time = datetime.fromisoformat(p.get("evaluated_at", ""))
                time_diff = abs((current_time - p_time).total_seconds())
                # Keep if different employee OR more than 5 seconds apart
                if p.get("employee_id") != employee_id or time_diff >= 5:
                    filtered_data.append(p)
            except:
                # If can't parse time, keep the record
                filtered_data.append(p)
        
        performance_data = filtered_data
        
        # Append new evaluation
        performance_data.append(evaluation)
        
        # Limit to last 100 records per employee to prevent file from growing too large
        # Group by employee and keep only last 100 per employee
        employee_perf = {}
        for p in performance_data:
            emp_id = p.get("employee_id")
            if emp_id not in employee_perf:
                employee_perf[emp_id] = []
            employee_perf[emp_id].append(p)
        
        # Keep only last 100 per employee
        limited_data = []
        for emp_id, perf_list in employee_perf.items():
            sorted_perf = sorted(perf_list, key=lambda x: x.get("evaluated_at", ""), reverse=True)
            limited_data.extend(sorted_perf[:100])
        
        # Sort all by timestamp
        limited_data.sort(key=lambda x: x.get("evaluated_at", ""), reverse=True)
        
        # self.data_manager.save_data("performances", limited_data)
    
    def get_employee_performance_history(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee performance history"""
        performance_data = self.data_manager.load_data("performances") or []
        return [p for p in performance_data if p.get("employee_id") == employee_id]

