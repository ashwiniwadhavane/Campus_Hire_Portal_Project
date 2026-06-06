"""
CampusHire Portal - Sample Data Seeder (MySQL version)
Run AFTER starting the app once (tables are created by run.py / init_db).
Usage: python seed.py
"""
import os
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'host':     os.environ.get('MYSQL_HOST',     'localhost'),
    'port':     int(os.environ.get('MYSQL_PORT', 3306)),
    'user':     os.environ.get('MYSQL_USER',     'root'),
    'password': os.environ.get('MYSQL_PASSWORD', 'Manager'),
    'database': os.environ.get('MYSQL_DATABASE', 'campushire'),
    'charset':  'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}


def seed():
    db = pymysql.connect(**DB_CONFIG)
    cur = db.cursor()

    users = [
        ('Arjun Sharma',    'arjun@student.edu',  'student', 'student123'),
        ('Priya Nair',      'priya@student.edu',  'student', 'student123'),
        ('Rahul Mehta',     'rahul@student.edu',  'student', 'student123'),
        ('Sneha Patel',     'sneha@student.edu',  'student', 'student123'),
        ('Karthik Reddy',   'karthik@student.edu','student', 'student123'),
        ('Divya Krishnan',  'divya@student.edu',  'student', 'student123'),
        ('Amit Gupta',      'amit@student.edu',   'student', 'student123'),
        ('TCS HR',          'hr@tcs.com',         'company', 'company123'),
        ('Infosys HR',      'hr@infosys.com',     'company', 'company123'),
        ('Wipro HR',        'hr@wipro.com',       'company', 'company123'),
    ]

    uid_map = {}
    for name, email, role, pwd in users:
        cur.execute('SELECT id FROM users WHERE email=%s', (email,))
        row = cur.fetchone()
        if row:
            uid_map[email] = row['id']
        else:
            cur.execute(
                'INSERT INTO users (name, email, password, role) VALUES (%s,%s,%s,%s)',
                (name, email, generate_password_hash(pwd), role)
            )
            uid_map[email] = cur.lastrowid
    db.commit()

    students_data = [
        ('arjun@student.edu',   'CS2021001',  'Computer Science',              8.5, 2024, '9876543210', 'Python,Java,React,SQL',          0, 'Male',   '2001-05-15'),
        ('priya@student.edu',   'IT2021002',  'Information Technology',         9.1, 2024, '9876543211', 'Node.js,Angular,MongoDB',         0, 'Female', '2001-07-20'),
        ('rahul@student.edu',   'CS2021003',  'Computer Science',              7.2, 2024, '9876543212', 'C++,Linux,DevOps',                1, 'Male',   '2001-03-10'),
        ('sneha@student.edu',   'ECE2021004', 'Electronics & Communication',   8.8, 2024, '9876543213', 'VLSI,Embedded,IoT',               0, 'Female', '2001-09-05'),
        ('karthik@student.edu', 'ME2021005',  'Mechanical Engineering',        7.8, 2024, '9876543214', 'AutoCAD,MATLAB,SolidWorks',        0, 'Male',   '2001-11-25'),
        ('divya@student.edu',   'IT2021006',  'Information Technology',         8.0, 2024, '9876543215', 'Python,Data Science,ML',          0, 'Female', '2001-06-18'),
        ('amit@student.edu',    'CS2021007',  'Computer Science',              6.8, 2024, '9876543216', 'Java,Spring Boot,SQL',             2, 'Male',   '2001-01-30'),
    ]

    sid_map = {}
    for email, roll, dept, cgpa, yop, phone, skills, backlogs, gender, dob in students_data:
        uid = uid_map[email]
        cur.execute('SELECT id FROM students WHERE user_id=%s', (uid,))
        row = cur.fetchone()
        if row:
            sid_map[email] = row['id']
        else:
            cur.execute('''INSERT INTO students
                (user_id, roll_number, department, cgpa, year_of_passing, phone, skills, backlogs, gender, date_of_birth)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (uid, roll, dept, cgpa, yop, phone, skills, backlogs, gender, dob))
            sid_map[email] = cur.lastrowid
    db.commit()

    companies_data = [
        ('hr@tcs.com',     'Tata Consultancy Services', 'IT & Software', 'https://www.tcs.com',     'TCS is a global IT services company.',              'Ramesh Kumar', '9988776655', 'hr@tcs.com',     'TCS House, Mumbai'),
        ('hr@infosys.com', 'Infosys Limited',           'IT & Software', 'https://www.infosys.com', 'Infosys is a leading global technology company.',   'Meena Pillai', '9988776656', 'hr@infosys.com', 'Electronic City, Bangalore'),
        ('hr@wipro.com',   'Wipro Technologies',        'IT & Software', 'https://www.wipro.com',   'Wipro is a technology and consulting company.',     'Suresh Babu',  '9988776657', 'hr@wipro.com',   'Sarjapur, Bangalore'),
    ]

    cid_map = {}
    for email, name, industry, website, desc, hr_name, hr_phone, hr_email, addr in companies_data:
        uid = uid_map[email]
        cur.execute('SELECT id FROM companies WHERE user_id=%s', (uid,))
        row = cur.fetchone()
        if row:
            cid_map[email] = row['id']
        else:
            cur.execute('''INSERT INTO companies
                (user_id, name, industry, website, description, hr_name, hr_phone, hr_email, address)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (uid, name, industry, website, desc, hr_name, hr_phone, hr_email, addr))
            cid_map[email] = cur.lastrowid
    db.commit()

    jobs_raw = [
        (cid_map['hr@tcs.com'],     'Software Engineer',          'Backend and full-stack development roles.',         'B.Tech CS/IT, strong coding skills', 6.0,  12.0, 'full-time', 'Mumbai / Pune',         6.5, 0, 'Computer Science,Information Technology', '2024-12-31'),
        (cid_map['hr@tcs.com'],     'System Engineer',            'Application development and maintenance.',          'Any engineering branch',              5.0,   8.0, 'full-time', 'Chennai / Hyderabad',   6.0, 1, 'All',                                     '2024-12-31'),
        (cid_map['hr@infosys.com'], 'Associate Software Engineer','Java full-stack development.',                      'CS/IT students with Java knowledge',  7.0,  14.0, 'full-time', 'Bangalore',             7.0, 0, 'Computer Science,Information Technology', '2024-11-30'),
        (cid_map['hr@infosys.com'], 'Data Analyst',               'Analyze and visualize business data.',              'Python, SQL, Tableau preferred',       8.0,  12.0, 'full-time', 'Pune',                  6.5, 0, 'Computer Science,Information Technology', '2024-11-30'),
        (cid_map['hr@wipro.com'],   'Project Engineer',           'Software testing and QA automation.',               'Good understanding of SDLC',           6.0,  10.0, 'full-time', 'Hyderabad',             6.0, 1, 'All',                                     '2024-12-15'),
    ]

    jid_list = []
    for jd in jobs_raw:
        cur.execute('SELECT id FROM jobs WHERE title=%s AND company_id=%s', (jd[1], jd[0]))
        row = cur.fetchone()
        if row:
            jid_list.append(row['id'])
        else:
            cur.execute('''INSERT INTO jobs
                (company_id, title, description, requirements, salary_min, salary_max,
                 job_type, location, min_cgpa, allowed_backlogs, allowed_departments, deadline)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', jd)
            jid_list.append(cur.lastrowid)
    db.commit()

    apps = [
        (sid_map['arjun@student.edu'],   jid_list[0], 'shortlisted'),
        (sid_map['arjun@student.edu'],   jid_list[2], 'applied'),
        (sid_map['priya@student.edu'],   jid_list[2], 'interview_scheduled'),
        (sid_map['priya@student.edu'],   jid_list[3], 'shortlisted'),
        (sid_map['rahul@student.edu'],   jid_list[1], 'applied'),
        (sid_map['sneha@student.edu'],   jid_list[4], 'applied'),
        (sid_map['divya@student.edu'],   jid_list[3], 'selected'),
        (sid_map['amit@student.edu'],    jid_list[1], 'rejected'),
    ]

    aid_map = {}
    for sid, jid, status in apps:
        cur.execute('SELECT id FROM applications WHERE student_id=%s AND job_id=%s', (sid, jid))
        row = cur.fetchone()
        if row:
            aid_map[(sid, jid)] = row['id']
        else:
            cur.execute('INSERT INTO applications (student_id, job_id, status) VALUES (%s,%s,%s)',
                        (sid, jid, status))
            aid_map[(sid, jid)] = cur.lastrowid
    db.commit()

    priya_app_id = aid_map.get((sid_map['priya@student.edu'], jid_list[2]))
    if priya_app_id:
        cur.execute('SELECT id FROM interviews WHERE application_id=%s', (priya_app_id,))
        if not cur.fetchone():
            cur.execute('''INSERT INTO interviews
                (application_id, interview_date, interview_time, interview_type, venue, round_number)
                VALUES (%s,%s,%s,%s,%s,%s)''',
                (priya_app_id, '2024-11-20', '10:00:00', 'in-person', 'HR Room, Infosys Campus', 1))
    db.commit()

    divya_sid = sid_map['divya@student.edu']
    cur.execute('SELECT id FROM placements WHERE student_id=%s', (divya_sid,))
    if not cur.fetchone():
        cur.execute('''INSERT INTO placements (student_id, company_id, job_id, offer_date, package)
                       VALUES (%s,%s,%s,%s,%s)''',
                    (divya_sid, cid_map['hr@infosys.com'], jid_list[3], '2024-10-15', 8.0))
        cur.execute('UPDATE students SET is_placed=1 WHERE id=%s', (divya_sid,))
    db.commit()

    officer_id = uid_map.get('officer@campus.edu')
    cur.execute('SELECT id FROM users WHERE email=%s', ('officer@campus.edu',))
    row = cur.fetchone()
    officer_id = row['id'] if row else 1

    announcements = [
        ('Infosys Campus Drive 2024',
         'Infosys will be conducting a campus placement drive on November 20, 2024. All eligible students must register before November 15.',
         officer_id),
        ('TCS Placement Shortlist Released',
         'TCS has shortlisted 15 students for the next round of interviews. Please check your application status.',
         officer_id),
        ('Resume Submission Deadline Extended',
         'The deadline to submit updated resumes to the placement cell has been extended to November 10, 2024.',
         officer_id),
    ]
    for title, content, cby in announcements:
        cur.execute('SELECT id FROM announcements WHERE title=%s', (title,))
        if not cur.fetchone():
            cur.execute('INSERT INTO announcements (title, content, created_by) VALUES (%s,%s,%s)',
                        (title, content, cby))
    db.commit()
    db.close()

    print("Seed data inserted successfully!")
    print("\nLogin credentials:")
    print("  Officer : officer@campus.edu / admin123")
    print("  Student : arjun@student.edu  / student123")
    print("  Company : hr@tcs.com         / company123")


if __name__ == '__main__':
    seed()
