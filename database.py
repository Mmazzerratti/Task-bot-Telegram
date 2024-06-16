import sqlite3


def get_connection():
    conn = sqlite3.connect('tasks.db')
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        user_id INTEGER,
                        task_title TEXT,
                        task_description TEXT
                    )''')
    conn.commit()
    conn.close()


def add_task(user_id, task_title, task_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (user_id, task_title, task_description) VALUES (?, ?, ?)',
                   (user_id, task_title, task_description))
    conn.commit()
    conn.close()


def get_tasks(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT task_title, task_description FROM tasks WHERE user_id = ?', (user_id,))
    tasks = cursor.fetchall()
    conn.close()
    return [f"{title}: {description}" for title, description in tasks]


def delete_task(user_id, task_index):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid FROM tasks WHERE user_id = ?', (user_id,))
    task_ids = cursor.fetchall()
    if 0 <= task_index < len(task_ids):
        task_id = task_ids[task_index][0]
        cursor.execute('DELETE FROM tasks WHERE rowid = ?', (task_id,))
        conn.commit()
    conn.close()


def update_task_name(user_id, task_index, new_title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid FROM tasks WHERE user_id = ?', (user_id,))
    task_ids = cursor.fetchall()
    if 0 <= task_index < len(task_ids):
        task_id = task_ids[task_index][0]
        cursor.execute('UPDATE tasks SET task_title = ? WHERE rowid = ?', (new_title, task_id))
        conn.commit()
    conn.close()


def update_task_description(user_id, task_index, new_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid FROM tasks WHERE user_id = ?', (user_id,))
    task_ids = cursor.fetchall()
    if 0 <= task_index < len(task_ids):
        task_id = task_ids[task_index][0]
        cursor.execute('UPDATE tasks SET task_description = ? WHERE rowid = ?', (new_description, task_id))
        conn.commit()
    conn.close()


create_tables()