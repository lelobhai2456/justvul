import os
import sys
import sqlite3
import subprocess
import pickle
import base64
import requests
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash, make_response
)
import database

app = Flask(__name__)
app.secret_key = "vulnerable_static_secret_key_12345"  # Deliberately weak/static secret key

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, 'sample_files')

# Ensure DB exists
if not os.path.exists(database.DB_PATH):
    database.init_db()

@app.before_request
def ensure_default_session():
    # Simulate a logged-in user for CSRF and IDOR challenges
    if 'user_id' not in session:
        session['user_id'] = 2  # Logged in as 'alice' by default
        session['username'] = 'alice'
        session['role'] = 'user'

@app.context_processor
def inject_user():
    return {
        'current_user_id': session.get('user_id', 2),
        'current_username': session.get('username', 'alice'),
        'current_role': session.get('role', 'user')
    }

# ==========================================
# 0. DASHBOARD & UTILITIES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset-db', methods=['POST'])
def reset_db_route():
    database.init_db(reset=True)
    session['user_id'] = 2
    session['username'] = 'alice'
    session['role'] = 'user'
    flash("Database reset successfully to initial factory state!", "success")
    return redirect(request.referrer or url_for('index'))

@app.route('/switch-session/<username>')
def switch_session(username):
    conn = database.get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        flash(f"Switched active session to: {user['username']} (Role: {user['role']})", "info")
    return redirect(request.referrer or url_for('index'))

# ==========================================
# 1. PASTEJACKING & CLIPBOARD HIJACKING LAB
# ==========================================
@app.route('/pastejack')
def pastejack():
    return render_template('pastejack.html')

# ==========================================
# 2. SQL INJECTION (SQLi) LAB
# ==========================================
@app.route('/sqli')
def sqli():
    return render_template('sqli.html', login_result=None, search_results=None)

@app.route('/sqli/login', methods=['POST'])
def sqli_login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # VULNERABLE: Direct string concatenation into SQL query!
    raw_query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    conn = database.get_db()
    error_msg = None
    user = None
    try:
        cursor = conn.cursor()
        cursor.execute(raw_query)
        user = cursor.fetchone()
    except Exception as e:
        error_msg = str(e)
    finally:
        conn.close()

    return render_template(
        'sqli.html',
        executed_query=raw_query,
        user=user,
        error_msg=error_msg,
        active_tab='login'
    )

@app.route('/sqli/search', methods=['GET'])
def sqli_search():
    query = request.args.get('q', '')
    results = []
    error_msg = None
    raw_query = ""

    if query:
        # VULNERABLE: Direct concatenation allowing UNION SELECT attacks!
        raw_query = f"SELECT id, name, category, price, description FROM products WHERE name LIKE '%{query}%'"
        conn = database.get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(raw_query)
            results = cursor.fetchall()
        except Exception as e:
            error_msg = str(e)
        finally:
            conn.close()

    return render_template(
        'sqli.html',
        search_query=query,
        executed_search_query=raw_query,
        search_results=results,
        search_error=error_msg,
        active_tab='search'
    )

