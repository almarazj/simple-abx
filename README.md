# ABX Test Application

A comprehensive FastAPI-based web application for conducting ABX subjective audio quality tests. This application allows researchers and audio engineers to evaluate audio processing algorithms through blind listening tests.

## Features

### Core Functionality

- **ABX Test Interface**: Three-button interface (A, B, X) with seamless audio switching
- **Participant Management**: Anonymous demographic data collection
- **Flexible Response Options**: Support for "tie/can't identify" responses
- **Real-time Statistics**: Detailed results analysis and visualization
- **MySQL Integration**: Persistent data storage using MySQL
- **Dockerized Deployment**: Easy setup with Docker and docker-compose

## Quickstart

```bash
# Clone the repository
git clone https://github.com/almarazj/simple-abx/
cd simple-abx

# Build and run with Docker
docker-compose up --build
```

- Access the API docs at `http://localhost:8000/docs`
- Access the web interface at `http://localhost:8000/`

## Configuration

- All configuration is handled via `app/core/config.py` and environment variables.
- See `.env.example` for available options.

## Project Structure

```bash
subjective-test-flask/
├── main.py                 # FastAPI entrypoint
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build file
├── docker-compose.yml      # Docker Compose setup (app + MySQL)
├── .env                    # Environment variables
├── .env.example            # Example env file
├── README.md
├── logs/                   # Log files
├── scripts/                # Utility scripts
├── app/
│   ├── core/               # Core app logic (config, logging, app factory)
│   ├── database/           # Database models, session, and init logic
│   ├── models/             # Pydantic schemas, enums
│   ├── utils/              # Utility functions
│   └── web/                # Web routes (FastAPI)
├── static/                 # Static files (audio, js, css, images)
├── templates/              # Jinja2 templates (web UI)
└── ...
```
