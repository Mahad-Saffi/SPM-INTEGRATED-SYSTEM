import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.services.user_service import user_service
from app.services.project_service import project_service

load_dotenv()

class AIService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        # Store conversation state per user
        self.user_conversations = {}

    def _get_user_state(self, user_id: int):
        """Get or create conversation state for a user"""
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = {
                "state": "INITIAL",
                "history": [],
                "project_description": ""
            }
        return self.user_conversations[user_id]

    def _reset_user_state(self, user_id: int):
        """Reset conversation state for a user"""
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]

    async def _get_formatted_users(self, user_id: int):
        """Get formatted list of users in the same organization"""
        from app.services.organization_service import organization_service
        
        # Get user's organization
        org = await organization_service.get_user_organization(user_id)
        if not org:
            return "No team members yet. Please add team members first."
        
        # Get organization members (pass UUID object directly)
        members = await organization_service.get_organization_members(org.id)
        
        if not members:
            return "No team members yet. Please add team members first."
        
        return "\n".join([
            f"- {member.user.username} (Role: {member.role}) - {member.description or 'No description'}"
            for member in members
        ])

    async def _call_openai(self, messages: list) -> str:
        """Call OpenAI API with conversation history"""
        if not self.client:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"I'm having trouble connecting to my AI brain right now. Error: {str(e)}"

    async def _generate_project_plan(self, project_description: str) -> dict:
        """Use OpenAI to generate a structured project plan"""
        if not self.client:
            # Fallback to mock plan if no API key
            return self._get_mock_plan(project_description)
        
        system_prompt = """You are a project planning assistant. Generate a detailed project plan in JSON format.
The plan should include:
- project_name: A concise name for the project
- description: A brief description
- epics: An array of 2-3 major epics, each with:
  - name: Epic name
  - description: Epic description
  - stories: An array of 2-3 user stories, each with:
    - name: Story name
    - description: Story description
    - tasks: An array of 3-5 specific tasks (strings)

Return ONLY valid JSON, no markdown formatting."""

        user_prompt = f"Create a project plan for: {project_description}"

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            plan = json.loads(content)
            return plan
        except Exception as e:
            print(f"Error generating plan: {e}")
            return self._get_mock_plan(project_description)

    def _get_mock_plan(self, project_description: str) -> dict:
        """Fallback mock plan when OpenAI is not available"""
        return {
            "project_name": "New Project",
            "description": project_description,
            "epics": [
                {
                    "name": "Setup & Foundation",
                    "description": "Initial project setup",
                    "stories": [
                        {
                            "name": "Project Initialization",
                            "description": "Set up project structure",
                            "tasks": [
                                "Create repository",
                                "Set up development environment",
                                "Configure CI/CD"
                            ]
                        }
                    ]
                },
                {
                    "name": "Core Features",
                    "description": "Main functionality",
                    "stories": [
                        {
                            "name": "Feature Implementation",
                            "description": "Implement core features",
                            "tasks": [
                                "Design architecture",
                                "Implement backend",
                                "Implement frontend",
                                "Write tests"
                            ]
                        }
                    ]
                }
            ]
        }

    async def get_discover_response(self, user_message: str, current_user: dict) -> str:
        """
        One-shot project creation - generates project immediately without follow-up questions.
        """
        user_id = current_user['id']
        
        # Check if user is asking a question or wants to chat (not create a project)
        question_keywords = ["what", "how", "why", "when", "where", "who", "can you", "tell me", "explain"]
        is_question = any(user_message.lower().strip().startswith(keyword) for keyword in question_keywords)
        
        if is_question:
            # Just answer the question, don't create a project
            if self.client:
                system_prompt = """You are a helpful project management assistant.
Answer the user's question concisely and friendly.
Keep responses short (2-3 sentences max).
Use emojis occasionally."""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
                response = await self._call_openai(messages)
                return response
            else:
                return "👋 I'm here to help you create projects! Just describe what you want to build, and I'll generate a complete project plan for you instantly."
        
        # User wants to create a project - do it immediately!
        try:
            from app.services.organization_service import organization_service
            
            # Get user's organization
            org = await organization_service.get_user_organization(current_user['id'])
            if not org:
                return "❌ Please create an organization and add team members before creating projects.\n\nGo to your dashboard to set up your team first!"
            
            # Check if organization has members (besides owner)
            members = await organization_service.get_organization_members(org.id)
            if len(members) < 2:  # Only owner
                return "❌ Please add at least one team member before creating projects.\n\nGo to 'Team Management' to add your team members first!"
            
            # Generate project plan from user's description
            plan = await self._generate_project_plan(user_message)
            owner_id = current_user['id']
            
            # Create the project (pass UUID object directly)
            await project_service.create_project_from_plan(plan, owner_id, org.id)
            
            # Get team info
            formatted_users = await self._get_formatted_users(current_user['id'])
            
            # Reset state for next project
            self._reset_user_state(user_id)
            
            return f"""✅ **Project Created: {plan['project_name']}**

📋 {plan['description']}

🎯 I've generated {len(plan.get('epics', []))} epics with stories and tasks for you!

👥 **Suggested Team:**
{formatted_users}

🚀 Head over to the Task Board to see your complete project plan and start working!"""
            
        except Exception as e:
            print(f"Error creating project: {e}")
            return f"😅 Oops! I hit a snag creating your project: {str(e)}\n\nTry describing your project again, and I'll create it for you!"

ai_service = AIService()
