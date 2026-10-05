# Gym Manager — Python + MySQL

A Windows desktop project for gym membership management using Tkinter and MySQL. Prices are in INR. The desktop connects directly to MySQL; running the optional API is not required.

## Features

- Add, search and edit members; select rows to copy IDs.
- Create fixed-day membership plans and activate memberships.
- Renew from the day after the latest membership, or today when expired.
- Record partial or advance offline payments with duplicate receipt protection.
- Show active, upcoming and expired memberships, fees and balances.
- Record one attendance entry per member per day with an active membership.
- Dashboard: member count, unique active members, receipts total, pending balances and today's attendance.
- Export membership, payment and attendance reports to CSV; save individual text receipts.
- Optional authenticated JSON API and original local MCP tools.

## Update your existing installation

1. Stop the desktop and backend. Keep a backup of your current project folder and database.
2. Extract this ZIP into a **new folder**. Copy your existing `.env` into its `gym-manager` folder locally. Never upload `.env`.
3. In MySQL Workbench, open `sql/upgrade.sql` and execute it against your existing database. It only creates the attendance table; it does not delete existing members or payments. If you use a database name other than `gym_manager`, change the `USE` line first. The existing SELECT/INSERT/UPDATE grant on `gym_manager.*` covers the new table.
4. Open a PowerShell terminal in the new `gym-manager` folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m gym.desktop
```

You can also double-click `start-desktop.bat` after setup.

## Fresh installation

Install Python 3.11+ with Tkinter and MySQL 8+. Create the virtual environment and install requirements as above. Execute `sql/schema.sql` in MySQL Workbench. Create an application database user:

```sql
CREATE USER 'gym_app'@'localhost' IDENTIFIED BY 'CHOOSE_YOUR_PASSWORD';
GRANT SELECT, INSERT, UPDATE ON gym_manager.* TO 'gym_app'@'localhost';
```

Copy `.env.example` to `.env` and set your database details locally. Launch `python -m gym.desktop` with your virtual environment activated. Existing test members remain ordinary records; adding real members does not replace them.

## Daily workflow

1. Add a member in Members, or search and select an existing one.
2. Create/select a plan in Plans.
3. In Memberships & Payments, activate with a start date. Renew uses the latest expiry automatically and ignores the start-date field.
4. Record money actually received using a unique receipt reference. Refresh memberships to see the balance.
5. Load payments in Receipts and save a selected receipt.
6. Select a member and use Attendance to check in today.
7. Refresh Dashboard, Reports and Expiry as needed. Lists refresh on button clicks.

Dates use YYYY-MM-DD. End dates are inclusive. A 30-day plan starting January 1 ends January 30. Attendance and dashboard dates use the computer's local date. Search returns the latest 100 matching members; reports include all memberships. Negative balances indicate advance payments; pending totals sum positive balances per membership. Overlapping memberships are permitted. Renewal should be submitted once and is designed for a single desktop operator.

## Optional API

Set a random `GYM_API_KEY` of at least 32 characters in `.env`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -m gym.api
```

API listens on 127.0.0.1:8000. It exposes the original eight tools through authenticated POST /tools/<tool_name> requests with a JSON body and Authorization: Bearer <key>. New desktop features use the service directly. The API has no browser dashboard. `run_mcp.py` is the original local stdio MCP entry point.

## Validation

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python tests/check_mcp.py
```

Service tests use a SQLite adapter, including renewal, attendance duplication, inactive-member rejection, balances, receipts and dashboard totals. They do not verify actual MySQL locking or credentials. Run the manual checklist in `CHECKLIST.md` on your Windows/MySQL installation before daily use.

## Project layout

- gym/desktop.py — desktop interface
- gym/service.py — validation and SQL workflows
- gym/db.py — environment-based MySQL connection
- sql/schema.sql — fresh database setup
- sql/upgrade.sql — additive attendance upgrade
- tests/ — workflow tests and MCP check
- GITHUB.md — upload instructions

## Scope

This is a local desktop project for a single operator. Payments record offline money received; they do not charge UPI or cards. Refunds, deletion, staff login, online hosting and automatic database backups are not implemented. Protect the computer account and back up MySQL separately. Do not publish exported member reports or receipts.
