#!/bin/bash

# Run LineupBoss Backend API Server

# Change to the backend directory
cd backend

# Run the Flask app with Gunicorn
gunicorn app:app --log-level debug --bind 0.0.0.0:5000