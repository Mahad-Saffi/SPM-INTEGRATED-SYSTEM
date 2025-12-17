"""
Correlation Agent - Metric correlation analysis
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
import math


class CorrelationAgent:
    """Statistical correlation analysis between metrics"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
    
    def analyze_correlation(self, metric1: str, metric2: str, 
                           employee_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze correlation between two metrics"""
        employees = self.data_manager.load_data("employees") or []
        performance_data = self.data_manager.load_data("performances") or []
        tasks = self.data_manager.load_data("tasks") or []
        
        if employee_ids:
            employees = [e for e in employees if e.get("id") in employee_ids]
        
        # Collect data points
        data_points = []
        
        for employee in employees:
            emp_id = employee.get("id")
            
            # Get metric values
            value1 = self._get_metric_value(emp_id, metric1, performance_data, tasks, employees)
            value2 = self._get_metric_value(emp_id, metric2, performance_data, tasks, employees)
            
            if value1 is not None and value2 is not None:
                data_points.append({
                    "employee_id": emp_id,
                    "employee_name": employee.get("name", ""),
                    metric1: value1,
                    metric2: value2
                })
        
        if len(data_points) < 3:
            return {
                "success": False,
                "error": "Insufficient data points for correlation analysis (need at least 3)"
            }
        
        # Calculate correlation coefficient
        values1 = [dp[metric1] for dp in data_points]
        values2 = [dp[metric2] for dp in data_points]
        
        correlation = self._calculate_pearson_correlation(values1, values2)
        
        # Interpret correlation
        strength = self._interpret_correlation(correlation)
        
        return {
            "success": True,
            "metric1": metric1,
            "metric2": metric2,
            "correlation_coefficient": round(correlation, 4),
            "correlation_strength": strength["strength"],
            "correlation_direction": strength["direction"],
            "interpretation": strength["interpretation"],
            "data_points": len(data_points),
            "data": data_points
        }
    
    def _get_metric_value(self, employee_id: str, metric: str, performance_data: List[Dict[str, Any]],
                         tasks: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> Optional[float]:
        """Get value for a specific metric"""
        # Performance metrics
        if metric in ["performance_score", "completion_rate", "on_time_rate"]:
            emp_perf = [p for p in performance_data if p.get("employee_id") == employee_id]
            if emp_perf:
                latest = max(emp_perf, key=lambda x: x.get("evaluated_at", ""))
                return latest.get(metric, 0)
        
        # Task metrics
        elif metric == "total_tasks":
            emp_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
            return len(emp_tasks)
        
        elif metric == "completed_tasks":
            emp_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
            return len([t for t in emp_tasks if t.get("status") == "completed"])
        
        elif metric == "overdue_tasks":
            emp_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
            now = datetime.now()
            overdue = 0
            for task in emp_tasks:
                if task.get("status") != "completed" and task.get("due_date"):
                    try:
                        due_date = datetime.fromisoformat(task["due_date"])
                        if due_date < now:
                            overdue += 1
                    except:
                        pass
            return overdue
        
        # Training hours (placeholder - would come from training data)
        elif metric == "training_hours":
            # In real system, this would come from training records
            return 0  # Placeholder
        
        # Experience (years)
        elif metric == "experience_years":
            employee = next((e for e in employees if e.get("id") == employee_id), None)
            if employee and employee.get("hire_date"):
                try:
                    hire_date = datetime.fromisoformat(employee["hire_date"])
                    years = (datetime.now() - hire_date).days / 365.25
                    return years
                except:
                    pass
            return 0
        
        return None
    
    def _calculate_pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _interpret_correlation(self, correlation: float) -> Dict[str, Any]:
        """Interpret correlation coefficient"""
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.7:
            strength = "strong"
        elif abs_corr >= 0.4:
            strength = "moderate"
        elif abs_corr >= 0.2:
            strength = "weak"
        else:
            strength = "very weak"
        
        direction = "positive" if correlation > 0 else "negative" if correlation < 0 else "none"
        
        if abs_corr < 0.2:
            interpretation = "No significant correlation between these metrics"
        elif correlation > 0.7:
            interpretation = f"Strong positive correlation: As {strength} increases, the other tends to increase significantly"
        elif correlation > 0.4:
            interpretation = f"Moderate positive correlation: As one increases, the other tends to increase"
        elif correlation > 0.2:
            interpretation = f"Weak positive correlation: Slight tendency for both to increase together"
        elif correlation < -0.7:
            interpretation = f"Strong negative correlation: As one increases, the other tends to decrease significantly"
        elif correlation < -0.4:
            interpretation = f"Moderate negative correlation: As one increases, the other tends to decrease"
        elif correlation < -0.2:
            interpretation = f"Weak negative correlation: Slight tendency for one to decrease as the other increases"
        else:
            interpretation = "No meaningful correlation detected"
        
        return {
            "strength": strength,
            "direction": direction,
            "interpretation": interpretation
        }
    
    def analyze_multiple_correlations(self, metrics: List[str], 
                                     employee_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze correlations between multiple metrics"""
        results = []
        
        for i in range(len(metrics)):
            for j in range(i + 1, len(metrics)):
                correlation_result = self.analyze_correlation(metrics[i], metrics[j], employee_ids)
                if correlation_result.get("success"):
                    results.append(correlation_result)
        
        return {
            "success": True,
            "total_correlations": len(results),
            "correlations": results
        }