# ==========================================
# 3. CROSS-SITE SCRIPTING (XSS) LAB
# ==========================================
@app.route('/xss')
def xss():
    conn = database.get_db()
    comments = conn.execute("SELECT * FROM comments ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('xss.html', comments=comments)

@app.route('/xss/reflected')
def xss_reflected():
    # VULNERABLE: Input is passed directly to template where it is rendered with `| safe`
    user_input = request.args.get('term', '')
    conn = database.get_db()
    comments = conn.execute("SELECT * FROM comments ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('xss.html', reflected_term=user_input, comments=comments, active_tab='reflected')

@app.route('/xss/stored', methods=['POST'])
def xss_stored():
    author = request.form.get('author', 'Anonymous')
    comment = request.form.get('comment', '')

    # VULNERABLE: Stored in raw form without sanitization or HTML escaping
    conn = database.get_db()
    conn.execute("INSERT INTO comments (author, comment) VALUES (?, ?)", (author, comment))
    conn.commit()
    conn.close()

    flash("Comment posted successfully!", "success")
    return redirect(url_for('xss') + '?tab=stored')

@app.route('/xss/clear-comments', methods=['POST'])
def xss_clear():
    conn = database.get_db()
    conn.execute("DELETE FROM comments")
    # Add back default harmless ones
    conn.execute("INSERT INTO comments (author, comment) VALUES ('Admin', 'Welcome to the comment board!')")
    conn.commit()
    conn.close()
    flash("Comments reset to default!", "info")
    return redirect(url_for('xss') + '?tab=stored')

# ==========================================
# 4. COMMAND INJECTION (RCE) LAB
# ==========================================
@app.route('/rce', methods=['GET', 'POST'])
def rce():
    output = None
    executed_command = None
    target = ""

    if request.method == 'POST':
        target = request.form.get('target', '').strip()
        if target:
            # VULNERABLE: Concatenating input directly into shell execution!
            # Uses ping -n 1 on Windows
            executed_command = f"ping -n 1 {target}"
            try:
                # shell=True allows command chaining (&, &&, |, ||)
                raw_out = subprocess.check_output(
                    executed_command,
                    shell=True,
                    stderr=subprocess.STDOUT,
                    timeout=5
                )
                output = raw_out.decode('utf-8', errors='replace')
            except subprocess.CalledProcessError as e:
                output = e.output.decode('utf-8', errors='replace')
            except subprocess.TimeoutExpired:
                output = "Error: Command timed out after 5 seconds."
            except Exception as e:
                output = f"Execution error: {str(e)}"

    return render_template('rce.html', output=output, executed_command=executed_command, target=target)

# ==========================================
# 5. PATH TRAVERSAL / LFI LAB
# ==========================================
@app.route('/traversal')
def traversal():
    filename = request.args.get('file', 'public_readme.txt')
    file_content = None
    error_msg = None
    resolved_path = None

    # VULNERABLE: Direct concatenation with os.path.join without verifying canonical root!
    # e.g., filename='../../app.py' or '..\..\..\windows\win.ini' escapes SAMPLE_DIR
    target_path = os.path.join(SAMPLE_DIR, filename)
    resolved_path = os.path.abspath(target_path)

    try:
        with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
    except Exception as e:
        error_msg = str(e)

    # List available legitimate files
    available_files = []
    if os.path.exists(SAMPLE_DIR):
        available_files = os.listdir(SAMPLE_DIR)

    return render_template(
        'traversal.html',
        current_file=filename,
        resolved_path=resolved_path,
        file_content=file_content,
        error_msg=error_msg,
        available_files=available_files
    )

# ==========================================
# 6. SERVER-SIDE REQUEST FORGERY (SSRF) LAB
# ==========================================
@app.route('/ssrf', methods=['GET', 'POST'])
def ssrf():
    url = ""
    status_code = None
    response_body = None
    error_msg = None

    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if url:
            try:
                # VULNERABLE: Server makes an outbound request to user-controlled URL without validation
                # Can access 127.0.0.1:5000/internal/cloud-metadata or internal network ports!
                resp = requests.get(url, timeout=3, headers={'User-Agent': 'VulnLab-Webhook-Previewer/1.0'})
                status_code = resp.status_code
                response_body = resp.text[:4000]  # Cap length for preview
            except Exception as e:
                error_msg = str(e)

    return render_template('ssrf.html', url=url, status_code=status_code, response_body=response_body, error_msg=error_msg)

# Simulated internal microservice endpoint that should NOT be accessible externally!
@app.route('/internal/cloud-metadata')
def internal_metadata():
    # Only meant for localhost internal calls
    remote_ip = request.remote_addr
    return jsonify({
        "status": "SECRET_INTERNAL_METADATA_UNLOCKED",
        "instance_id": "i-09ab12cd34ef5678",
        "iam_role": "VulnLab-Root-Service-Account",
        "security_credentials": {
            "AccessKeyId": "AKIAVULNLABDEMO2026KEY",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "Token": "FLAG{ssrf_internal_metadata_leaked_8819}"
        },
        "internal_redis": "redis://10.0.4.12:6379",
        "caller_remote_ip": remote_ip
    })

# ==========================================
# 7. INSECURE DIRECT OBJECT REFERENCE (IDOR)
# ==========================================
@app.route('/idor')
def idor():
    user_id = request.args.get('id', session.get('user_id', 2))
    conn = database.get_db()
    # VULNERABLE: No authorization check! Any user can pass any id to see anyone's profile, balance, & secret API keys!
    user_data = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    all_users = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()

    return render_template('idor.html', user_data=user_data, current_id=user_id, all_users=all_users)

@app.route('/api/user/<int:user_id>')
def api_user_idor(user_id):
    # VULNERABLE: Direct API endpoint leaking user data without auth check
    conn = database.get_db()
    user = conn.execute("SELECT id, username, email, role, bio, secret_api_key, account_balance FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return jsonify(dict(user))
    return jsonify({"error": "User not found"}), 404

# ==========================================
# 8. CROSS-SITE REQUEST FORGERY (CSRF) LAB
# ==========================================
@app.route('/csrf')
def csrf():
    conn = database.get_db()
    current_user = conn.execute("SELECT * FROM users WHERE id = ?", (session.get('user_id', 2),)).fetchone()
    users = conn.execute("SELECT id, username, account_balance FROM users").fetchall()
    conn.close()
    return render_template('csrf.html', user=current_user, all_users=users)

@app.route('/csrf/transfer', methods=['POST'])
def csrf_transfer():
    # VULNERABLE: State-changing endpoint without any CSRF token or origin validation!
    # Relies solely on ambient cookies / session!
    recipient_username = request.form.get('recipient')
    amount_str = request.form.get('amount', '0')

    try:
        amount = float(amount_str)
    except ValueError:
        flash("Invalid transfer amount.", "error")
        return redirect(url_for('csrf'))

    sender_id = session.get('user_id', 2)

    conn = database.get_db()
    sender = conn.execute("SELECT * FROM users WHERE id = ?", (sender_id,)).fetchone()
    recipient = conn.execute("SELECT * FROM users WHERE username = ?", (recipient_username,)).fetchone()

    if not recipient:
        flash(f"Recipient user '{recipient_username}' not found!", "error")
        conn.close()
        return redirect(url_for('csrf'))

    if sender['account_balance'] < amount:
        flash("Insufficient account balance for this transfer!", "error")
        conn.close()
        return redirect(url_for('csrf'))

    # Perform balance update
    conn.execute("UPDATE users SET account_balance = account_balance - ? WHERE id = ?", (amount, sender_id))
    conn.execute("UPDATE users SET account_balance = account_balance + ? WHERE id = ?", (amount, recipient['id']))
    conn.commit()
    conn.close()

    flash(f"Successfully transferred ${amount:.2f} to {recipient_username}!", "success")
    return redirect(url_for('csrf'))

@app.route('/csrf/attacker-simulation')
def csrf_attacker():
    # Simulates an external malicious website tricking the victim
    return render_template('csrf_poc.html')

# ==========================================
# 9. INSECURE DESERIALIZATION & EVAL LAB
# ==========================================
@app.route('/deserial', methods=['GET', 'POST'])
def deserial():
    eval_result = None
    eval_error = None
    pickle_result = None
    pickle_error = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'eval':
            expr = request.form.get('expression', '')
            # VULNERABLE: Direct Python eval() of user-supplied string!
            try:
                eval_result = str(eval(expr))
            except Exception as e:
                eval_error = str(e)

        elif action == 'pickle':
            payload_b64 = request.form.get('pickle_data', '')
            # VULNERABLE: Unpickling untrusted serialized byte stream!
            try:
                raw_bytes = base64.b64decode(payload_b64)
                unpickled = pickle.loads(raw_bytes)
                pickle_result = f"Object of type '{type(unpickled).__name__}': {repr(unpickled)}"
            except Exception as e:
                pickle_error = str(e)

    return render_template(
        'deserial.html',
        eval_result=eval_result,
        eval_error=eval_error,
        pickle_result=pickle_result,
        pickle_error=pickle_error
    )

# ==========================================
# 10. INFORMATION DISCLOSURE
# ==========================================
@app.route('/.git/config')
def git_config():
    # Mock exposed .git repository config
    return """[core]
    repositoryformatversion = 0
    filemode = false
    bare = false
    logallrefupdates = true
    symlinks = false
    ignorecase = true
[remote "origin"]
    url = https://github.com/vulnlab-internal/production-core.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
    remote = origin
    merge = refs/heads/main
# FLAG{git_exposure_found_source_code_leak_2026}
""", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    print("=" * 60)
    print("  VULNLAB - DELIBERATELY VULNERABLE WEB APPLICATION")
    print("  Running at: http://127.0.0.1:5000")
    print("  FOR LOCAL EDUCATIONAL AND SECURITY TESTING ONLY!")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
