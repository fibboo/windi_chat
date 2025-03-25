# WinDi Chat

## Overview

WinDi Chat is a project that provides a chat application backend powered by FastAPI and SQLAlchemy, featuring
database migrations managed by Alembic. It includes built-in API documentation accessible via Swagger and Redoc, and
offers comprehensive test support either through Docker or locally using pytest.


## Quick Start

1. Clone the repository:
   ```bash
   git clone git@github.com:fibboo/windi_chat.git
   ```
2. Navigate to the project directory:
   ```bash
   cd windi_chat
   ```
3. Build the Docker images:
   ```bash
   docker compose build
   ```
4. Start the project:
   ```bash
   docker compose up -d
   ```
5. Create the database:
   ```bash
   docker compose exec postgres psql -U user_id -d postgres -c "CREATE DATABASE windi_chat;"
   ```
6. Apply database migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```
7. Populate the database with test data (optional):
   ```bash
   docker compose exec backend python app/test_scripts/generate_test_data.py
   ```
   
Once all steps are completed, your project will be available at:  
[http://localhost:8000](http://localhost:8000)

---

## API Documentation

The project provides built-in API documentation, available via Swagger or Redoc. To access it, open the following URL after starting the project:

Swagger - [http://localhost:8000/docs](http://localhost:8000/docs)

Redoc - [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Running Tests

You can verify the functionality of the project by running the tests. There are two ways to do so:

1. **Inside the Docker container** (service should be running):
   ```bash
   docker compose exec backend pytest -n auto
   ```

2. **Locally (if you have Python installed)**:
   Ensure your virtual environment is activated, then run:
   ```bash
   pytest -n auto
   ```
