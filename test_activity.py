import time
import requests
import json

# Wait for services to be ready
print('Waiting for services to be ready...')
time.sleep(10)

# Step 1: Register user
print('\nSTEP 1: Register User')
register_response = requests.post(
    'http://localhost:9000/api/v1/auth/register',
    json={
        'email': f'testuser{int(time.time())}@example.com',
        'name': 'Test User',
        'password': 'TestPass123!',
        'role': 'member'
    }
)
print(f'Status: {register_response.status_code}')
register_data = register_response.json()
print(json.dumps(register_data, indent=2))

token = register_data.get('access_token', '')
user_id = register_data.get('user', {}).get('id', '')

if not token:
    print('Failed to get token')
    exit(1)

print(f'Token: {token[:30]}...')
print(f'User ID: {user_id}')

# Step 2: Log activity
print('\nSTEP 2: Log Activity')
activity_response = requests.post(
    'http://localhost:9000/api/v1/monitoring/activity/log',
    headers={'Authorization': f'Bearer {token}'},
    json={
        'activity_type': 'task_completed',
        'description': 'Completed login bug fix',
        'duration_minutes': 120,
        'tags': ['bug-fix', 'urgent']
    }
)
print(f'Status: {activity_response.status_code}')
print(json.dumps(activity_response.json(), indent=2))

if activity_response.status_code == 200:
    print('Activity logged successfully!')
else:
    print('Failed to log activity')
