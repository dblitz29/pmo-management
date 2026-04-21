from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
DB = 'projects.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Only create if not exists
    if os.path.exists(DB):
        return
    
    conn = get_db()
    
    # Users table
    conn.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'viewer',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Default admin user only
    conn.execute('INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)',
        ('admin', hash_password('admin123'), 'Administrator', 'admin'))
    
    # Projects table (empty)
    conn.execute('''CREATE TABLE projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cust_name TEXT NOT NULL,
        pmo TEXT,
        rm_ticket TEXT,
        complete_date TEXT,
        project_tier TEXT,
        project_name TEXT NOT NULL,
        tech_point INTEGER DEFAULT 0,
        cust_point INTEGER DEFAULT 0,
        time_point INTEGER DEFAULT 0,
        total_cust INTEGER DEFAULT 0,
        avg_bar INTEGER DEFAULT 0,
        engineer1 TEXT,
        engineer2 TEXT,
        link TEXT
    )''')
    
    conn.commit()
    conn.close()
    print("Database initialized (empty projects, default admin user)")

# Auth decorators
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            if request.is_json:
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and user['password'] == hash_password(password):
            session['user'] = username
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            return jsonify({'status': 'ok', 'role': session['role'], 'name': session['name']})
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/me')
@login_required
def get_me():
    return jsonify({'user': session['user'], 'role': session['role'], 'name': session['name']})

# Page routes
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@app.route('/form')
@login_required
def form_page():
    return render_template('form.html')

@app.route('/users')
@login_required
def users_page():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('users.html')

# User management API (admin only)
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    conn = get_db()
    rows = conn.execute('SELECT id, username, name, role, created_at FROM users ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/users', methods=['POST'])
@admin_required
def add_user():
    d = request.json
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)',
            (d['username'], hash_password(d['password']), d['name'], d['role']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Username already exists'}), 400

@app.route('/api/users/<int:id>', methods=['PUT'])
@admin_required
def update_user(id):
    d = request.json
    conn = get_db()
    
    # Check if trying to demote last admin
    if d['role'] != 'admin':
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND id != ?", (id,)).fetchone()[0]
        if admin_count == 0:
            conn.close()
            return jsonify({'error': 'Cannot demote the last admin'}), 400
    
    if d.get('password'):
        conn.execute('UPDATE users SET username=?, password=?, name=?, role=? WHERE id=?',
            (d['username'], hash_password(d['password']), d['name'], d['role'], id))
    else:
        conn.execute('UPDATE users SET username=?, name=?, role=? WHERE id=?',
            (d['username'], d['name'], d['role'], id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    conn = get_db()
    
    # Prevent deleting yourself
    if id == session.get('user_id'):
        conn.close()
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    # Prevent deleting last admin
    user = conn.execute('SELECT role FROM users WHERE id=?', (id,)).fetchone()
    if user and user['role'] == 'admin':
        admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
        if admin_count <= 1:
            conn.close()
            return jsonify({'error': 'Cannot delete the last admin'}), 400
    
    conn.execute('DELETE FROM users WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

# API routes - Read (all users)
@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    conn = get_db()
    rows = conn.execute('SELECT * FROM projects ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/stats')
@login_required
def get_stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM projects WHERE pmo='Completed'").fetchone()[0]
    cancelled = conn.execute("SELECT COUNT(*) FROM projects WHERE pmo='Cancelled'").fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM projects WHERE pmo='In Progress'").fetchone()[0]
    avg = conn.execute('SELECT AVG(total_cust) FROM projects').fetchone()[0] or 0
    conn.close()
    return jsonify({'total': total, 'completed': completed, 'cancelled': cancelled, 'in_progress': in_progress, 'avg': round(avg)})

@app.route('/api/chart/engineers')
@login_required
def chart_engineers():
    conn = get_db()
    rows = conn.execute("SELECT engineer1, COUNT(*) as count FROM projects WHERE engineer1 != '' GROUP BY engineer1").fetchall()
    conn.close()
    return jsonify([{'name': r['engineer1'], 'count': r['count']} for r in rows])

@app.route('/api/chart/customers')
@login_required
def chart_customers():
    conn = get_db()
    rows = conn.execute("SELECT cust_name, COUNT(*) as count FROM projects GROUP BY cust_name ORDER BY count DESC LIMIT 5").fetchall()
    conn.close()
    return jsonify([{'name': r['cust_name'], 'count': r['count']} for r in rows])

# API routes - Write (admin only)
@app.route('/api/projects', methods=['POST'])
@admin_required
def add_project():
    d = request.json
    conn = get_db()
    conn.execute('''INSERT INTO projects (cust_name, pmo, rm_ticket, complete_date, project_tier, project_name, tech_point, cust_point, time_point, total_cust, avg_bar, engineer1, engineer2, link) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['cust_name'], d['pmo'], d['rm_ticket'], d['complete_date'], d['project_tier'], d['project_name'], 
         int(d['tech_point'] or 0), int(d['cust_point'] or 0), int(d['time_point'] or 0), int(d['total_cust'] or 0), int(d['avg_bar'] or 0), 
         d['engineer1'], d['engineer2'], d['link']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/projects/<int:id>', methods=['PUT'])
@admin_required
def update_project(id):
    d = request.json
    conn = get_db()
    conn.execute('''UPDATE projects SET cust_name=?, pmo=?, rm_ticket=?, complete_date=?, project_tier=?, project_name=?, 
        tech_point=?, cust_point=?, time_point=?, total_cust=?, avg_bar=?, engineer1=?, engineer2=?, link=? WHERE id=?''',
        (d['cust_name'], d['pmo'], d['rm_ticket'], d['complete_date'], d['project_tier'], d['project_name'],
         int(d['tech_point'] or 0), int(d['cust_point'] or 0), int(d['time_point'] or 0), int(d['total_cust'] or 0), int(d['avg_bar'] or 0),
         d['engineer1'], d['engineer2'], d['link'], id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

@app.route('/api/projects/<int:id>', methods=['DELETE'])
@admin_required
def delete_project(id):
    conn = get_db()
    conn.execute('DELETE FROM projects WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
