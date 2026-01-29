import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/applications.db")

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


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


def calculate_response_time(date_applied, last_updated):
    applied_date = datetime.strptime(date_applied, "%Y-%m-%d")
    updated_date = datetime.strptime(last_updated, "%Y-%m-%d")

    response_days = (updated_date - applied_date).days
    return response_days

update_application_status(
    application_id=1,
    new_status="Interview",
    update_date="2024-06-10"
)

def calculate_average_response_time(applications):
    total_days = 0
    count = 0

    for app in applications:
        date_applied = app[5]
        last_updated = app[7]

        response_time = calculate_response_time(date_applied, last_updated)
        total_days += response_time
        count += 1

    if count == 0:
        return 0

    return total_days / count

def response_time_by_source(applications):
    source_data = {}

    for app in applications:
        source = app[4]
        date_applied = app[5]
        last_updated = app[7]

        response_time = calculate_response_time(date_applied, last_updated)

        if source not in source_data:
            source_data[source] = []

        source_data[source].append(response_time)

    return source_data

def find_stale_applications(applications, threshold_days=7):
    stale_apps = []

    for app in applications:
        status = app[6]
        date_applied = app[5]
        last_updated = app[7]

        response_time = calculate_response_time(date_applied, last_updated)

        if status == "Applied" and response_time > threshold_days:
            stale_apps.append({
                "company": app[1],
                "role": app[2],
                "days_waiting": response_time
            })

    return stale_apps


if __name__ == "__main__":
    create_tables()

    applications = get_all_applications()

    average_time = calculate_average_response_time(applications)
    print(f"\nAverage Response Time: {average_time:.2f} days\n")

    source_stats = response_time_by_source(applications)
    print("Response Time by Source:")
    for source, times in source_stats.items():
        avg = sum(times) / len(times)
        print(f"{source}: {avg:.2f} days")

    print("\nApplications:")
    for app in applications:
        company = app[1]
        role = app[2]
        status = app[6]
        response_time = calculate_response_time(app[5], app[7])

        print(f"{company} | {role} | Status: {status} | Response Time: {response_time} days")
    
    stale_apps = find_stale_applications(applications, threshold_days=7)

    print("\nStale Applications (Follow-up Recommended):")
    if not stale_apps:
        print("No stale applications 🎉")
    else:
        for app in stale_apps:
            print(
                f"{app['company']} | {app['role']} | Waiting {app['days_waiting']} days"
            )
