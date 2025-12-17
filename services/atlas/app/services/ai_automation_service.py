from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from openai import AsyncOpenAI
import json
import asyncio
import base64
from typing import Dict, List, Optional
from datetime import datetime
import os
import re

class AIAutomationService:
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.app_map = self._load_app_map()
        self.context_history = []
        self.current_task = None
        self.is_running = False
        
    def _load_app_map(self) -> Dict:
        """Load application map from JSON file"""
        map_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'app_map.json')
        with open(map_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def start_automation(self, task: str, websocket):
        """Main automation loop"""
        self.is_running = True
        self.current_task = task
        self.context_history = []
        
        try:
            # Initialize browser
            await self._send_update(websocket, "🚀 Initializing browser...", "info")
            self._init_browser()
            await asyncio.sleep(2)
            await self._send_screenshot(websocket)
            
            # Check if we need to login
            current_page = self._detect_current_page()
            if current_page == "login":
                await self._send_update(websocket, "🔐 Logging in with demo account...", "info")
                await self._auto_login(websocket)
                await asyncio.sleep(2)
                await self._send_screenshot(websocket)
            
            # Parse task with GPT
            await self._send_update(websocket, f"🤔 Understanding task: {task}", "info")
            plan = await self._create_task_plan(task)
            
            await self._send_update(websocket, f"📋 Created plan with {len(plan['steps'])} steps", "info")
            
            # Execute plan
            for idx, step in enumerate(plan['steps'], 1):
                if not self.is_running:
                    break
                    
                await self._send_update(
                    websocket, 
                    f"⚙️ Step {idx}/{len(plan['steps'])}: {step.get('description', 'Executing step')}", 
                    "info"
                )
                
                try:
                    await self._execute_step(step, websocket)
                except Exception as step_error:
                    # Try to recover from error
                    await self._send_update(websocket, f"⚠️ Step failed: {str(step_error)}", "warning")
                    await self._send_update(websocket, "🔄 Attempting to recover...", "info")
                    
                    recovered = await self._attempt_recovery(step, websocket)
                    if not recovered:
                        raise step_error
                
                await asyncio.sleep(0.5)
                await self._send_screenshot(websocket)
            
            await self._send_update(websocket, "✅ Task completed successfully!", "success")
            
        except Exception as e:
            await self._send_update(websocket, f"❌ Error: {str(e)}", "error")
            print(f"Automation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await asyncio.sleep(2)
            self._cleanup()
            self.is_running = False
    
    def _init_browser(self):
        """Initialize Selenium WebDriver"""
        options = Options()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Don't use headless mode so we can see what's happening
        # options.add_argument('--headless')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get('http://localhost:5173')
    
    async def _auto_login(self, websocket):
        """Automatically login with demo credentials"""
        try:
            # Click Try Demo button
            login_step = {
                "page": "login",
                "action": "login",
                "params": {},
                "description": "Login with demo account"
            }
            
            await self._execute_step(login_step, websocket)
            await self._send_update(websocket, "✅ Successfully logged in!", "success")
            
        except Exception as e:
            await self._send_update(websocket, f"❌ Login failed: {str(e)}", "error")
            raise
    
    async def _create_task_plan(self, task: str) -> Dict:
        """Use GPT to create execution plan"""
        
        # Add context about current state
        current_url = self.driver.current_url if self.driver else "http://localhost:5173"
        current_page = self._detect_current_page()
        
        prompt = f"""You are an AI automation assistant for the Atlas project management application.

Current State:
- Current URL: {current_url}
- Current Page: {current_page}
- User is logged in: {current_page != 'login'}

User Task: "{task}"

Application Map (available pages and actions):
{json.dumps(self.app_map, indent=2)}

Analyze the user's task and create a step-by-step plan to accomplish it.

IMPORTANT RULES:
1. If the user is asking a QUESTION (e.g., "how many projects?", "what tasks?"), you need to:
   - Navigate to the relevant page
   - Use "count_elements" action if available to count items
   - The system will report the count back to the user

2. If the user wants to PERFORM AN ACTION (e.g., "create project", "add member"), use the appropriate actions from the map

3. Use ONLY pages and actions that exist in the application map
4. Extract parameters from the user's task
5. Be specific and sequential

CRITICAL: Return ONLY valid JSON. NO comments, NO explanations, NO markdown.

Return this exact structure:
{{
    "steps": [
        {{
            "page": "page_name_from_map",
            "action": "action_name_from_map",
            "params": {{"param_name": "value"}},
            "description": "Human-readable description of what this step does"
        }}
    ]
}}

Examples:
- "How many projects?" → Navigate to dashboard, count_projects action
- "Create a project called X" → Navigate to project_creation, create_project_with_ai action
- "Open first project" → Navigate to dashboard, open_first_project action
"""
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful automation assistant. Return ONLY valid JSON without any comments or explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        # Remove any comments from JSON (just in case)
        content = re.sub(r'//.*?\n', '\n', content)  # Remove single-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)  # Remove multi-line comments
        
        try:
            plan = json.loads(content)
            return plan
        except json.JSONDecodeError as e:
            print(f"Failed to parse GPT response: {content}")
            raise Exception(f"Failed to create plan: {str(e)}")
    
    async def _execute_step(self, step: Dict, websocket):
        """Execute a single step"""
        page = step['page']
        action = step['action']
        params = step.get('params', {})
        
        # Navigate to page if needed
        current_page = self._detect_current_page()
        if current_page != page:
            await self._navigate_to_page(page, websocket)
            await asyncio.sleep(1)
        
        # Execute action
        if page not in self.app_map['pages']:
            raise Exception(f"Page '{page}' not found in application map")
        
        if action not in self.app_map['pages'][page]['actions']:
            raise Exception(f"Action '{action}' not found for page '{page}'")
        
        action_def = self.app_map['pages'][page]['actions'][action]
        
        for action_step in action_def['steps']:
            await self._execute_action_step(action_step, params, websocket)
            await asyncio.sleep(0.3)
    
    async def _execute_action_step(self, action_step: Dict, params: Dict, websocket):
        """Execute individual action step"""
        action_type = action_step['type']
        description = action_step.get('description', '')
        
        if description:
            await self._send_update(websocket, f"  → {description}", "action")
        
        try:
            if action_type == 'click':
                selector = action_step['selector']
                fallback_selectors = action_step.get('fallback_selectors', [])
                element = self._find_element_with_fallback(selector, fallback_selectors)
                element.click()
                
            elif action_type == 'input':
                selector = action_step['selector']
                fallback_selectors = action_step.get('fallback_selectors', [])
                param_name = action_step['param']
                value = params.get(param_name, '')
                
                element = self._find_element_with_fallback(selector, fallback_selectors)
                element.clear()
                element.send_keys(value)
                
            elif action_type == 'select':
                selector = action_step['selector']
                fallback_selectors = action_step.get('fallback_selectors', [])
                param_name = action_step['param']
                value = params.get(param_name, '')
                
                from selenium.webdriver.support.ui import Select
                element = self._find_element_with_fallback(selector, fallback_selectors)
                select = Select(element)
                select.select_by_visible_text(value)
                
            elif action_type == 'wait':
                seconds = action_step.get('seconds', 1)
                await asyncio.sleep(seconds)
                
            elif action_type == 'wait_for_text':
                text = action_step['text']
                timeout = action_step.get('timeout', 10)
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{text}')]"))
                )
                
            elif action_type == 'count_elements':
                selector = action_step['selector']
                fallback_selectors = action_step.get('fallback_selectors', [])
                elements = self._find_elements_with_fallback(selector, fallback_selectors)
                count = len(elements)
                await self._send_update(websocket, f"  → Found {count} elements", "info")
                return count
                
            elif action_type == 'find_and_click':
                find_text = action_step['find_text']
                # Replace placeholders with actual values
                for key, value in params.items():
                    find_text = find_text.replace(f"{{{key}}}", value)
                
                # Find element containing text
                xpath = f"//*[contains(text(), '{find_text}')]"
                element = self.driver.find_element(By.XPATH, xpath)
                
                # Find button within or near that element
                then_click = action_step['then_click']
                parent = element.find_element(By.XPATH, "..")
                button = parent.find_element(By.CSS_SELECTOR, then_click)
                button.click()
                
        except Exception as e:
            await self._send_update(websocket, f"⚠️ Action failed: {str(e)}", "warning")
            raise
    
    def _find_element(self, selector: str, timeout: int = 10):
        """Find element with multiple selector strategies"""
        # Try CSS selector first (if it doesn't contain :contains)
        if ':contains' not in selector:
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            except:
                pass
        
        # Try XPath if selector contains :contains
        if ':contains' in selector:
            # Convert jQuery-style :contains to XPath
            match = re.search(r'([^:]+):contains\([\'"]([^\'"]+)[\'"]\)', selector)
            if match:
                tag = match.group(1) or '*'
                text = match.group(2)
                xpath = f"//{tag}[contains(text(), '{text}')]"
                try:
                    return WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                except:
                    pass
        
        # Try as XPath
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, selector))
            )
        except:
            raise NoSuchElementException(f"Could not find element: {selector}")
    
    def _find_element_with_fallback(self, selector: str, fallback_selectors: List[str], timeout: int = 10):
        """Find element with fallback selectors"""
        # Try primary selector first
        try:
            return self._find_element(selector, timeout=2)
        except NoSuchElementException:
            pass
        
        # Try fallback selectors
        for fallback in fallback_selectors:
            try:
                return self._find_element(fallback, timeout=2)
            except NoSuchElementException:
                continue
        
        # If all fail, raise exception with all attempted selectors
        all_selectors = [selector] + fallback_selectors
        raise NoSuchElementException(f"Could not find element with any selector: {', '.join(all_selectors)}")
    
    def _find_elements_with_fallback(self, selector: str, fallback_selectors: List[str], timeout: int = 10):
        """Find multiple elements with fallback selectors"""
        # Try primary selector first
        try:
            if ':contains' not in selector:
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    return self.driver.find_elements(By.CSS_SELECTOR, selector)
                except:
                    pass
            
            # Try as XPath
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                return self.driver.find_elements(By.XPATH, selector)
            except:
                pass
        except:
            pass
        
        # Try fallback selectors
        for fallback in fallback_selectors:
            try:
                if ':contains' not in fallback:
                    try:
                        WebDriverWait(self.driver, 2).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, fallback))
                        )
                        return self.driver.find_elements(By.CSS_SELECTOR, fallback)
                    except:
                        pass
                
                # Try as XPath
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, fallback))
                    )
                    return self.driver.find_elements(By.XPATH, fallback)
                except:
                    continue
            except:
                continue
        
        # If all fail, return empty list
        return []
    
    def _detect_current_page(self) -> str:
        """Detect which page we're currently on"""
        if not self.driver:
            return "unknown"
        
        current_url = self.driver.current_url
        page_title = self.driver.title
        
        # Special case: root URL could be login or dashboard
        if current_url == "http://localhost:5173/" or current_url == "http://localhost:5173":
            # Check if we see login elements (Try Demo button)
            try:
                # Try multiple ways to detect login page
                self.driver.find_element(By.XPATH, "//button[contains(text(), 'Try Demo')]")
                return "login"
            except:
                try:
                    self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
                    return "login"
                except:
                    # If no login button, we're on dashboard
                    return "dashboard"
        
        # Check URL patterns for all pages
        for page_name, page_def in self.app_map['pages'].items():
            # Check URL pattern first (more specific)
            url_pattern = page_def['identifiers'].get('url_pattern', '')
            if url_pattern and re.search(url_pattern, current_url):
                return page_name
        
        # Fallback: check if URL contains page URL
        for page_name, page_def in self.app_map['pages'].items():
            page_url = page_def['url']
            # Extract path from page URL
            if '{' in page_url:
                # Handle dynamic URLs like /project/{project_id}
                url_template = page_url.replace('http://localhost:5173', '')
                url_pattern = url_template.replace('{project_id}', '[a-f0-9-]+')
                if re.search(url_pattern, current_url):
                    return page_name
            elif page_url in current_url:
                return page_name
        
        return "unknown"
    
    async def _navigate_to_page(self, target_page: str, websocket):
        """Navigate to a specific page"""
        current_page = self._detect_current_page()
        
        await self._send_update(websocket, f"🧭 Navigating from {current_page} to {target_page}", "info")
        
        # Direct navigation
        if target_page in self.app_map['pages']:
            target_url = self.app_map['pages'][target_page]['url']
            self.driver.get(target_url)
            await asyncio.sleep(1)
    
    async def _attempt_recovery(self, failed_step: Dict, websocket) -> bool:
        """Attempt to recover from a failed step by analyzing current state"""
        try:
            # Get current state
            current_url = self.driver.current_url
            current_page = self._detect_current_page()
            target_page = failed_step.get('page', 'unknown')
            
            await self._send_update(
                websocket, 
                f"📍 Current location: {current_page} (URL: {current_url})", 
                "info"
            )
            await self._send_update(
                websocket, 
                f"🎯 Target location: {target_page}", 
                "info"
            )
            
            # If we're on login page, login first
            if current_page == "login":
                await self._send_update(websocket, "🔐 Detected login page, logging in...", "info")
                try:
                    await self._auto_login(websocket)
                    await asyncio.sleep(2)
                    
                    # Re-detect page after login
                    current_page = self._detect_current_page()
                    await self._send_update(websocket, f"✅ Logged in, now on: {current_page}", "info")
                    
                    # If we need to be on a different page, navigate there
                    if current_page != target_page and target_page != 'unknown':
                        await self._navigate_to_page(target_page, websocket)
                        await asyncio.sleep(2)
                    
                    # Try the step again
                    await self._send_update(websocket, "🔄 Retrying step after login...", "info")
                    await self._execute_step(failed_step, websocket)
                    return True
                except Exception as login_error:
                    await self._send_update(websocket, f"❌ Login failed: {str(login_error)}", "error")
                    return False
            
            # If we're not on the right page, navigate there
            if current_page != target_page and target_page != 'unknown':
                await self._send_update(
                    websocket, 
                    f"🧭 Wrong page detected, navigating to {target_page}...", 
                    "info"
                )
                try:
                    await self._navigate_to_page(target_page, websocket)
                    await asyncio.sleep(2)
                    
                    # Try the step again
                    await self._send_update(websocket, "🔄 Retrying step after navigation...", "info")
                    await self._execute_step(failed_step, websocket)
                    return True
                except Exception as nav_error:
                    await self._send_update(websocket, f"❌ Navigation failed: {str(nav_error)}", "error")
                    # Continue to AI suggestion
            
            # If we're on the right page but element not found, wait and retry
            if current_page == target_page:
                await self._send_update(websocket, "⏳ Waiting for page to fully load...", "info")
                await asyncio.sleep(2)
                
                try:
                    await self._send_update(websocket, "🔄 Retrying step after wait...", "info")
                    await self._execute_step(failed_step, websocket)
                    return True
                except Exception as retry_error:
                    await self._send_update(websocket, f"⚠️ Retry failed: {str(retry_error)}", "warning")
                    # Continue to AI suggestion
            
            # If element not found, use GPT to find alternative
            await self._send_update(
                websocket, 
                "🤖 Asking AI for alternative approach...", 
                "info"
            )
            
            # Get page source for context
            page_source = self.driver.page_source[:5000]  # First 5000 chars
            
            prompt = f"""The automation failed on this step:
Page: {target_page}
Action: {failed_step.get('action', 'unknown')}
Description: {failed_step.get('description', 'N/A')}

Current URL: {current_url}
Current Page: {current_page}

Page HTML (first 5000 chars):
{page_source}

Suggest an alternative approach or confirm if the task is impossible from current state.
Return JSON with: {{"possible": true/false, "suggestion": "what to do next"}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful automation assistant. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            suggestion = json.loads(content)
            
            if suggestion.get('possible', False):
                await self._send_update(
                    websocket, 
                    f"💡 AI suggestion: {suggestion.get('suggestion', 'Try alternative approach')}", 
                    "info"
                )
                # For now, just log the suggestion
                # In future, could implement dynamic action execution
                return False
            else:
                await self._send_update(
                    websocket, 
                    f"❌ AI says: {suggestion.get('suggestion', 'Cannot proceed from current state')}", 
                    "error"
                )
                return False
                
        except Exception as recovery_error:
            await self._send_update(
                websocket, 
                f"❌ Recovery failed: {str(recovery_error)}", 
                "error"
            )
            return False
    
    async def _send_screenshot(self, websocket):
        """Send current browser screenshot"""
        if not self.driver:
            return
        
        try:
            screenshot = self.driver.get_screenshot_as_base64()
            await websocket.send_json({
                "type": "screenshot",
                "data": screenshot,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Screenshot error: {e}")
    
    async def _send_update(self, websocket, message: str, level: str):
        """Send status update"""
        try:
            await websocket.send_json({
                "type": "update",
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"WebSocket send error: {e}")
    
    def _cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def stop(self):
        """Stop automation"""
        self.is_running = False
        self._cleanup()

# Global instance
automation_service = AIAutomationService()
