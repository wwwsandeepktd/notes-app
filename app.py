
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
DB_PATH = os.path.join(DB_DIR, 'notes.db')
os.makedirs(DB_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.before_first_request
def setup():
    init_db()

@app.route('/', methods=['GET'])
def index():
    q = request.args.get('q', '').strip()
    conn = get_db()
    if q:
        rows = conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR body LIKE ? ORDER BY updated_at DESC",
            (f"%{q}%", f"%{q}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    return render_template('index.html', notes=rows, q=q)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    if not title or not body:
        flash('Title and note body are required.', 'error')
        return redirect(url_for('index'))
    now = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute("INSERT INTO notes (title, body, created_at, updated_at) VALUES (?, ?, ?, ?)",
                 (title, body, now, now))
    conn.commit()
    conn.close()
    flash('Note added!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete(note_id):
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    flash('Note deleted.', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:note_id>', methods=['POST'])
def edit(note_id):
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    if not title or not body:
        flash('Title and note body are required.', 'error')
        return redirect(url_for('index'))
    now = datetime.utcnow().isoformat()
    conn = get_db()
    conn.execute("UPDATE notes SET title = ?, body = ?, updated_at = ? WHERE id = ?",
                 (title, body, now, note_id))
    conn.commit()
    conn.close()
    flash('Note updated!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
