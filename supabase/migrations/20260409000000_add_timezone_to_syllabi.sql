-- Add timezone column to syllabi table for storing user's preferred export timezone
ALTER TABLE syllabi ADD COLUMN timezone TEXT;
