-- Create admin user
-- Password: ChangeMe123!
INSERT INTO users (email, hashed_password, is_admin, created_at)
VALUES (
    'admin@pfm-qa.com',
    '$2b$12$48B0wgdiKhuny7SbezKh0O1sKal4BLlrOeVWzRrWytS4plpK2/jpu',
    true,
    NOW()
)
ON CONFLICT (email) DO NOTHING;

