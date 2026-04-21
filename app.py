from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
import hashlib
import json
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

DATA_FILE = 'data.json'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    # Default data
    return {
        'users': [
            {'id': 1, 'username': 'admin', 'password': hash_password('admin123'), 'name': 'Administrator', 'role': 'admin'}
        ],
        'projects': []
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_next_id(items):
    return max([i['id'] for i in items], default=0) + 1

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
        
        db = load_data()
        user = next((u for u in db['users'] if u['username'] == username), None)
        
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

# User API
@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    db = load_data()
    users = [{'id': u['id'], 'username': u['username'], 'name': u['name'], 'role': u['role']} for u in db['users']]
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
@admin_required
def add_user():
    d = request.json
    db = load_data()
    
    if any(u['username'] == d['username'] for u in db['users']):
        return jsonify({'error': 'Username already exists'}), 400
    
    new_user = {
        'id': get_next_id(db['users']),
        'username': d['username'],
        'password': hash_password(d['password']),
        'name': d['name'],
        'role': d['role']
    }
    db['users'].append(new_user)
    save_data(db)
    return jsonify({'status': 'ok'})

@app.route('/api/users/<int:id>', methods=['PUT'])
@admin_required
def update_user(id):
    d = request.json
    db = load_data()
    user = next((u for u in db['users'] if u['id'] == id), None)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if d['role'] != 'admin':
        admin_count = sum(1 for u in db['users'] if u['role'] == 'admin' and u['id'] != id)
        if admin_count == 0:
            return jsonify({'error': 'Cannot demote the last admin'}), 400
    
    user['username'] = d['username']
    user['name'] = d['name']
    user['role'] = d['role']
    if d.get('password'):
        user['password'] = hash_password(d['password'])
    
    save_data(db)
    return jsonify({'status': 'ok'})

@app.route('/api/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    db = load_data()
    
    if id == session.get('user_id'):
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = next((u for u in db['users'] if u['id'] == id), None)
    if user and user['role'] == 'admin':
        admin_count = sum(1 for u in db['users'] if u['role'] == 'admin')
        if admin_count <= 1:
            return jsonify({'error': 'Cannot delete the last admin'}), 400
    
    db['users'] = [u for u in db['users'] if u['id'] != id]
    save_data(db)
    return jsonify({'status': 'ok'})

# Project API
@app.route('/api/projects', methods=['GET'])
@login_required
def get_projects():
    db = load_data()
    return jsonify(db['projects'])

@app.route('/api/projects', methods=['POST'])
@admin_required
def add_project():
    d = request.json
    db = load_data()
    
    new_project = {
        'id': get_next_id(db['projects']),
        'cust_name': d['cust_name'],
        'pmo': d['pmo'],
        'rm_ticket': d.get('rm_ticket', ''),
        'complete_date': d.get('complete_date', ''),
        'project_tier': d.get('project_tier', '☆☆☆☆☆'),
        'project_name': d['project_name'],
        'tech_point': int(d.get('tech_point') or 0),
        'cust_point': int(d.get('cust_point') or 0),
        'time_point': int(d.get('time_point') or 0),
        'total_cust': int(d.get('total_cust') or 0),
        'avg_bar': int(d.get('avg_bar') or 0),
        'engineer1': d.get('engineer1', ''),
        'engineer2': d.get('engineer2', ''),
        'link': d.get('link', '')
    }
    db['projects'].append(new_project)
    save_data(db)
    return jsonify({'status': 'ok'})

@app.route('/api/projects/<int:id>', methods=['PUT'])
@admin_required
def update_project(id):
    d = request.json
    db = load_data()
    project = next((p for p in db['projects'] if p['id'] == id), None)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    project.update({
        'cust_name': d['cust_name'],
        'pmo': d['pmo'],
        'rm_ticket': d.get('rm_ticket', ''),
        'complete_date': d.get('complete_date', ''),
        'project_tier': d.get('project_tier', '☆☆☆☆☆'),
        'project_name': d['project_name'],
        'tech_point': int(d.get('tech_point') or 0),
        'cust_point': int(d.get('cust_point') or 0),
        'time_point': int(d.get('time_point') or 0),
        'total_cust': int(d.get('total_cust') or 0),
        'avg_bar': int(d.get('avg_bar') or 0),
        'engineer1': d.get('engineer1', ''),
        'engineer2': d.get('engineer2', ''),
        'link': d.get('link', '')
    })
    save_data(db)
    return jsonify({'status': 'ok'})

@app.route('/api/projects/<int:id>', methods=['DELETE'])
@admin_required
def delete_project(id):
    db = load_data()
    db['projects'] = [p for p in db['projects'] if p['id'] != id]
    save_data(db)
    return jsonify({'status': 'ok'})

@app.route('/api/stats')
@login_required
def get_stats():
    db = load_data()
    projects = db['projects']
    total = len(projects)
    completed = sum(1 for p in projects if p['pmo'] == 'Completed')
    cancelled = sum(1 for p in projects if p['pmo'] == 'Cancelled')
    in_progress = sum(1 for p in projects if p['pmo'] == 'In Progress')
    avg = sum(p['total_cust'] for p in projects) / total if total > 0 else 0
    return jsonify({'total': total, 'completed': completed, 'cancelled': cancelled, 'in_progress': in_progress, 'avg': round(avg)})

@app.route('/api/chart/engineers')
@login_required
def chart_engineers():
    db = load_data()
    engineers = {}
    for p in db['projects']:
        if p.get('engineer1'):
            engineers[p['engineer1']] = engineers.get(p['engineer1'], 0) + 1
    return jsonify([{'name': k, 'count': v} for k, v in engineers.items()])

@app.route('/api/chart/customers')
@login_required
def chart_customers():
    db = load_data()
    customers = {}
    for p in db['projects']:
        customers[p['cust_name']] = customers.get(p['cust_name'], 0) + 1
    sorted_customers = sorted(customers.items(), key=lambda x: x[1], reverse=True)[:5]
    return jsonify([{'name': k, 'count': v} for k, v in sorted_customers])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
