# Smart Project Administrative System (SPAS)

SPAS is a robust, lightweight, Streamlit-based project management dashboard designed to help teams efficiently organize projects and tasks. 

## 🚀 Features

* **Secure Authentication**: Role-based access control (Admin, Manager, Team Member) with SHA-256 password hashing.
* **Interactive Dashboard**: View real-time metrics, task distributions, and project progress.
* **Smart Insights**: Automated warnings for overdue projects, upcoming deadlines, and overloaded team members.
* **Comprehensive Task Board**: A Kanban-style view to easily track Pending, In Progress, and Completed tasks.
* **Full CRUD Functionality**: Create, Read, Update, and Delete projects and tasks seamlessly.
* **User Profiles**: Manage your personal workload and securely update your password.

## 🛠️ Tech Stack

* **Frontend/UI**: [Streamlit](https://streamlit.io/) with Material Icons
* **Backend/Logic**: Python
* **Database**: SQLite (`spas.db`)
* **Data Manipulation**: Pandas

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <your-github-repo-url>
   cd spas
   ```

2. **Install dependencies**:
   Ensure you have Python 3.8+ installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run cp.py
   ```

## 👥 Roles & Permissions

* **Admin**: Can add new users, create/manage projects, and assign tasks.
* **Manager**: Can create/manage projects and assign tasks.
* **Team Member**: Can view assigned tasks, update task statuses, and manage their own profile.

## 📁 Project Structure

* `cp.py`: The main Streamlit application script containing all logic and UI components.
* `spas.db`: The SQLite database automatically generated to store users, projects, and tasks.
* `requirements.txt`: Python package dependencies.
