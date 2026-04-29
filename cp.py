import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime, date

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Smart Project Administrative System",
    page_icon=":material/bar_chart:",
    layout="wide"
)

# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

.stButton>button {
    border-radius: 8px;
    height: 40px;
    width: 100%;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------

conn = sqlite3.connect("spas.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
username TEXT,
password TEXT,
role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS projects(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
description TEXT,
deadline TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
project_id INTEGER,
task_name TEXT,
assigned_to TEXT,
status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS project_members(
project_id INTEGER,
username TEXT,
PRIMARY KEY (project_id, username)
)
""")

conn.commit()

# ---------------- TITLE ----------------

st.title(":material/bar_chart: Smart Project Administrative System")

# ---------------- AUTHENTICATION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.role = None
    st.session_state.username = None

if not st.session_state.logged_in:
    st.header(":material/lock: Welcome")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                hashed_pwd = hash_password(password)
                cursor.execute("SELECT name, role, username FROM users WHERE username=? AND password=?", (username, hashed_pwd))
                user = cursor.fetchone()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.current_user = user[0]
                    st.session_state.role = user[1]
                    st.session_state.username = user[2]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    
    with tab2:
        with st.form("signup_form"):
            new_name = st.text_input("Full Name")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            new_role = st.selectbox("Role", ["Admin", "Manager", "Team Member"])
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if not new_name.strip() or not new_username.strip() or not new_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                else:
                    cursor.execute("SELECT * FROM users WHERE username=?", (new_username,))
                    if cursor.fetchone():
                        st.error("Username already exists")
                    else:
                        hashed_pwd = hash_password(new_password)
                        cursor.execute("INSERT INTO users(name, username, password, role) VALUES (?,?,?,?)", 
                                       (new_name, new_username, hashed_pwd, new_role))
                        conn.commit()
                        st.success("Account created successfully! Please login in the Login tab.")
    st.stop()

# ---------------- NAVIGATION ----------------

st.sidebar.title(f"Welcome, {st.session_state.current_user}")
st.sidebar.subheader(f"Role: {st.session_state.role}")
st.sidebar.divider()
st.sidebar.subheader("Navigation")

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if st.sidebar.button(":material/dashboard: Dashboard"):
    st.session_state.page = "Dashboard"

if st.sidebar.button(":material/view_kanban: Task Board"):
    st.session_state.page = "Task Board"

if st.sidebar.button(":material/person: My Profile"):
    st.session_state.page = "My Profile"

if st.session_state.role == "Admin":
    if st.sidebar.button(":material/person_add: Add User"):
        st.session_state.page = "Add User"

if st.session_state.role in ["Admin", "Manager"]:
    if st.sidebar.button(":material/create_new_folder: Create Project"):
        st.session_state.page = "Create Project"

if st.sidebar.button(":material/add_task: Add Task"):
    st.session_state.page = "Add Task"

if st.sidebar.button(":material/edit_document: Manage Tasks"):
    st.session_state.page = "Manage Tasks"

if st.sidebar.button(":material/folder_managed: Manage Projects"):
    st.session_state.page = "Manage Projects"

st.sidebar.divider()
if st.sidebar.button(":material/logout: Logout"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.role = None
    st.rerun()

menu = st.session_state.page

# ---------------- DASHBOARD ----------------

if menu == "Dashboard":

    st.header(":material/dashboard: Project Dashboard")

    users = pd.read_sql("SELECT * FROM users", conn)
    
    if st.session_state.role == "Team Member":
        projects = pd.read_sql("""
            SELECT p.* FROM projects p 
            JOIN project_members pm ON p.id = pm.project_id 
            WHERE pm.username = ?
        """, conn, params=(st.session_state.username,))
        
        if not projects.empty:
            project_ids = projects["id"].tolist()
            placeholders = ",".join(["?"] * len(project_ids))
            tasks = pd.read_sql(f"SELECT * FROM tasks WHERE project_id IN ({placeholders})", conn, params=tuple(project_ids))
        else:
            tasks = pd.DataFrame(columns=["id", "project_id", "task_name", "assigned_to", "status"])
    else:
        projects = pd.read_sql("SELECT * FROM projects", conn)
        tasks = pd.read_sql("SELECT * FROM tasks", conn)

    # --- My Tasks Section ---
    st.subheader(":material/assignment_ind: My Tasks")
    my_tasks = tasks[tasks["assigned_to"] == st.session_state.current_user]
    if not my_tasks.empty:
        st.dataframe(my_tasks, use_container_width=True)
    else:
        st.info("You have no tasks assigned.")
    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("Users", len(users))
    col2.metric("Projects", len(projects))
    col3.metric("Tasks", len(tasks))

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        st.subheader(":material/folder: Projects")

        if not projects.empty:
            st.dataframe(projects, use_container_width=True)
        else:
            st.info("No projects created yet")

    with colB:
        st.subheader(":material/pie_chart: Task Status Distribution")
        if not tasks.empty:
            status_counts = tasks["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig = px.pie(status_counts, values="Count", names="Status", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("View All Tasks"):
                st.dataframe(tasks, use_container_width=True)
        else:
            st.info("No tasks created yet")

    st.divider()
    
    st.subheader(":material/lightbulb: Smart Insights")
    
    # Resource Load Insight
    if not tasks.empty:
        pending_in_progress = tasks[tasks["status"].isin(["Pending", "In Progress"])]
        if not pending_in_progress.empty:
            user_load = pending_in_progress["assigned_to"].value_counts()
            overloaded_users = user_load[user_load > 5]
            for user, count in overloaded_users.items():
                st.warning(f":material/warning: **Resource Load Alert**: {user} has {count} active tasks. Consider rebalancing work.")

    if not projects.empty:
        for _, project in projects.iterrows():
            try:
                deadline_date = datetime.strptime(project["deadline"], "%Y-%m-%d").date()
                days_left = (deadline_date - date.today()).days
                
                project_tasks = tasks[tasks["project_id"] == project["id"]]
                pending_tasks = len(project_tasks[project_tasks["status"] != "Completed"])
                
                if pending_tasks > 0 or days_left < 0:
                    if days_left < 0:
                        st.error(f":material/error: **{project['name']}** is OVERDUE by {abs(days_left)} days with {pending_tasks} pending tasks!")
                    elif days_left <= 3 and pending_tasks > 0:
                        st.warning(f":material/warning: **{project['name']}** is due very soon ({days_left} days left) and has {pending_tasks} pending tasks!")
                    else:
                        # Basic prediction insight
                        if pending_tasks > days_left * 2:
                            st.info(f":material/psychology: **Insight**: '{project['name']}' has a high volume of pending tasks ({pending_tasks}) compared to days left ({days_left}). Consider reassigning resources.")
            except Exception as e:
                pass

    st.divider()
    
    colC, colD = st.columns(2)
    with colC:
        st.subheader(":material/group: Tasks per User")
        if not tasks.empty:
            user_counts = tasks["assigned_to"].value_counts()
            st.bar_chart(user_counts)
            
    with colD:
        st.subheader(":material/trending_up: Project Progress")

        if not projects.empty and not tasks.empty:

            for project in projects["id"]:

                project_tasks = tasks[tasks["project_id"] == project]

                if len(project_tasks) > 0:

                    completed = len(project_tasks[project_tasks["status"] == "Completed"])
                    total = len(project_tasks)

                    progress = completed / total

                    project_name = projects[projects["id"] == project]["name"].values[0]

                    st.write(f"**{project_name}** - {progress*100:.1f}%")
                    st.progress(progress)

# ---------------- MY PROFILE ----------------

elif menu == "My Profile":
    st.header(":material/person: My Profile")
    
    st.subheader("Profile Details")
    st.write(f"**Name/Username:** {st.session_state.current_user}")
    st.write(f"**Role:** {st.session_state.role}")
    
    st.divider()
    st.subheader("Change Password")
    with st.form("change_password_form"):
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        submit_pwd = st.form_submit_button("Update Password")
        
        if submit_pwd:
            if not old_password or not new_password or not confirm_new_password:
                st.error("Please fill in all fields")
            elif new_password != confirm_new_password:
                st.error("New passwords do not match")
            else:
                hashed_old = hash_password(old_password)
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (st.session_state.current_user, hashed_old))
                if cursor.fetchone():
                    hashed_new = hash_password(new_password)
                    cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed_new, st.session_state.current_user))
                    conn.commit()
                    st.success("Password updated successfully!")
                else:
                    st.error("Incorrect current password")

# ---------------- ADD USER ----------------

elif menu == "Add User" and st.session_state.role == "Admin":

    st.header(":material/person_add: Add Team Member")

    name = st.text_input("Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    role = st.selectbox(
        "Role",
        ["Admin", "Manager", "Team Member"]
    )

    if st.button("Add User"):
        if not name.strip() or not username.strip() or not password:
            st.warning(":material/warning: Please fill in all fields")
        else:
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            if cursor.fetchone():
                st.error(":material/error: Username already exists")
            else:
                hashed_pwd = hash_password(password)
                cursor.execute(
                    "INSERT INTO users(name, username, password, role) VALUES (?,?,?,?)",
                    (name, username, hashed_pwd, role)
                )

                conn.commit()

                st.success("User added successfully")
                st.balloons()

# ---------------- CREATE PROJECT ----------------

elif menu == "Create Project" and st.session_state.role in ["Admin", "Manager"]:

    st.header(":material/create_new_folder: Create Project")

    name = st.text_input("Project Name")

    description = st.text_area("Project Description")

    deadline = st.date_input("Deadline")

    if st.button("Create Project"):
        if not name.strip():
            st.warning(":material/warning: Project Name cannot be empty")
        else:
            cursor.execute(
                "INSERT INTO projects(name, description, deadline) VALUES (?,?,?)",
                (name, description, deadline)
            )

            conn.commit()

            st.success("Project created successfully")
            st.balloons()

# ---------------- ADD TASK ----------------

elif menu == "Add Task":

    st.header(":material/add_task: Add Task")

    projects = pd.read_sql("SELECT * FROM projects", conn)
    if st.session_state.role == "Team Member":
        projects = pd.read_sql("""
            SELECT p.* FROM projects p 
            JOIN project_members pm ON p.id = pm.project_id 
            WHERE pm.username = ?
        """, conn, params=(st.session_state.username,))
    
    users = pd.read_sql("SELECT * FROM users", conn)

    if projects.empty:
        st.warning("Create a project first")

    elif users.empty:
        st.warning("Add users first")

    else:

        project = st.selectbox(
            "Project",
            projects["name"]
        )

        task = st.text_input("Task Name")

        assigned = st.selectbox(
            "Assign To",
            users["name"]
        )

        status = st.selectbox(
            "Status",
            ["Pending", "In Progress", "Completed"]
        )

        if st.button("Add Task"):
            if not task.strip():
                st.warning(":material/warning: Task Name cannot be empty")
            else:
                project_id = projects[projects["name"] == project]["id"].values[0]

                cursor.execute(
                    "INSERT INTO tasks(project_id, task_name, assigned_to, status) VALUES (?,?,?,?)",
                    (int(project_id), task, assigned, status)
                )

                conn.commit()

                st.success("Task added successfully")
                st.balloons()

# ---------------- MANAGE TASKS ----------------

elif menu == "Manage Tasks":

    st.header(":material/edit_document: Manage Tasks")

    projects = pd.read_sql("SELECT * FROM projects", conn)
    
    if st.session_state.role == "Team Member":
        projects = pd.read_sql("""
            SELECT p.* FROM projects p 
            JOIN project_members pm ON p.id = pm.project_id 
            WHERE pm.username = ?
        """, conn, params=(st.session_state.username,))

    if projects.empty:
        st.warning("No projects assigned/available")
    else:
        sel_project_id = st.selectbox(
            "Select Project",
            projects["id"].tolist(),
            format_func=lambda x: projects[projects["id"] == x]["name"].values[0],
            key="manage_tasks_proj"
        )
        
        tasks = pd.read_sql("SELECT * FROM tasks WHERE project_id=?", conn, params=(int(sel_project_id),))
        users = pd.read_sql("SELECT * FROM users", conn)

        if tasks.empty:
            st.info("No tasks for this project")
        else:
            task_id = st.selectbox(
                "Select Task",
                tasks["id"].tolist(),
                format_func=lambda x: tasks[tasks["id"] == x]["task_name"].values[0]
            )
        
        task_info = tasks[tasks["id"] == task_id].iloc[0]

        with st.form("edit_task_form"):
            new_task_name = st.text_input("Task Name", value=task_info["task_name"])
            
            assigned_index = users["name"].tolist().index(task_info["assigned_to"]) if task_info["assigned_to"] in users["name"].tolist() else 0
            new_assigned = st.selectbox("Assign To", users["name"], index=assigned_index)
            
            status_index = ["Pending", "In Progress", "Completed"].index(task_info["status"])
            new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], index=status_index)
            
            update_btn = st.form_submit_button("Update Task")

            if update_btn:
                if not new_task_name.strip():
                    st.warning(":material/warning: Task Name cannot be empty")
                else:
                    cursor.execute(
                        "UPDATE tasks SET task_name=?, assigned_to=?, status=? WHERE id=?",
                        (new_task_name, new_assigned, new_status, int(task_id))
                    )
                    conn.commit()
                    st.success("Task updated successfully")
                    st.rerun()

        st.divider()
        st.subheader(":material/delete_forever: Danger Zone")
        if st.session_state.role in ["Admin", "Manager"]:
            if st.button("Delete Task", type="primary"):
                cursor.execute("DELETE FROM tasks WHERE id=?", (int(task_id),))
                conn.commit()
                st.success("Task deleted successfully")
                st.rerun()

# ---------------- MANAGE PROJECTS ----------------

elif menu == "Manage Projects" and st.session_state.role in ["Admin", "Manager"]:

    st.header(":material/folder_managed: Manage Projects")

    projects = pd.read_sql("SELECT * FROM projects", conn)

    if projects.empty:
        st.warning("No projects available")
    else:
        project_id = st.selectbox(
            "Select Project", 
            projects["id"].tolist(),
            format_func=lambda x: projects[projects["id"] == x]["name"].values[0]
        )
        
        project_info = projects[projects["id"] == project_id].iloc[0]
        
        # Get current members
        cursor.execute("SELECT username FROM project_members WHERE project_id=?", (int(project_id),))
        current_members = [row[0] for row in cursor.fetchall()]
        
        # Get all team members for assignment
        all_team_members = pd.read_sql("SELECT name, username FROM users WHERE role='Team Member'", conn)
        member_options = all_team_members["username"].tolist()
        member_display = {row["username"]: row["name"] for _, row in all_team_members.iterrows()}
        
        with st.form("edit_project_form"):
            new_name = st.text_input("Project Name", value=project_info["name"])
            new_desc = st.text_area("Project Description", value=project_info["description"])
            
            # Member assignment
            selected_members = st.multiselect(
                "Assign Team Members",
                options=member_options,
                default=[m for m in current_members if m in member_options],
                format_func=lambda x: f"{member_display[x]} ({x})"
            )
            
            try:
                current_deadline = datetime.strptime(project_info["deadline"], "%Y-%m-%d").date()
            except:
                current_deadline = date.today()
                
            new_deadline = st.date_input("Deadline", value=current_deadline)
            
            update_proj_btn = st.form_submit_button("Update Project")
            
            if update_proj_btn:
                if not new_name.strip():
                    st.warning(":material/warning: Project Name cannot be empty")
                else:
                    cursor.execute(
                        "UPDATE projects SET name=?, description=?, deadline=? WHERE id=?",
                        (new_name, new_desc, new_deadline, int(project_id))
                    )
                    
                    # Update project members
                    cursor.execute("DELETE FROM project_members WHERE project_id=?", (int(project_id),))
                    for m_username in selected_members:
                        cursor.execute("INSERT INTO project_members(project_id, username) VALUES (?,?)", (int(project_id), m_username))
                    
                    conn.commit()
                    st.success("Project updated successfully")
                    st.rerun()
        
        st.divider()
        st.subheader(":material/delete_forever: Danger Zone")
        st.warning(f"Are you sure you want to delete this project? This will also delete all associated tasks.")
        
        if st.button("Delete Project", type="primary"):
            # Delete tasks first
            cursor.execute("DELETE FROM tasks WHERE project_id=?", (int(project_id),))
            # Delete project
            cursor.execute("DELETE FROM projects WHERE id=?", (int(project_id),))
            
            conn.commit()
            st.success("Project deleted successfully")
            st.rerun()

# ---------------- Task Board ----------------

elif menu == "Task Board":
    st.header(":material/view_kanban: Task Board")
    
    projects = pd.read_sql("SELECT * FROM projects", conn)
    if st.session_state.role == "Team Member":
        projects = pd.read_sql("""
            SELECT p.* FROM projects p 
            JOIN project_members pm ON p.id = pm.project_id 
            WHERE pm.username = ?
        """, conn, params=(st.session_state.username,))
    
    tasks = pd.read_sql("SELECT * FROM tasks", conn)
    
    if projects.empty:
        st.warning("No projects available")
    else:
        project_id = st.selectbox(
            "Select Project", 
            projects["id"].tolist(),
            format_func=lambda x: projects[projects["id"] == x]["name"].values[0]
        )
        
        project_tasks = tasks[tasks["project_id"] == project_id]
        
        if project_tasks.empty:
            st.info("No tasks for this project yet")
        else:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader(":material/schedule: Pending")
                pending = project_tasks[project_tasks["status"] == "Pending"]
                for _, task in pending.iterrows():
                    with st.container():
                        st.markdown(f"**{task['task_name']}**")
                        st.caption(f":material/person: {task['assigned_to']}")
                        st.divider()
                        
            with col2:
                st.subheader(":material/hourglass_empty: In Progress")
                in_progress = project_tasks[project_tasks["status"] == "In Progress"]
                for _, task in in_progress.iterrows():
                    with st.container():
                        st.markdown(f"**{task['task_name']}**")
                        st.caption(f":material/person: {task['assigned_to']}")
                        st.divider()
                        
            with col3:
                st.subheader(":material/check_circle: Completed")
                completed = project_tasks[project_tasks["status"] == "Completed"]
                for _, task in completed.iterrows():
                    with st.container():
                        st.markdown(f"**{task['task_name']}**")
                        st.caption(f":material/person: {task['assigned_to']}")
                        st.divider()