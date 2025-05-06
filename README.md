# PuckPattern

A tactical hockey intelligence platform that decodes, visualizes, and simulates why players and teams succeed using deep behavioral modeling, system inference, and custom analytics.

## Overview

PuckPattern analyzes NHL event data to infer tactical systems, visualize player behavior, profile team identities, predict player performance in different systems, and define new performance metrics aligned to on-ice decision-making.

## Features

- **Transition Engine**: Track how teams/players move the puck between zones
- **Shot & Chance Map**: Visualize where shots are taken and their quality
- **Cycle & Movement Engine**: Reconstruct puck movement in offensive zone
- **Rush & Breakout Viewer**: Track puck movement from defensive to offensive zone
- **Netfront Battle Index**: Track physical engagements at the net
- **Forecheck Disruption Map**: Identify forecheck pressure points
- **Defensive System Viewer**: Classify team defensive structure
- **Power Play Decoder**: Detect and visualize PP formations
- **And many more...**

## Custom Metrics

- **Entry Conversion Rate (ECR)**: Controlled entries leading to shots/chances
- **Puck Recovery Impact (PRI)**: Weighted sum of puck recoveries
- **Positional Disruption Index (PDI)**: Effectiveness of defensive positioning
- **xGΔPSM**: Impact of passing on expected goal value
- **System Fidelity Score (SFS)**: Player adherence to team systems
- **Offensive Momentum Curve (OMC)**: Change in offensive pressure over time
- **ICE+**: Composite player impact score

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, pandas, NumPy, scikit-learn
- **Frontend**: React, Redux Toolkit, D3.js, React-Vis, Material-UI/Chakra UI
- **Database**: PostgreSQL
- **Hosting**: Vercel, Railway/Render, Supabase/ElephantSQL
- **CI/CD**: GitHub Actions

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL
- Node.js (for frontend)

### Backend Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/puckpattern.git
   cd puckpattern
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   # Create a .env file with the following content
   DATABASE_URL=postgresql://postgres:postgres@localhost/puckpattern
   ```

5. Run database migrations:
   ```
   alembic upgrade head
   ```

6. Start the development server:
   ```
   uvicorn app.main:app --reload
   ```

7. The API will be available at http://127.0.0.1:8000

### Data Import

To import NHL data into the database, use the provided import script:

```
# Import all NHL teams
python scripts/import_data.py teams

# Import rosters for all teams
python scripts/import_data.py roster --all

# Import a specific game
python scripts/import_data.py game --game-id 2022020001

# Import schedule for a date range
python scripts/import_data.py schedule --start-date 2022-10-01 --end-date 2022-10-31

# Import a full season
python scripts/import_data.py season --season 20222023
```

### Running Tests

To run tests:

```
cd backend
pytest
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Core Endpoints

- `/api/teams`: Team management
- `/api/players`: Player management
- `/api/games`: Game management
- `/api/events`: Game event management
- `/api/shots`: Shot analysis
- `/api/entries`: Zone entry analysis
- `/api/metrics`: Performance metrics

## Development Roadmap

The project is being developed in phases according to the project development plan:

1. **Foundation Microprojects** (Current Phase)
   - Core Data Model & API Foundation
   - Frontend Framework & Design System

2. **Event Analysis Microprojects**
   - Shot Analysis
   - Puck Movement
   - Zone Control
   - Physical Play
   - Defensive Systems
   - Set Pieces

3. **Team/Player Analysis Microprojects**
   - Power Play Decoder
   - Penalty Kill Analysis
   - Team Strategy Profiler
   - Player Intelligence
   - Deployment Analysis
   - System Fit Engine
   - ICE+ Composite Score

4. **Integration Microprojects**
   - Dashboard Integration
   - Advanced Search & Filtering
   - User Management & Permissions

5. **Deployment & Production**

## License

[MIT License](LICENSE)