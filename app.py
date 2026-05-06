from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key' # For session security

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Database setup
with get_db() as db:
    db.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
    db.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY, amount REAL, type TEXT, 
                    creator_id INTEGER, collab_id INTEGER, 
                    status TEXT DEFAULT 'pending')''')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pw = generate_password_hash(request.form['password'])
        try:
            db = get_db()
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw))
            db.commit()
            return redirect('/login')
        except:
            flash("Username taken!")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (request.form['username'],)).fetchone()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/dashboard')
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    db = get_db()
    # Transactions created by me OR waiting for me
    txs = db.execute("""
        SELECT t.*, u.username as creator_name 
        FROM transactions t JOIN users u ON t.creator_id = u.id 
        WHERE t.collab_id = ? OR t.creator_id = ?""", (session['user_id'], session['user_id'])).fetchall()
    return render_template('dashboard.html', transactions=txs)

@app.route('/approve/<int:tx_id>')
def approve(tx_id):
    db = get_db()
    db.execute("UPDATE transactions SET status = 'approved' WHERE id = ? AND collab_id = ?", (tx_id, session['user_id']))
    db.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
