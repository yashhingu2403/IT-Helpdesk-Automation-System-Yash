from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from threading import Thread
import smtplib

app = Flask(__name__)
app.secret_key = 'supersecretkey'

DATABASE = 'it_helpdesk.db'

# Initialize database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Route for home page
@app.route('/')
def index():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    return render_template('index.html', tickets=tickets)

# Route to create a new support ticket
@app.route('/new_ticket', methods=('GET', 'POST'))
def new_ticket():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        issue = request.form['issue']

        if not name or not email or not issue:
            flash('All fields are required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO tickets (name, email, issue, status) VALUES (?, ?, ?, ?)',
                         (name, email, issue, 'Open'))
            conn.commit()
            conn.close()

            # Send email confirmation in a new thread
            Thread(target=send_email, args=(email, issue)).start()
            flash('Ticket created successfully!')
            return redirect(url_for('index'))

    return render_template('new_ticket.html')

# Route to update ticket status
@app.route('/update_ticket/<int:ticket_id>', methods=('GET', 'POST'))
def update_ticket(ticket_id):
    conn = get_db_connection()
    ticket = conn.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,)).fetchone()

    if request.method == 'POST':
        status = request.form['status']
        conn.execute('UPDATE tickets SET status = ? WHERE id = ?', (status, ticket_id))
        conn.commit()
        conn.close()
        flash('Ticket updated successfully!')
        return redirect(url_for('index'))

    conn.close()
    return render_template('update_ticket.html', ticket=ticket)

# Email notification function
def send_email(email, issue):
    with smtplib.SMTP('smtp.mailtrap.io', 2525) as server:
        server.login('username', 'password')
        message = f"Subject: IT Support Ticket\n\nYour ticket '{issue}' has been created."
        server.sendmail('support@yourcompany.com', email, message)

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            issue TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
