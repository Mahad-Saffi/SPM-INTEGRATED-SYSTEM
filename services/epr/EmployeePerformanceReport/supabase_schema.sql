-- Supabase PostgreSQL Schema for Employee Performance System
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Employees Table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    department VARCHAR(100),
    position VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    hire_date TIMESTAMP,
    skills JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    deadline TIMESTAMP,
    manager VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(50) DEFAULT 'medium',
    assigned_to UUID REFERENCES employees(id),
    project_id UUID REFERENCES projects(id),
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_by VARCHAR(255)
);

-- Performance Evaluations Table
CREATE TABLE IF NOT EXISTS performances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) NOT NULL,
    performance_score DECIMAL(5,2) NOT NULL,
    completion_rate DECIMAL(5,2) NOT NULL,
    on_time_rate DECIMAL(5,2) NOT NULL,
    rank INTEGER,
    trend VARCHAR(50),
    evaluation_date TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance Goals Table
CREATE TABLE IF NOT EXISTS performance_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES employees(id) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    goal_type VARCHAR(50) NOT NULL,
    target_value DECIMAL(10,2),
    current_value DECIMAL(10,2) DEFAULT 0,
    start_date TIMESTAMP NOT NULL,
    target_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'in_progress',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Peer Feedback Table
CREATE TABLE IF NOT EXISTS peer_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) NOT NULL,
    reviewer_id UUID REFERENCES employees(id) NOT NULL,
    project_id UUID REFERENCES projects(id),
    feedback_type VARCHAR(50) NOT NULL,
    rating DECIMAL(3,2) NOT NULL,
    feedback_text TEXT NOT NULL,
    is_anonymous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance Reviews Table
CREATE TABLE IF NOT EXISTS performance_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID REFERENCES employees(id) NOT NULL,
    reviewer_id UUID REFERENCES employees(id) NOT NULL,
    review_period_start TIMESTAMP NOT NULL,
    review_period_end TIMESTAMP NOT NULL,
    overall_rating DECIMAL(3,2),
    strengths TEXT,
    areas_for_improvement TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Skill Assessments Table
CREATE TABLE IF NOT EXISTS skill_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES employees(id) NOT NULL,
    skill_name VARCHAR(255) NOT NULL,
    skill_category VARCHAR(50),
    proficiency_level VARCHAR(50) NOT NULL,
    proficiency_score DECIMAL(5,2) NOT NULL,
    assessed_by UUID REFERENCES employees(id),
    assessment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance Metrics Table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES employees(id) NOT NULL,
    metric_date TIMESTAMP NOT NULL,
    tasks_completed INTEGER DEFAULT 0,
    tasks_on_time INTEGER DEFAULT 0,
    productivity_score DECIMAL(5,2) DEFAULT 0,
    collaboration_score DECIMAL(5,2) DEFAULT 0,
    overall_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES employees(id) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_performances_employee_id ON performances(employee_id);
CREATE INDEX IF NOT EXISTS idx_performances_evaluation_date ON performances(evaluation_date);
CREATE INDEX IF NOT EXISTS idx_goals_user_id ON performance_goals(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_employee_id ON peer_feedback(employee_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- Enable Row Level Security (RLS) - Optional, configure as needed
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE performances ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE peer_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust based on your security needs)
-- For development, allow all operations
CREATE POLICY "Allow all operations" ON employees FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON projects FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON tasks FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON performances FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON performance_goals FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON peer_feedback FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON performance_reviews FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON skill_assessments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON performance_metrics FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations" ON notifications FOR ALL USING (true) WITH CHECK (true);

