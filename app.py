import os
import pymysql
import pymysql.cursors
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'campushireportal_secret_2024')

@app.template_filter('dateformat')
def dateformat(value, format='%d-%m-%Y'):
    if value is None:
        return '—'
    if isinstance(value, str):
        return value[:10]
    return value.strftime(format)

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%Y %H:%M'):
    if value is None:
        return '—'
    if isinstance(value, str):
        return value[:16]
    return value.strftime(format)

DB_CONFIG = {
    'host':     os.environ.get('MYSQL_HOST',     'localhost'),
    'port':     int(os.environ.get('MYSQL_PORT', 3306)),
    'user':     os.environ.get('MYSQL_USER',     'root'),
    'password': os.environ.get('MYSQL_PASSWORD', 'Manager'),
    'database': os.environ.get('MYSQL_DATABASE', 'campushire'),
    'charset':  'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': False,
}


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = pymysql.connect(**DB_CONFIG)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    query = query.replace('?', '%s')
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, args)
        rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    query = query.replace('?', '%s')
    db = get_db()
    with db.cursor() as cur:
        cur.execute(query, args)
        db.commit()
        return cur.lastrowid


def init_db():
    """Create all tables if they don't exist and seed the default officer account."""
    cfg = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
    db = pymysql.connect(**cfg)
    with db.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cur.execute(f"USE `{DB_CONFIG['database']}`")

        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                name        VARCHAR(255) NOT NULL,
                email       VARCHAR(255) UNIQUE NOT NULL,
                password    VARCHAR(512) NOT NULL,
                role        ENUM('student','officer','company') NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS students (
                id               INT PRIMARY KEY AUTO_INCREMENT,
                user_id          INT NOT NULL UNIQUE,
                roll_number      VARCHAR(50) UNIQUE NOT NULL,
                department       VARCHAR(100) NOT NULL,
                cgpa             DECIMAL(4,2) DEFAULT 0.00,
                year_of_passing  INT,
                phone            VARCHAR(20),
                resume_url       VARCHAR(500),
                skills           TEXT,
                backlogs         INT DEFAULT 0,
                gender           VARCHAR(20),
                date_of_birth    DATE,
                address          TEXT,
                is_placed        TINYINT(1) DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS companies (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                user_id     INT UNIQUE,
                name        VARCHAR(255) NOT NULL,
                industry    VARCHAR(100),
                website     VARCHAR(500),
                description TEXT,
                hr_name     VARCHAR(255),
                hr_phone    VARCHAR(20),
                hr_email    VARCHAR(255),
                address     TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id                   INT PRIMARY KEY AUTO_INCREMENT,
                company_id           INT NOT NULL,
                title                VARCHAR(255) NOT NULL,
                description          TEXT,
                requirements         TEXT,
                salary_min           DECIMAL(10,2),
                salary_max           DECIMAL(10,2),
                job_type             ENUM('full-time','part-time','internship','contract') DEFAULT 'full-time',
                location             VARCHAR(255),
                min_cgpa             DECIMAL(4,2) DEFAULT 0.00,
                allowed_backlogs     INT DEFAULT 0,
                allowed_departments  TEXT,
                deadline             DATE,
                status               ENUM('open','closed') DEFAULT 'open',
                created_at           DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS applications (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                student_id  INT NOT NULL,
                job_id      INT NOT NULL,
                status      ENUM('applied','shortlisted','interview_scheduled','selected','rejected') DEFAULT 'applied',
                applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                remarks     TEXT,
                UNIQUE KEY uq_student_job (student_id, job_id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (job_id)     REFERENCES jobs(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS interviews (
                id               INT PRIMARY KEY AUTO_INCREMENT,
                application_id   INT NOT NULL UNIQUE,
                interview_date   DATE NOT NULL,
                interview_time   TIME NOT NULL,
                interview_type   ENUM('in-person','online','telephonic','panel') DEFAULT 'in-person',
                venue            VARCHAR(500),
                interview_link   VARCHAR(500),
                round_number     INT DEFAULT 1,
                notes            TEXT,
                result           ENUM('pending','pass','fail') DEFAULT 'pending',
                created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS placements (
                id               INT PRIMARY KEY AUTO_INCREMENT,
                student_id       INT NOT NULL,
                company_id       INT NOT NULL,
                job_id           INT NOT NULL,
                offer_date       DATE,
                joining_date     DATE,
                package          DECIMAL(10,2),
                offer_letter_url VARCHAR(500),
                created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (company_id) REFERENCES companies(id),
                FOREIGN KEY (job_id)     REFERENCES jobs(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS announcements (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                title       VARCHAR(500) NOT NULL,
                content     TEXT NOT NULL,
                created_by  INT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """,
        ]

        for sql in tables:
            cur.execute(sql)

        cur.execute("SELECT COUNT(*) as cnt FROM users")
        if cur.fetchone()['cnt'] == 0:
            hashed = generate_password_hash('admin123')
            cur.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ('Placement Officer', 'officer@campus.edu', hashed, 'officer')
            )
        db.commit()
    db.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE email = ?', [email], one=True)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'student':
                student = query_db('SELECT * FROM students WHERE user_id = ?', [user['id']], one=True)
                if student:
                    session['student_id'] = student['id']
            elif user['role'] == 'company':
                company = query_db('SELECT * FROM companies WHERE user_id = ?', [user['id']], one=True)
                if company:
                    session['company_id'] = company['id']
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        existing = query_db('SELECT id FROM users WHERE email = ?', [email], one=True)
        if existing:
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        hashed = generate_password_hash(password)
        user_id = execute_db(
            'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
            (name, email, hashed, role)
        )
        if role == 'student':
            roll = request.form.get('roll_number', '')
            dept = request.form.get('department', '')
            execute_db('INSERT INTO students (user_id, roll_number, department) VALUES (?, ?, ?)',
                       (user_id, roll, dept))
        elif role == 'company':
            company_name = request.form.get('company_name', name)
            execute_db('INSERT INTO companies (user_id, name, hr_email) VALUES (?, ?, ?)',
                       (user_id, company_name, email))
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    data = {}

    if role == 'officer':
        data['total_students'] = query_db('SELECT COUNT(*) as c FROM students', one=True)['c']
        data['placed_students'] = query_db('SELECT COUNT(*) as c FROM students WHERE is_placed=1', one=True)['c']
        data['total_companies'] = query_db('SELECT COUNT(*) as c FROM companies', one=True)['c']
        data['open_jobs'] = query_db("SELECT COUNT(*) as c FROM jobs WHERE status='open'", one=True)['c']
        data['total_applications'] = query_db('SELECT COUNT(*) as c FROM applications', one=True)['c']
        data['scheduled_interviews'] = query_db("SELECT COUNT(*) as c FROM interviews WHERE result='pending'", one=True)['c']
        data['recent_applications'] = query_db('''
            SELECT a.id, s.roll_number, u.name as student_name, j.title, c.name as company_name, a.status, a.applied_at
            FROM applications a
            JOIN students s ON a.student_id=s.id
            JOIN users u ON s.user_id=u.id
            JOIN jobs j ON a.job_id=j.id
            JOIN companies c ON j.company_id=c.id
            ORDER BY a.applied_at DESC LIMIT 5
        ''')
        data['recent_placements'] = query_db('''
            SELECT p.*, u.name as student_name, c.name as company_name, j.title
            FROM placements p
            JOIN students s ON p.student_id=s.id
            JOIN users u ON s.user_id=u.id
            JOIN companies c ON p.company_id=c.id
            JOIN jobs j ON p.job_id=j.id
            ORDER BY p.created_at DESC LIMIT 5
        ''')
        data['dept_stats'] = query_db('''
            SELECT department, COUNT(*) as total, SUM(is_placed) as placed
            FROM students GROUP BY department
        ''')
        data['announcements'] = query_db('SELECT * FROM announcements ORDER BY created_at DESC LIMIT 3')

    elif role == 'student':
        sid = session.get('student_id')
        if sid:
            data['student'] = query_db(
                'SELECT s.*, u.name, u.email FROM students s JOIN users u ON s.user_id=u.id WHERE s.id=?',
                [sid], one=True)
            data['my_applications'] = query_db('''
                SELECT a.*, j.title, c.name as company_name, j.location, j.salary_max
                FROM applications a
                JOIN jobs j ON a.job_id=j.id
                JOIN companies c ON j.company_id=c.id
                WHERE a.student_id=? ORDER BY a.applied_at DESC LIMIT 5
            ''', [sid])
            data['open_jobs_count'] = query_db("SELECT COUNT(*) as c FROM jobs WHERE status='open'", one=True)['c']
            data['applied_count'] = query_db('SELECT COUNT(*) as c FROM applications WHERE student_id=?', [sid], one=True)['c']
            data['shortlisted_count'] = query_db(
                "SELECT COUNT(*) as c FROM applications WHERE student_id=? AND status='shortlisted'", [sid], one=True)['c']
            data['interviews'] = query_db('''
                SELECT i.*, j.title, c.name as company_name
                FROM interviews i
                JOIN applications a ON i.application_id=a.id
                JOIN jobs j ON a.job_id=j.id
                JOIN companies c ON j.company_id=c.id
                WHERE a.student_id=? AND i.result='pending'
                ORDER BY i.interview_date
            ''', [sid])
        data['announcements'] = query_db('SELECT * FROM announcements ORDER BY created_at DESC LIMIT 3')

    elif role == 'company':
        cid = session.get('company_id')
        if cid:
            data['company'] = query_db('SELECT * FROM companies WHERE id=?', [cid], one=True)
            data['open_jobs'] = query_db(
                "SELECT COUNT(*) as c FROM jobs WHERE company_id=? AND status='open'", [cid], one=True)['c']
            data['total_applications'] = query_db('''
                SELECT COUNT(*) as c FROM applications a
                JOIN jobs j ON a.job_id=j.id WHERE j.company_id=?
            ''', [cid], one=True)['c']
            data['shortlisted'] = query_db('''
                SELECT COUNT(*) as c FROM applications a
                JOIN jobs j ON a.job_id=j.id
                WHERE j.company_id=? AND a.status='shortlisted'
            ''', [cid], one=True)['c']
            data['selected'] = query_db('''
                SELECT COUNT(*) as c FROM applications a
                JOIN jobs j ON a.job_id=j.id
                WHERE j.company_id=? AND a.status='selected'
            ''', [cid], one=True)['c']
            data['recent_apps'] = query_db('''
                SELECT a.*, u.name as student_name, s.roll_number, s.department, s.cgpa, j.title
                FROM applications a
                JOIN students s ON a.student_id=s.id
                JOIN users u ON s.user_id=u.id
                JOIN jobs j ON a.job_id=j.id
                WHERE j.company_id=? ORDER BY a.applied_at DESC LIMIT 5
            ''', [cid])

    return render_template('dashboard.html', data=data, role=role)


@app.route('/students')
@login_required
@role_required('officer')
def students():
    search = request.args.get('search', '')
    dept = request.args.get('department', '')
    placed = request.args.get('placed', '')
    query = 'SELECT s.*, u.name, u.email FROM students s JOIN users u ON s.user_id=u.id WHERE 1=1'
    params = []
    if search:
        query += ' AND (u.name LIKE ? OR s.roll_number LIKE ?)'
        params += [f'%{search}%', f'%{search}%']
    if dept:
        query += ' AND s.department=?'
        params.append(dept)
    if placed != '':
        query += ' AND s.is_placed=?'
        params.append(int(placed))
    query += ' ORDER BY u.name'
    students_list = query_db(query, params)
    departments = query_db('SELECT DISTINCT department FROM students ORDER BY department')
    return render_template('students.html', students=students_list, departments=departments,
                           search=search, dept=dept, placed=placed)


@app.route('/students/<int:sid>')
@login_required
def student_detail(sid):
    student = query_db(
        'SELECT s.*, u.name, u.email FROM students s JOIN users u ON s.user_id=u.id WHERE s.id=?',
        [sid], one=True)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))
    if session['role'] == 'student' and session.get('student_id') != sid:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    applications = query_db('''
        SELECT a.*, j.title, c.name as company_name, j.location, j.salary_max,
               i.interview_date, i.interview_type, i.result as interview_result
        FROM applications a
        JOIN jobs j ON a.job_id=j.id
        JOIN companies c ON j.company_id=c.id
        LEFT JOIN interviews i ON i.application_id=a.id
        WHERE a.student_id=? ORDER BY a.applied_at DESC
    ''', [sid])
    placement = query_db('''
        SELECT p.*, c.name as company_name, j.title
        FROM placements p JOIN companies c ON p.company_id=c.id
        JOIN jobs j ON p.job_id=j.id WHERE p.student_id=?
    ''', [sid], one=True)
    return render_template('student_detail.html', student=student, applications=applications, placement=placement)


@app.route('/students/edit/<int:sid>', methods=['GET', 'POST'])
@login_required
def edit_student(sid):
    if session['role'] == 'student' and session.get('student_id') != sid:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    student = query_db(
        'SELECT s.*, u.name, u.email FROM students s JOIN users u ON s.user_id=u.id WHERE s.id=?',
        [sid], one=True)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))
    if request.method == 'POST':
        execute_db('UPDATE users SET name=? WHERE id=?', (request.form['name'], student['user_id']))
        dob = request.form['date_of_birth'] or None
        execute_db('''UPDATE students SET department=?, cgpa=?, year_of_passing=?, phone=?,
                      skills=?, backlogs=?, gender=?, date_of_birth=?, address=? WHERE id=?''',
                   (request.form['department'], request.form['cgpa'] or 0,
                    request.form['year_of_passing'] or None,
                    request.form['phone'], request.form['skills'],
                    request.form['backlogs'] or 0, request.form['gender'],
                    dob, request.form['address'], sid))
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_detail', sid=sid))
    return render_template('edit_student.html', student=student)


@app.route('/companies')
@login_required
def companies():
    search = request.args.get('search', '')
    query = 'SELECT c.*, u.email FROM companies c LEFT JOIN users u ON c.user_id=u.id WHERE 1=1'
    params = []
    if search:
        query += ' AND (c.name LIKE ? OR c.industry LIKE ?)'
        params += [f'%{search}%', f'%{search}%']
    query += ' ORDER BY c.name'
    companies_list = query_db(query, params)
    return render_template('companies.html', companies=companies_list, search=search)


@app.route('/companies/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_company():
    if request.method == 'POST':
        execute_db('''INSERT INTO companies (name, industry, website, description, hr_name, hr_phone, hr_email, address)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                   (request.form['name'], request.form['industry'], request.form['website'],
                    request.form['description'], request.form['hr_name'], request.form['hr_phone'],
                    request.form['hr_email'], request.form['address']))
        flash('Company added successfully!', 'success')
        return redirect(url_for('companies'))
    return render_template('add_company.html')


@app.route('/companies/<int:cid>')
@login_required
def company_detail(cid):
    company = query_db('SELECT * FROM companies WHERE id=?', [cid], one=True)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('companies'))
    jobs = query_db('SELECT * FROM jobs WHERE company_id=? ORDER BY created_at DESC', [cid])
    return render_template('company_detail.html', company=company, jobs=jobs)


@app.route('/companies/edit/<int:cid>', methods=['GET', 'POST'])
@login_required
def edit_company(cid):
    company = query_db('SELECT * FROM companies WHERE id=?', [cid], one=True)
    if not company:
        flash('Company not found.', 'danger')
        return redirect(url_for('companies'))
    if session['role'] == 'company' and session.get('company_id') != cid:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        execute_db('''UPDATE companies SET name=?, industry=?, website=?, description=?,
                      hr_name=?, hr_phone=?, hr_email=?, address=? WHERE id=?''',
                   (request.form['name'], request.form['industry'], request.form['website'],
                    request.form['description'], request.form['hr_name'], request.form['hr_phone'],
                    request.form['hr_email'], request.form['address'], cid))
        flash('Company updated!', 'success')
        return redirect(url_for('company_detail', cid=cid))
    return render_template('edit_company.html', company=company)


@app.route('/jobs')
@login_required
def jobs():
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    query = '''SELECT j.*, c.name as company_name,
                (SELECT COUNT(*) FROM applications a WHERE a.job_id=j.id) as app_count
               FROM jobs j JOIN companies c ON j.company_id=c.id WHERE 1=1'''
    params = []
    if status:
        query += ' AND j.status=?'
        params.append(status)
    if search:
        query += ' AND (j.title LIKE ? OR c.name LIKE ?)'
        params += [f'%{search}%', f'%{search}%']
    query += ' ORDER BY j.created_at DESC'
    jobs_list = query_db(query, params)
    return render_template('jobs.html', jobs=jobs_list, status=status, search=search)


@app.route('/jobs/add', methods=['GET', 'POST'])
@login_required
@role_required('officer', 'company')
def add_job():
    companies_list = query_db('SELECT * FROM companies ORDER BY name')
    if session['role'] == 'company':
        cid = session.get('company_id')
        companies_list = query_db('SELECT * FROM companies WHERE id=?', [cid])
    if request.method == 'POST':
        deadline = request.form['deadline'] or None
        execute_db('''INSERT INTO jobs (company_id, title, description, requirements, salary_min, salary_max,
                      job_type, location, min_cgpa, allowed_backlogs, allowed_departments, deadline)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (request.form['company_id'], request.form['title'], request.form['description'],
                    request.form['requirements'],
                    request.form['salary_min'] or None, request.form['salary_max'] or None,
                    request.form['job_type'], request.form['location'],
                    request.form['min_cgpa'] or 0, request.form['allowed_backlogs'] or 0,
                    request.form['allowed_departments'], deadline))
        flash('Job posted successfully!', 'success')
        return redirect(url_for('jobs'))
    return render_template('add_job.html', companies=companies_list)


@app.route('/jobs/<int:jid>')
@login_required
def job_detail(jid):
    job = query_db('''SELECT j.*, c.name as company_name, c.hr_email
                      FROM jobs j JOIN companies c ON j.company_id=c.id WHERE j.id=?''', [jid], one=True)
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs'))
    already_applied = False
    if session.get('role') == 'student':
        sid = session.get('student_id')
        if sid:
            existing = query_db('SELECT id FROM applications WHERE student_id=? AND job_id=?', [sid, jid], one=True)
            already_applied = existing is not None
    applications = []
    if session['role'] in ('officer', 'company'):
        applications = query_db('''
            SELECT a.*, u.name as student_name, s.roll_number, s.department, s.cgpa
            FROM applications a JOIN students s ON a.student_id=s.id
            JOIN users u ON s.user_id=u.id WHERE a.job_id=?
            ORDER BY a.applied_at DESC
        ''', [jid])
    return render_template('job_detail.html', job=job, already_applied=already_applied, applications=applications)


@app.route('/jobs/edit/<int:jid>', methods=['GET', 'POST'])
@login_required
@role_required('officer', 'company')
def edit_job(jid):
    job = query_db('SELECT * FROM jobs WHERE id=?', [jid], one=True)
    if not job:
        flash('Job not found.', 'danger')
        return redirect(url_for('jobs'))
    companies_list = query_db('SELECT * FROM companies ORDER BY name')
    if request.method == 'POST':
        deadline = request.form['deadline'] or None
        execute_db('''UPDATE jobs SET title=?, description=?, requirements=?, salary_min=?, salary_max=?,
                      job_type=?, location=?, min_cgpa=?, allowed_backlogs=?, allowed_departments=?,
                      deadline=?, status=? WHERE id=?''',
                   (request.form['title'], request.form['description'], request.form['requirements'],
                    request.form['salary_min'] or None, request.form['salary_max'] or None,
                    request.form['job_type'], request.form['location'],
                    request.form['min_cgpa'] or 0, request.form['allowed_backlogs'] or 0,
                    request.form['allowed_departments'], deadline, request.form['status'], jid))
        flash('Job updated!', 'success')
        return redirect(url_for('job_detail', jid=jid))
    return render_template('edit_job.html', job=job, companies=companies_list)


@app.route('/apply/<int:jid>', methods=['POST'])
@login_required
@role_required('student')
def apply_job(jid):
    sid = session.get('student_id')
    if not sid:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('dashboard'))
    student = query_db('SELECT * FROM students WHERE id=?', [sid], one=True)
    job = query_db('SELECT * FROM jobs WHERE id=?', [jid], one=True)
    if not job or job['status'] != 'open':
        flash('Job is not available.', 'danger')
        return redirect(url_for('jobs'))
    if float(student['cgpa'] or 0) < float(job['min_cgpa'] or 0):
        flash(f'You do not meet the minimum CGPA requirement of {job["min_cgpa"]}.', 'danger')
        return redirect(url_for('job_detail', jid=jid))
    if int(student['backlogs'] or 0) > int(job['allowed_backlogs'] or 0):
        flash('You have more backlogs than allowed.', 'danger')
        return redirect(url_for('job_detail', jid=jid))
    existing = query_db('SELECT id FROM applications WHERE student_id=? AND job_id=?', [sid, jid], one=True)
    if existing:
        flash('You have already applied for this job.', 'warning')
        return redirect(url_for('job_detail', jid=jid))
    execute_db('INSERT INTO applications (student_id, job_id) VALUES (?, ?)', (sid, jid))
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('applications'))


@app.route('/applications')
@login_required
def applications():
    role = session.get('role')
    if role == 'student':
        sid = session.get('student_id')
        apps = query_db('''
            SELECT a.*, j.title, c.name as company_name, j.location, j.salary_max, j.job_type,
                   i.interview_date, i.interview_time, i.interview_type, i.result as interview_result
            FROM applications a
            JOIN jobs j ON a.job_id=j.id
            JOIN companies c ON j.company_id=c.id
            LEFT JOIN interviews i ON i.application_id=a.id
            WHERE a.student_id=? ORDER BY a.applied_at DESC
        ''', [sid])
        return render_template('applications.html', applications=apps, role=role)
    elif role == 'company':
        cid = session.get('company_id')
        apps = query_db('''
            SELECT a.*, u.name as student_name, s.roll_number, s.department, s.cgpa, s.backlogs,
                   j.title, j.id as job_id
            FROM applications a
            JOIN students s ON a.student_id=s.id
            JOIN users u ON s.user_id=u.id
            JOIN jobs j ON a.job_id=j.id
            WHERE j.company_id=? ORDER BY a.applied_at DESC
        ''', [cid])
        return render_template('applications.html', applications=apps, role=role)
    else:
        status_filter = request.args.get('status', '')
        job_filter = request.args.get('job_id', '')
        query = '''SELECT a.*, u.name as student_name, s.roll_number, s.department, s.cgpa,
                          j.title, c.name as company_name
                   FROM applications a
                   JOIN students s ON a.student_id=s.id
                   JOIN users u ON s.user_id=u.id
                   JOIN jobs j ON a.job_id=j.id
                   JOIN companies c ON j.company_id=c.id WHERE 1=1'''
        params = []
        if status_filter:
            query += ' AND a.status=?'
            params.append(status_filter)
        if job_filter:
            query += ' AND a.job_id=?'
            params.append(job_filter)
        query += ' ORDER BY a.applied_at DESC'
        apps = query_db(query, params)
        all_jobs = query_db('SELECT id, title FROM jobs ORDER BY title')
        return render_template('applications.html', applications=apps, role=role,
                               status_filter=status_filter, all_jobs=all_jobs)


@app.route('/applications/update/<int:aid>', methods=['POST'])
@login_required
@role_required('officer', 'company')
def update_application(aid):
    new_status = request.form['status']
    remarks = request.form.get('remarks', '')
    execute_db('UPDATE applications SET status=?, remarks=? WHERE id=?', (new_status, remarks, aid))
    if new_status == 'selected':
        app_row = query_db(
            'SELECT a.*, j.company_id FROM applications a JOIN jobs j ON a.job_id=j.id WHERE a.id=?',
            [aid], one=True)
        if app_row:
            existing = query_db('SELECT id FROM placements WHERE student_id=? AND job_id=?',
                                [app_row['student_id'], app_row['job_id']], one=True)
            if not existing:
                execute_db('''INSERT INTO placements (student_id, company_id, job_id, offer_date)
                              VALUES (?, ?, ?, ?)''',
                           (app_row['student_id'], app_row['company_id'], app_row['job_id'],
                            datetime.now().strftime('%Y-%m-%d')))
                execute_db('UPDATE students SET is_placed=1 WHERE id=?', (app_row['student_id'],))
    flash('Application status updated!', 'success')
    ref = request.form.get('redirect', '')
    if ref == 'job':
        jid = request.form.get('job_id', '')
        return redirect(url_for('job_detail', jid=jid))
    return redirect(url_for('applications'))


@app.route('/interviews')
@login_required
def interviews():
    role = session.get('role')
    if role == 'student':
        sid = session.get('student_id')
        ivs = query_db('''
            SELECT i.*, j.title, c.name as company_name, a.status as app_status
            FROM interviews i
            JOIN applications a ON i.application_id=a.id
            JOIN jobs j ON a.job_id=j.id
            JOIN companies c ON j.company_id=c.id
            WHERE a.student_id=? ORDER BY i.interview_date
        ''', [sid])
    elif role == 'company':
        cid = session.get('company_id')
        ivs = query_db('''
            SELECT i.*, j.title, c.name as company_name,
                   u.name as student_name, s.roll_number, s.department
            FROM interviews i
            JOIN applications a ON i.application_id=a.id
            JOIN jobs j ON a.job_id=j.id
            JOIN companies c ON j.company_id=c.id
            JOIN students s ON a.student_id=s.id
            JOIN users u ON s.user_id=u.id
            WHERE j.company_id=? ORDER BY i.interview_date
        ''', [cid])
    else:
        ivs = query_db('''
            SELECT i.*, j.title, c.name as company_name,
                   u.name as student_name, s.roll_number, s.department, s.cgpa
            FROM interviews i
            JOIN applications a ON i.application_id=a.id
            JOIN jobs j ON a.job_id=j.id
            JOIN companies c ON j.company_id=c.id
            JOIN students s ON a.student_id=s.id
            JOIN users u ON s.user_id=u.id
            ORDER BY i.interview_date
        ''')
    return render_template('interviews.html', interviews=ivs, role=role)


@app.route('/interviews/schedule', methods=['GET', 'POST'])
@login_required
@role_required('officer', 'company')
def schedule_interview():
    if request.method == 'POST':
        aid = request.form['application_id']
        existing = query_db('SELECT id FROM interviews WHERE application_id=?', [aid], one=True)
        if existing:
            execute_db('''UPDATE interviews SET interview_date=?, interview_time=?, interview_type=?,
                          venue=?, interview_link=?, round_number=?, notes=? WHERE application_id=?''',
                       (request.form['interview_date'], request.form['interview_time'],
                        request.form['interview_type'], request.form['venue'],
                        request.form['interview_link'], request.form['round_number'] or 1,
                        request.form['notes'], aid))
        else:
            execute_db('''INSERT INTO interviews (application_id, interview_date, interview_time,
                          interview_type, venue, interview_link, round_number, notes)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                       (aid, request.form['interview_date'], request.form['interview_time'],
                        request.form['interview_type'], request.form['venue'],
                        request.form['interview_link'], request.form['round_number'] or 1,
                        request.form['notes']))
            execute_db("UPDATE applications SET status='interview_scheduled' WHERE id=?", (aid,))
        flash('Interview scheduled!', 'success')
        return redirect(url_for('interviews'))
    shortlisted = query_db('''
        SELECT a.id, u.name as student_name, s.roll_number, j.title, c.name as company_name
        FROM applications a
        JOIN students s ON a.student_id=s.id
        JOIN users u ON s.user_id=u.id
        JOIN jobs j ON a.job_id=j.id
        JOIN companies c ON j.company_id=c.id
        WHERE a.status IN ('shortlisted','interview_scheduled')
        ORDER BY u.name
    ''')
    return render_template('schedule_interview.html', applications=shortlisted)


@app.route('/interviews/result/<int:iid>', methods=['POST'])
@login_required
@role_required('officer', 'company')
def update_interview_result(iid):
    result = request.form['result']
    execute_db('UPDATE interviews SET result=? WHERE id=?', (result, iid))
    if result == 'pass':
        iv = query_db('SELECT application_id FROM interviews WHERE id=?', [iid], one=True)
        if iv:
            execute_db("UPDATE applications SET status='shortlisted' WHERE id=?", (iv['application_id'],))
    flash('Interview result updated!', 'success')
    return redirect(url_for('interviews'))


@app.route('/placements')
@login_required
def placements():
    role = session.get('role')
    if role == 'student':
        sid = session.get('student_id')
        pls = query_db('''
            SELECT p.*, c.name as company_name, j.title
            FROM placements p JOIN companies c ON p.company_id=c.id
            JOIN jobs j ON p.job_id=j.id WHERE p.student_id=?
        ''', [sid])
    elif role == 'company':
        cid = session.get('company_id')
        pls = query_db('''
            SELECT p.*, u.name as student_name, s.roll_number, s.department, j.title
            FROM placements p JOIN students s ON p.student_id=s.id
            JOIN users u ON s.user_id=u.id
            JOIN jobs j ON p.job_id=j.id WHERE p.company_id=?
        ''', [cid])
    else:
        pls = query_db('''
            SELECT p.*, u.name as student_name, s.roll_number, s.department,
                   c.name as company_name, j.title
            FROM placements p JOIN students s ON p.student_id=s.id
            JOIN users u ON s.user_id=u.id
            JOIN companies c ON p.company_id=c.id
            JOIN jobs j ON p.job_id=j.id
            ORDER BY p.created_at DESC
        ''')
    return render_template('placements.html', placements=pls, role=role)


@app.route('/placements/update/<int:pid>', methods=['POST'])
@login_required
@role_required('officer')
def update_placement(pid):
    execute_db('UPDATE placements SET package=?, joining_date=?, offer_date=? WHERE id=?',
               (request.form['package'] or None,
                request.form['joining_date'] or None,
                request.form['offer_date'] or None, pid))
    flash('Placement updated!', 'success')
    return redirect(url_for('placements'))


@app.route('/announcements', methods=['GET', 'POST'])
@login_required
def announcements():
    if request.method == 'POST' and session.get('role') == 'officer':
        execute_db('INSERT INTO announcements (title, content, created_by) VALUES (?, ?, ?)',
                   (request.form['title'], request.form['content'], session['user_id']))
        flash('Announcement posted!', 'success')
        return redirect(url_for('announcements'))
    ann_list = query_db('''
        SELECT a.*, u.name as author FROM announcements a
        JOIN users u ON a.created_by=u.id ORDER BY a.created_at DESC
    ''')
    return render_template('announcements.html', announcements=ann_list)


@app.route('/announcements/delete/<int:aid>', methods=['POST'])
@login_required
@role_required('officer')
def delete_announcement(aid):
    execute_db('DELETE FROM announcements WHERE id=?', (aid,))
    flash('Announcement deleted.', 'info')
    return redirect(url_for('announcements'))


@app.route('/reports')
@login_required
@role_required('officer')
def reports():
    dept_report = query_db('''
        SELECT s.department,
               COUNT(s.id) as total,
               SUM(s.is_placed) as placed,
               AVG(s.cgpa) as avg_cgpa,
               ROUND(SUM(s.is_placed)*100.0/COUNT(s.id),1) as placement_pct
        FROM students s GROUP BY s.department ORDER BY placement_pct DESC
    ''')
    company_report = query_db('''
        SELECT c.name as company_name, COUNT(DISTINCT p.student_id) as hired,
               AVG(p.package) as avg_package, MAX(p.package) as max_package
        FROM companies c LEFT JOIN placements p ON p.company_id=c.id
        GROUP BY c.id ORDER BY hired DESC
    ''')
    monthly_placements = query_db('''
        SELECT DATE_FORMAT(created_at, '%Y-%m') as month, COUNT(*) as count
        FROM placements GROUP BY month ORDER BY month DESC LIMIT 12
    ''')
    top_packages = query_db('''
        SELECT u.name as student_name, s.roll_number, s.department,
               c.name as company_name, j.title, p.package
        FROM placements p JOIN students s ON p.student_id=s.id
        JOIN users u ON s.user_id=u.id
        JOIN companies c ON p.company_id=c.id
        JOIN jobs j ON p.job_id=j.id
        WHERE p.package IS NOT NULL
        ORDER BY p.package DESC LIMIT 10
    ''')
    return render_template('reports.html', dept_report=dept_report,
                           company_report=company_report,
                           monthly_placements=monthly_placements,
                           top_packages=top_packages)


@app.route('/profile')
@login_required
def profile():
    user = query_db('SELECT * FROM users WHERE id=?', [session['user_id']], one=True)
    extra = None
    if session['role'] == 'student':
        extra = query_db('SELECT * FROM students WHERE user_id=?', [session['user_id']], one=True)
    elif session['role'] == 'company':
        extra = query_db('SELECT * FROM companies WHERE user_id=?', [session['user_id']], one=True)
    return render_template('profile.html', user=user, extra=extra)


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user = query_db('SELECT * FROM users WHERE id=?', [session['user_id']], one=True)
        if not check_password_hash(user['password'], request.form['current_password']):
            flash('Current password is incorrect.', 'danger')
        elif request.form['new_password'] != request.form['confirm_password']:
            flash('New passwords do not match.', 'danger')
        else:
            hashed = generate_password_hash(request.form['new_password'])
            execute_db('UPDATE users SET password=? WHERE id=?', (hashed, session['user_id']))
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
    return render_template('change_password.html')


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
