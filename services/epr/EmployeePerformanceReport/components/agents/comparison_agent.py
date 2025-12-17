"""
Comparison Agent - Team performance comparison
"""
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class ComparisonAgent:
    """Team performance comparison agent"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
    
    def compare_team_performance(self, employee_ids: Optional[List[str]] = None,
                                department: Optional[str] = None) -> Dict[str, Any]:
        """Compare team performance"""
        employees = self.data_manager.load_data("employees") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        # Filter employees
        if department:
            employees = [e for e in employees if e.get("department") == department]
        
        if employee_ids:
            employees = [e for e in employees if e.get("id") in employee_ids]
        
        # Get performance for each employee
        comparison_data = []
        for employee in employees:
            emp_id = employee.get("id")
            
            # Get latest performance
            emp_perf = [p for p in performance_data if p.get("employee_id") == emp_id]
            if emp_perf:
                latest_perf = max(emp_perf, key=lambda x: x.get("evaluated_at", ""))
            else:
                # Evaluate if not exists - but DON'T save to prevent recursive growth
                latest_perf = self.performance_agent.evaluate_employee(emp_id, save=False)
            
            comparison_data.append({
                "employee_id": emp_id,
                "name": employee.get("name"),
                "performance_score": latest_perf.get("performance_score", 0),
                "completion_rate": latest_perf.get("completion_rate", 0),
                "on_time_rate": latest_perf.get("on_time_rate", 0),
                "rank": latest_perf.get("rank", 0),
                "trend": latest_perf.get("trend", "stable")
            })
        
        # Sort by performance score
        comparison_data.sort(key=lambda x: x.get("performance_score", 0), reverse=True)
        
        return {
            "comparison": comparison_data,
            "total_employees": len(comparison_data),
            "average_score": sum(d.get("performance_score", 0) for d in comparison_data) / len(comparison_data) if comparison_data else 0
        }
    
    def generate_comparison_chart(self, comparison_data: Dict[str, Any], chart_type: str = "bar") -> Optional[Dict[str, Any]]:
        """Generate comparison chart using Plotly"""
        if not PLOTLY_AVAILABLE:
            return None
        
        if not comparison_data.get("comparison"):
            return None
        
        data = comparison_data["comparison"]
        names = [d.get("name", d.get("employee_id", "")) for d in data]
        scores = [d.get("performance_score", 0) for d in data]
        
        if chart_type == "bar":
            fig = go.Figure(data=[
                go.Bar(
                    x=names,
                    y=scores,
                    marker_color="rgb(68, 114, 196)",
                    text=[f"{s:.1f}" for s in scores],
                    textposition="auto"
                )
            ])
            fig.update_layout(
                title="Team Performance Comparison",
                xaxis_title="Employee",
                yaxis_title="Performance Score",
                yaxis_range=[0, 100]
            )
        elif chart_type == "scatter":
            completion_rates = [d.get("completion_rate", 0) for d in data]
            fig = go.Figure(data=[
                go.Scatter(
                    x=completion_rates,
                    y=scores,
                    mode="markers+text",
                    text=names,
                    textposition="top center",
                    marker=dict(size=10, color="rgb(68, 114, 196)")
                )
            ])
            fig.update_layout(
                title="Performance vs Completion Rate",
                xaxis_title="Completion Rate (%)",
                yaxis_title="Performance Score"
            )
        else:
            return None
        
        return {
            "chart_type": chart_type,
            "figure": fig,
            "chart_data": fig.to_json(),
            "html": fig.to_html(include_plotlyjs="cdn")
        }

