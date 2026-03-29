# Task Planner
A flexible, robust task management platform. Built with Python, FastAPI, and TailwindCSS, this full-stack application enables users to manage their schedules, while providing administrators complete oversight over system records, users, and tasks.

## 🚀 Key Features

*   **Robust Multi-Role Architecture:** Safely structure usage via `Admin` and `User` roles. Users enjoy access restricted to their individual schedules, empowering them to coordinate without friction. Alternately, Admins unlock overarching authority to track user workloads, re-assign priority tasks across the workspace, and force-reset passwords.
*   **Intuitive Visual Displays:** Visualize your schedule dynamically via three persistent modes—choose between a classic compact List View, an organized Table View, or an integrated Calendar View via FullCalendar.
*   **Intelligent Overdue Highlighting:** Overdue tasks are automatically flagged via visually striking red badges and distinct row highlights inside the table view—making sure you never miss a deadline.
*   **Granular Dynamic Filtering:** Immediately narrow what you engage with using robust filtering controls covering Task Status (All, Pending, Completed, Overdue), Priority, Category, and Assigned User (Admin-only). Filters gracefully reflect in both list/table view and instantly synchronize with the schedule calendar endpoints.
*   **Admin Settings Suite:** Seamlessly add or manage permitted workflow `Category` labels live via an administrative UI block—allowing admins to scale taxonomy effortlessly without deploying code changes!
*   **Docker-Ready Local Storage:** Ship or develop seamlessly via Docker. Built natively on top of SQLite, the container mounts `/app/data` to a steady persistent volume protecting your `scheduler.db` across container stops or redeploys!

## 💻 Tech Stack
*   **Backend:** Python 3.12, FastAPI, SQLAlchemy, SQLite
*   **Frontend:** HTML/Jinja2 Templates, TailwindCSS (CDN), FullCalendar (JS component)
*   **Dependency Management:** Pip & [**Uv**](https://github.com/astral-sh/uv)

## 🏃 Getting Started

### Option 1: Running Locally with Uvicorn

1.  **Clone the repository and jump into the directory**:
    ```bash
    git clone git@github.com:daniel-dunning/task-planner.git
    cd student
    ```
    
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  *(Optional but Recommended)* **Run the Initial Category Migration**:
    ```bash
    python migrate_categories.py
    ```
    
4.  **Start the Local Development Server**:
    ```bash
    uvicorn main:app --port 8111 --reload
    ```
    
5.  Access the server in your browser at `http://localhost:8111`.

### Option 2: Running with Docker

1.  **Build the Docker Image**:
    ```bash
    docker build -t task-planner .
    ```

2.  **Run the Container** (mounting a volume for data persistence):
    ```bash
    docker run -d -p 8111:8111 -v task-planner-data:/app/data --name task-planner-app task-planner
    ```
    
3.  Access the server in your browser at `http://localhost:8111`.

## 📜 Administrative Access
Upon launching the application empty for the first time, you must seed an `Admin` user inside the database (or through testing seeds) manually to unlock administrative workflow routes and the "Add Category" and "Add User" interfaces. From there, your workflow scales intelligently inside your active workspace.
