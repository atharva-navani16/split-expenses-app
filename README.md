# Split App - Complete Backend Assignment Solution

A production-ready expense splitting application built with FastAPI, PostgreSQL, and Docker. This system helps groups split expenses fairly and calculates optimal settlements to minimize transactions.

## 🏗️ Project Structure

```
split-app/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Main FastAPI application
│   │   ├── database.py        # Database configuration
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── crud.py            # Database operations
│   │   └── api/               # API endpoints
│   │       ├── __init__.py
│   │       ├── expenses.py    # Expense management
│   │       ├── balances.py    # Balance calculations
│   │       └── settlements.py # Settlement optimization
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Backend container
├── frontend/                  # Web Interface
│   ├── index.html            # Main HTML file
│   └── static/
│       ├── css/
│       │   └── style.css     # Styling