"""
Enhanced AI Agent - AI-powered predictions, insights, and correlations
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent


class EnhancedAIAgent:
    """AI-powered predictions and insights agent"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
    
    def predict_performance_trend(self, employee_id: str, months: int = 3) -> Dict[str, Any]:
        """Predict performance trend for an employee"""
        performance_data = self.data_manager.load_data("performances") or []
        emp_perf = [p for p in performance_data if p.get("employee_id") == employee_id]
        
        if len(emp_perf) < 2:
            # Not enough data for prediction
            return {
                "employee_id": employee_id,
                "prediction": "insufficient_data",
                "message": "Need at least 2 performance evaluations for trend prediction"
            }
        
        # Get recent performance data
        recent_perf = sorted(emp_perf, key=lambda x: x.get("evaluated_at", ""), reverse=True)[:6]
        scores = [p.get("performance_score", 0) for p in recent_perf]
        
        # Simple linear trend calculation
        n = len(scores)
        if n >= 2:
            # Calculate trend direction
            recent_avg = sum(scores[:3]) / min(3, len(scores))
            older_avg = sum(scores[-3:]) / min(3, len(scores[-3:]))
            trend_direction = "improving" if recent_avg > older_avg else "declining" if recent_avg < older_avg else "stable"
            
            # Predict future scores
            trend_slope = (recent_avg - older_avg) / max(n - 1, 1)
            predicted_scores = []
            current_score = scores[0]
            
            for i in range(months):
                predicted_score = current_score + (trend_slope * (i + 1))
                predicted_score = max(0, min(100, predicted_score))  # Clamp between 0-100
                predicted_scores.append({
                    "month": i + 1,
                    "predicted_score": round(predicted_score, 2)
                })
            
            return {
                "employee_id": employee_id,
                "current_score": round(scores[0], 2),
                "trend_direction": trend_direction,
                "predicted_scores": predicted_scores,
                "confidence": "medium" if n >= 3 else "low"
            }
        
        return {
            "employee_id": employee_id,
            "prediction": "insufficient_data"
        }
    
    def correlate_training_with_productivity(self, employee_id: str) -> Dict[str, Any]:
        """Correlate training with productivity (placeholder implementation)"""
        # This is a placeholder - would require training data integration
        performance_data = self.data_manager.load_data("performances") or []
        emp_perf = [p for p in performance_data if p.get("employee_id") == employee_id]
        
        if not emp_perf:
            return {
                "employee_id": employee_id,
                "correlation": "no_data",
                "message": "No performance data available"
            }
        
        # Placeholder: Use performance improvement as proxy for training correlation
        if len(emp_perf) >= 2:
            recent = sorted(emp_perf, key=lambda x: x.get("evaluated_at", ""), reverse=True)[:2]
            score_change = recent[0].get("performance_score", 0) - recent[1].get("performance_score", 0)
            
            return {
                "employee_id": employee_id,
                "correlation": "positive" if score_change > 0 else "negative" if score_change < 0 else "neutral",
                "performance_change": round(score_change, 2),
                "note": "This is a placeholder. Actual training correlation requires training data integration."
            }
        
        return {
            "employee_id": employee_id,
            "correlation": "insufficient_data"
        }
    
    def generate_growth_insights(self, employee_id: str) -> Dict[str, Any]:
        """Generate growth insights and recommendations"""
        employees = self.data_manager.load_data("employees") or []
        tasks = self.data_manager.load_data("tasks") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        employee = next((e for e in employees if e.get("id") == employee_id), None)
        if not employee:
            return {"error": "Employee not found"}
        
        # Get performance history
        emp_perf = [p for p in performance_data if p.get("employee_id") == employee_id]
        if not emp_perf:
            # Evaluate if not exists - but DON'T save to prevent recursive growth
            current_perf = self.performance_agent.evaluate_employee(employee_id, save=False)
        else:
            current_perf = max(emp_perf, key=lambda x: x.get("evaluated_at", ""))
        
        # Get employee tasks
        emp_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
        
        # Generate insights
        insights = []
        recommendations = []
        
        # Performance insights
        score = current_perf.get("performance_score", 0)
        if score < 60:
            insights.append({
                "type": "performance",
                "severity": "high",
                "message": f"Performance score is below average ({score:.1f}/100)"
            })
            recommendations.append("Focus on completing tasks on time and improving quality")
        elif score > 80:
            insights.append({
                "type": "performance",
                "severity": "positive",
                "message": f"Excellent performance score ({score:.1f}/100)"
            })
            recommendations.append("Consider taking on more challenging tasks or mentoring others")
        
        # Task completion insights
        completion_rate = current_perf.get("completion_rate", 0)
        if completion_rate < 70:
            insights.append({
                "type": "completion",
                "severity": "medium",
                "message": f"Completion rate is {completion_rate:.1f}%"
            })
            recommendations.append("Work on improving task completion rate")
        
        # On-time delivery insights
        on_time_rate = current_perf.get("on_time_rate", 0)
        if on_time_rate < 80:
            insights.append({
                "type": "timeliness",
                "severity": "medium",
                "message": f"On-time delivery rate is {on_time_rate:.1f}%"
            })
            recommendations.append("Improve time management and deadline adherence")
        
        # Workload insights
        if len(emp_tasks) > 10:
            insights.append({
                "type": "workload",
                "severity": "medium",
                "message": f"High workload: {len(emp_tasks)} assigned tasks"
            })
            recommendations.append("Consider delegating or prioritizing tasks")
        
        # Trend insights
        trend = current_perf.get("trend", "stable")
        if trend == "declining":
            insights.append({
                "type": "trend",
                "severity": "high",
                "message": "Performance trend is declining"
            })
            recommendations.append("Review recent performance and identify areas for improvement")
        elif trend == "improving":
            insights.append({
                "type": "trend",
                "severity": "positive",
                "message": "Performance trend is improving"
            })
        
        return {
            "employee_id": employee_id,
            "employee_name": employee.get("name"),
            "current_performance": current_perf,
            "insights": insights,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

