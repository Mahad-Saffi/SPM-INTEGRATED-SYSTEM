-- Initialize all databases for the project management system
-- This script runs automatically when PostgreSQL container starts

-- Create databases
CREATE DATABASE project_management;
CREATE DATABASE atlas;
CREATE DATABASE workpulse;
CREATE DATABASE epr;
CREATE DATABASE labs;

-- Grant privileges to admin user
GRANT ALL PRIVILEGES ON DATABASE project_management TO admin;
GRANT ALL PRIVILEGES ON DATABASE atlas TO admin;
GRANT ALL PRIVILEGES ON DATABASE workpulse TO admin;
GRANT ALL PRIVILEGES ON DATABASE epr TO admin;
GRANT ALL PRIVILEGES ON DATABASE labs TO admin;

-- Connect to each database and set up extensions
\c project_management
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c atlas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c workpulse
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c epr
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

\c labs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
