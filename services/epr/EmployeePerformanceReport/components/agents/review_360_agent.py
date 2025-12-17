"""
360° Review Agent - Manages multi-source performance reviews
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class Review360Agent:
    """Manages 360-degree performance reviews from multiple sources"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def submit_review(self, employee_id: str, reviewer_id: str, reviewer_type: str, 
                     rating: float, comments: Optional[str] = None) -> Dict[str, Any]:
        """Submit a review for an employee
        
        Args:
            employee_id: Employee being reviewed
            reviewer_id: ID of the reviewer (employee ID or manager email)
            reviewer_type: "self", "peer", or "manager"
            rating: Rating score (1-5 or 1-100)
            comments: Optional comments
        """
        if reviewer_type not in ["self", "peer", "manager"]:
            return {"success": False, "error": "Reviewer type must be 'self', 'peer', or 'manager'"}
        
        # Normalize rating to 0-100 scale
        if rating <= 5:
            rating = (rating / 5) * 100
        
        reviews_data = self.data_manager.load_data("reviews_360") or []
        
        review_record = {
            "id": str(len(reviews_data) + 1),
            "employee_id": employee_id,
            "reviewer_id": reviewer_id,
            "reviewer_type": reviewer_type,
            "rating": round(rating, 2),
            "comments": comments,
            "created_at": datetime.now().isoformat()
        }
        
        reviews_data.append(review_record)
        self.data_manager.save_data("reviews_360", reviews_data)
        
        return {"success": True, "review": review_record}
    
    def get_employee_reviews(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get all reviews for an employee"""
        reviews_data = self.data_manager.load_data("reviews_360") or []
        return [r for r in reviews_data if r.get("employee_id") == employee_id]
    
    def calculate_average_rating(self, employee_id: str) -> Dict[str, Any]:
        """Calculate average rating from all review sources"""
        reviews = self.get_employee_reviews(employee_id)
        
        if not reviews:
            return {
                "employee_id": employee_id,
                "overall_average": 0,
                "self_rating": None,
                "peer_average": None,
                "manager_average": None,
                "total_reviews": 0
            }
        
        self_reviews = [r for r in reviews if r.get("reviewer_type") == "self"]
        peer_reviews = [r for r in reviews if r.get("reviewer_type") == "peer"]
        manager_reviews = [r for r in reviews if r.get("reviewer_type") == "manager"]
        
        self_rating = None
        if self_reviews:
            self_rating = sum(r.get("rating", 0) for r in self_reviews) / len(self_reviews)
        
        peer_average = None
        if peer_reviews:
            peer_average = sum(r.get("rating", 0) for r in peer_reviews) / len(peer_reviews)
        
        manager_average = None
        if manager_reviews:
            manager_average = sum(r.get("rating", 0) for r in manager_reviews) / len(manager_reviews)
        
        # Calculate overall average (weighted: manager 40%, peer 30%, self 30%)
        overall_average = 0
        total_weight = 0
        
        if manager_average is not None:
            overall_average += manager_average * 0.4
            total_weight += 0.4
        
        if peer_average is not None:
            overall_average += peer_average * 0.3
            total_weight += 0.3
        
        if self_rating is not None:
            overall_average += self_rating * 0.3
            total_weight += 0.3
        
        if total_weight > 0:
            overall_average = overall_average / total_weight
        else:
            overall_average = sum(r.get("rating", 0) for r in reviews) / len(reviews)
        
        return {
            "employee_id": employee_id,
            "overall_average": round(overall_average, 2),
            "self_rating": round(self_rating, 2) if self_rating else None,
            "peer_average": round(peer_average, 2) if peer_average else None,
            "manager_average": round(manager_average, 2) if manager_average else None,
            "total_reviews": len(reviews),
            "self_reviews_count": len(self_reviews),
            "peer_reviews_count": len(peer_reviews),
            "manager_reviews_count": len(manager_reviews)
        }

