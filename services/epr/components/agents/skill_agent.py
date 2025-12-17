"""
Skill Tracking Agent - Manages employee skills and skill levels
"""
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class SkillAgent:
    """Manages employee skills and skill levels"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def add_skill(self, employee_id: str, skill_name: str, skill_level: int) -> Dict[str, Any]:
        """Add or update a skill for an employee
        
        Args:
            employee_id: Employee ID
            skill_name: Name of the skill
            skill_level: Skill level (1-5)
        """
        if skill_level < 1 or skill_level > 5:
            return {"success": False, "error": "Skill level must be between 1 and 5"}
        
        employees = self.data_manager.load_data("employees") or []
        employee = next((e for e in employees if e.get("id") == employee_id), None)
        
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        # Initialize skills if not present
        if "skills" not in employee:
            employee["skills"] = {}
        
        # Add or update skill
        employee["skills"][skill_name] = skill_level
        
        # Update employee record
        for i, emp in enumerate(employees):
            if emp.get("id") == employee_id:
                employees[i] = employee
                break
        
        self.data_manager.save_data("employees", employees)
        return {"success": True, "skill": {skill_name: skill_level}}
    
    def get_employee_skills(self, employee_id: str) -> Dict[str, int]:
        """Get all skills for an employee"""
        employees = self.data_manager.load_data("employees") or []
        employee = next((e for e in employees if e.get("id") == employee_id), None)
        
        if not employee:
            return {}
        
        return employee.get("skills", {})
    
    def get_strong_skills(self, employee_id: str, threshold: int = 4) -> List[str]:
        """Get skills with level >= threshold"""
        skills = self.get_employee_skills(employee_id)
        return [skill for skill, level in skills.items() if level >= threshold]
    
    def get_weak_skills(self, employee_id: str, threshold: int = 2) -> List[str]:
        """Get skills with level <= threshold"""
        skills = self.get_employee_skills(employee_id)
        return [skill for skill, level in skills.items() if level <= threshold]
    
    def get_skills_needing_improvement(self, employee_id: str) -> List[str]:
        """Get skills that need improvement (level 1-3)"""
        skills = self.get_employee_skills(employee_id)
        return [skill for skill, level in skills.items() if 1 <= level <= 3]
    
    def remove_skill(self, employee_id: str, skill_name: str) -> Dict[str, Any]:
        """Remove a skill from an employee"""
        employees = self.data_manager.load_data("employees") or []
        employee = next((e for e in employees if e.get("id") == employee_id), None)
        
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        if "skills" in employee and skill_name in employee["skills"]:
            del employee["skills"][skill_name]
            
            # Update employee record
            for i, emp in enumerate(employees):
                if emp.get("id") == employee_id:
                    employees[i] = employee
                    break
            
            self.data_manager.save_data("employees", employees)
            return {"success": True}
        
        return {"success": False, "error": "Skill not found"}

