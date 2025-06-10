-- Create database
CREATE DATABASE expense_splitter;

-- Connect to the database
\c expense_splitter

-- Create people table
CREATE TABLE people (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Create expenses table
CREATE TABLE expenses (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10,2) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_by INTEGER REFERENCES people(id)
);

-- Create expense_shares table
CREATE TABLE expense_shares (
    id SERIAL PRIMARY KEY,
    expense_id INTEGER REFERENCES expenses(id),
    person_id INTEGER REFERENCES people(id),
    share_type VARCHAR(20) NOT NULL, -- percentage, exact, or equal
    share_value DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_expense FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
    CONSTRAINT fk_person FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO people (name) VALUES ('Shantanu'), ('Sanket'), ('Om');

-- Insert sample expenses
INSERT INTO expenses (amount, description, paid_by) VALUES
    (600.00, 'Dinner at restaurant', (SELECT id FROM people WHERE name = 'Shantanu')),
    (450.00, 'Groceries', (SELECT id FROM people WHERE name = 'Sanket')),
    (300.00, 'Petrol', (SELECT id FROM people WHERE name = 'Om')),
    (500.00, 'Movie Tickets', (SELECT id FROM people WHERE name = 'Shantanu')),
    (280.00, 'Pizza', (SELECT id FROM people WHERE name = 'Sanket'));

-- Insert sample shares
INSERT INTO expense_shares (expense_id, person_id, share_type, share_value) VALUES
    -- Dinner split equally
    ((SELECT id FROM expenses WHERE description = 'Dinner at restaurant'), (SELECT id FROM people WHERE name = 'Shantanu'), 'percentage', 33.33),
    ((SELECT id FROM expenses WHERE description = 'Dinner at restaurant'), (SELECT id FROM people WHERE name = 'Sanket'), 'percentage', 33.33),
    ((SELECT id FROM expenses WHERE description = 'Dinner at restaurant'), (SELECT id FROM people WHERE name = 'Om'), 'percentage', 33.33),
    
    -- Groceries split 50-50
    ((SELECT id FROM expenses WHERE description = 'Groceries'), (SELECT id FROM people WHERE name = 'Sanket'), 'percentage', 50),
    ((SELECT id FROM expenses WHERE description = 'Groceries'), (SELECT id FROM people WHERE name = 'Shantanu'), 'percentage', 50),
    
    -- Petrol split exactly
    ((SELECT id FROM expenses WHERE description = 'Petrol'), (SELECT id FROM people WHERE name = 'Om'), 'exact', 150.00),
    ((SELECT id FROM expenses WHERE description = 'Petrol'), (SELECT id FROM people WHERE name = 'Sanket'), 'exact', 150.00),
    
    -- Movie tickets split equally
    ((SELECT id FROM expenses WHERE description = 'Movie Tickets'), (SELECT id FROM people WHERE name = 'Shantanu'), 'percentage', 33.33),
    ((SELECT id FROM expenses WHERE description = 'Movie Tickets'), (SELECT id FROM people WHERE name = 'Sanket'), 'percentage', 33.33),
    ((SELECT id FROM expenses WHERE description = 'Movie Tickets'), (SELECT id FROM people WHERE name = 'Om'), 'percentage', 33.33),
    
    -- Pizza split exactly
    ((SELECT id FROM expenses WHERE description = 'Pizza'), (SELECT id FROM people WHERE name = 'Sanket'), 'exact', 140.00),
    ((SELECT id FROM expenses WHERE description = 'Pizza'), (SELECT id FROM people WHERE name = 'Om'), 'exact', 140.00);
