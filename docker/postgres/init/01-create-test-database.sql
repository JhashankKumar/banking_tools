-- Runs once when the database volume is first created.
-- Separate database for the backend test suite (tests refuse to run unless the name ends in _test).
CREATE DATABASE openfraud_test;
