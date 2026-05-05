import sqlite3
from pathlib import Path
from datetime import datetime
from transformers import pipeline

DB_PATH = Path("data/applications.db")

#  AI MODEL 
generator = pipeline("text-generation", model="google/flan-t5-small")

#  DB CONNECTION 
def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

#  CREATE TABLE 
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            source TEXT,
            date_applied TEXT NOT NULL,
            status TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_application(company, role, location, source, date_applied, status, notes=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications
        (company, role, location, source, date_applied, status, last_updated, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company,
        role,
        location,
        source,
        date_applied,
        status,
        date_applied,
        notes
    ))

    conn.commit()
    conn.close()

 
def get_all_applications():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM applications")
    rows = cursor.fetchall()

    conn.close()
    return rows

# UPDATE STATUS 
def update_application_status(application_id, new_status, update_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE applications
        SET status = ?, last_updated = ?
        WHERE id = ?
    """, (
        new_status,
        update_date,
        application_id
    ))

    conn.commit()
    conn.close()

# RESPONSE TIME 
def calculate_response_time(date_applied, last_updated):
    applied_date = datetime.strptime(date_applied, "%Y-%m-%d")
    updated_date = datetime.strptime(last_updated, "%Y-%m-%d")

    return (updated_date - applied_date).days

#  AVG RESPONSE TIME
def calculate_average_response_time(applications):
    total_days = 0
    count = 0

    for app in applications:
        response_time = calculate_response_time(app[5], app[7])
        total_days += response_time
        count += 1

    return total_days / count if count else 0

#  SOURCE ANALYSIS 
def response_time_by_source(applications):
    source_data = {}

    for app in applications:
        source = app[4]
        response_time = calculate_response_time(app[5], app[7])

        if source not in source_data:
            source_data[source] = []

        source_data[source].append(response_time)

    return source_data

# STALE APPLICATIONS 
def find_stale_applications(applications, threshold_days=7):
    stale_apps = []

    for app in applications:
        status = app[6]
        response_time = calculate_response_time(app[5], app[7])

        if status == "Applied" and response_time > threshold_days:
            stale_apps.append({
                "company": app[1],
                "role": app[2],
                "days_waiting": response_time
            })

    return stale_apps

#  AI: PREPARE TEXT
def prepare_text_for_ai(applications):
    if not applications:
        return "No job applications available."

    text = ""
    for app in applications:
        text += f"{app[2]} at {app[1]} from {app[4]} - status {app[6]}. "

    return text

def generate_ai_insights(applications):
    text_data = prepare_text_for_ai(applications)

    prompt = f"Analyze the following job application data and give key insights:\n{text_data}"

    result = generator(prompt, max_length=150, do_sample=False)

    return result[0]["generated_text"]

#  MAIN 
if __name__ == "__main__":
    create_tables()

    applications = get_all_applications()

    # Average response time
    avg_time = calculate_average_response_time(applications)
    print(f"\nAverage Response Time: {avg_time:.2f} days\n")

    # Source analysis
    print("Response Time by Source:")
    source_stats = response_time_by_source(applications)
    for source, times in source_stats.items():
        avg = sum(times) / len(times)
        print(f"{source}: {avg:.2f} days")

    # Application details
    print("\nApplications:")
    for app in applications:
        response_time = calculate_response_time(app[5], app[7])
        print(f"{app[1]} | {app[2]} | Status: {app[6]} | Response Time: {response_time} days")

    # Stale applications
    stale_apps = find_stale_applications(applications)
    print("\nStale Applications:")
    if not stale_apps:
        print("No stale applications 🎉")
    else:
        for app in stale_apps:
            print(f"{app['company']} | {app['role']} | Waiting {app['days_waiting']} days")

    # AI INSIGHTS
    insights = generate_ai_insights(applications)

    print("\nAI Insights:")
    print(insights)