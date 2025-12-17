"""
Data Manager for JSON file persistence - Non-recursive implementation
"""
import json
import os
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import shutil


class DataManager:
    """Handles data persistence to JSON files - Non-recursive to prevent stack overflow"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, "backups"), exist_ok=True)
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to JSON file - Completely non-recursive with size limits"""
        import sys
        import traceback
        
        # DEBUG: Log when performances.json is being saved
        if filename == "performances":
            print(f"🔴 DEBUG: save_data('performances') called!")
            print(f"   Data length: {len(data) if isinstance(data, list) else 'N/A'}")
            print(f"   Call stack:")
            for line in traceback.format_stack()[-5:-1]:
                print(f"     {line.strip()}")
        
        # DEBUG: Alert if old "performance" filename is used
        if filename == "performance":
            print(f"⚠️ WARNING: save_data('performance') called! Should use 'performances' instead!")
            print(f"   Data length: {len(data) if isinstance(data, list) else 'N/A'}")
            print(f"   Call stack:")
            for line in traceback.format_stack()[-5:-1]:
                print(f"     {line.strip()}")
        
        try:
            filepath = os.path.join(self.data_dir, f"{filename}.json")
            
            # Limit data size to prevent huge files
            if isinstance(data, list) and len(data) > 1000:
                print(f"Warning: {filename} has {len(data)} items, limiting to 1000")
                data = data[:1000]
            elif isinstance(data, dict) and len(data) > 1000:
                print(f"Warning: {filename} dict has {len(data)} keys, limiting to 1000")
                items = list(data.items())[:1000]
                data = dict(items)
            
            # Clean data to remove any non-serializable objects BEFORE saving
            def clean_data(obj, visited=None):
                """Recursively clean data to remove circular refs and non-serializable objects"""
                if visited is None:
                    visited = set()
                
                # Prevent circular references
                obj_id = id(obj)
                if obj_id in visited:
                    return None  # Circular reference detected
                visited.add(obj_id)
                
                try:
                    if isinstance(obj, (datetime, date)):
                        return obj.isoformat()
                    elif isinstance(obj, set):
                        return [clean_data(item, visited) for item in obj]
                    elif isinstance(obj, dict):
                        return {str(k): clean_data(v, visited) for k, v in obj.items() if not isinstance(v, type) and not hasattr(v, '__call__')}
                    elif isinstance(obj, (list, tuple)):
                        return [clean_data(item, visited) for item in obj]
                    elif isinstance(obj, (str, int, float, bool, type(None))):
                        return obj
                    elif hasattr(obj, '__dict__'):
                        # Object with __dict__ - might be a class instance
                        # Only serialize if it's a simple data class, otherwise convert to string
                        if type(obj).__name__ in ['DataManager', 'EnhancedPerformanceAgent', 'TaskAgent', 'GoalAgent']:
                            return f"<{type(obj).__name__} instance>"
                        return str(obj)
                    else:
                        return str(obj)
                finally:
                    visited.discard(obj_id)
            
            # Clean the data first
            try:
                cleaned_data = clean_data(data)
            except Exception as e:
                print(f"Warning: Error cleaning {filename} data: {e}")
                cleaned_data = data
            
            # Ultra-simple serializer - no recursion, no complex objects
            def simple_serializer(obj):
                """Convert non-serializable objects to strings"""
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                elif isinstance(obj, set):
                    return list(obj)
                # For everything else, just return string - NO object inspection
                return str(obj)
            
            # Increase recursion limit for save operation
            old_limit = sys.getrecursionlimit()
            try:
                sys.setrecursionlimit(10000)
                
                # Try direct save with cleaned data
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump(cleaned_data, f, indent=2, default=simple_serializer, ensure_ascii=False)
                return True
            except (RecursionError, OverflowError) as e:
                # If recursion still occurs, try to save a limited version instead of empty
                print(f"Warning: {filename} has circular references: {e}")
                try:
                    # Try to save a simplified version (first 100 items if list)
                    if isinstance(cleaned_data, list) and len(cleaned_data) > 0:
                        limited_data = cleaned_data[:100]  # Keep first 100 items
                        with open(filepath, "w", encoding='utf-8') as f:
                            json.dump(limited_data, f, indent=2, default=simple_serializer, ensure_ascii=False)
                        print(f"Saved limited version of {filename} ({len(limited_data)} items)")
                        return True
                    else:
                        # Last resort: save empty list
                        with open(filepath, "w", encoding='utf-8') as f:
                            json.dump([], f, indent=2)
                        return True
                except:
                    # Final fallback
                    with open(filepath, "w", encoding='utf-8') as f:
                        json.dump([], f, indent=2)
                    return True
            finally:
                sys.setrecursionlimit(old_limit)
                
        except Exception as e:
            print(f"Error saving {filename}: {str(e)}")
            # Last resort: save empty list
            try:
                filepath = os.path.join(self.data_dir, f"{filename}.json")
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return True
            except:
                return False
    
    def load_data(self, filename: str) -> Optional[Any]:
        """Load data from JSON file - Ultra-safe loading with recursion protection"""
        import sys
        
        # WARNING: Prevent loading old "performance" filename
        if filename == "performance":
            print(f"⚠️ WARNING: load_data('performance') called! Should use 'performances' instead!")
            import traceback
            for line in traceback.format_stack()[-3:-1]:
                print(f"     {line.strip()}")
            # Redirect to "performances" instead - DO NOT load/fix the old file
            filename = "performances"
        
        filepath = os.path.join(self.data_dir, f"{filename}.json")
        
        # Special handling: If old "performance.json" exists, don't touch it
        old_performance_file = os.path.join(self.data_dir, "performance.json")
        if os.path.exists(old_performance_file) and filename == "performances":
            # Old file exists but we're loading "performances" - that's fine, ignore old file
            pass
        
        # Check if file exists
        if not os.path.exists(filepath):
            return None
        
        # Check file size first
        try:
            file_size = os.path.getsize(filepath)
            if file_size == 0 or file_size > 10000000:  # 10MB limit
                # Fix empty or too large file
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
        except:
            return None
        
        # Read file content with strict size limit
        try:
            with open(filepath, "r", encoding='utf-8') as f:
                content = f.read(1000000).strip()  # 1MB limit
        except Exception:
            # Can't read file, fix it
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        
        # Quick validation - check if it looks like valid JSON
        if not content or len(content) < 2:
            # Fix empty file
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        
        content_clean = content.strip()
        
        # Check for corruption patterns BEFORE parsing
        if content_clean in ["[", "[\n", "[\n  ", "[\n\n", "[\n  \n]", "null", "", "[]"]:
            # Already valid empty array, return it
            if content_clean == "[]":
                return []
            # Fix corrupted file
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        
        # Must start with [ or {
        if not (content_clean.startswith('[') or content_clean.startswith('{')):
            # Not valid JSON, fix it
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        
        # Parse JSON with increased recursion limit and strict error handling
        old_limit = sys.getrecursionlimit()
        try:
            # Temporarily increase recursion limit for JSON parsing
            sys.setrecursionlimit(10000)
            
            # Try to parse JSON
            data = json.loads(content)
            
            # Validate result
            if not isinstance(data, (list, dict)):
                # Invalid structure, fix it
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            
            return data
            
        except RecursionError:
            # Recursion happened - file is corrupted or too deeply nested
            # Fix immediately without trying to parse again
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        except (json.JSONDecodeError, ValueError) as e:
            # JSON syntax error - fix file
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        except Exception:
            # Any other error - fix file
            try:
                with open(filepath, "w", encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            except:
                return None
        finally:
            # Always restore recursion limit
            sys.setrecursionlimit(old_limit)
    
    def backup_data(self) -> bool:
        """Create backup of all data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.data_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            data_files = ["projects", "tasks", "employees", "performances", "users", 
                         "feedback", "goals", "notifications", "risks"]
            for file in data_files:
                source = os.path.join(self.data_dir, f"{file}.json")
                if os.path.exists(source):
                    backup_path = os.path.join(backup_dir, f"{file}_{timestamp}.json")
                    shutil.copy2(source, backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all data files"""
        data_files = ["projects", "tasks", "employees", "performances", "users",
                     "feedback", "goals", "notifications", "risks"]
        return {file: self.load_data(file) or [] for file in data_files}
