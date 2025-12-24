from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List

app = FastAPI(title="To-Do-Server")

class Task(BaseModel):
    title: str
    completed: bool = False
    
class TaskResponse(Task):
    id: int


conn = sqlite3.connect("tasks.db", check_same_thread=False)
conn.row_factory = sqlite3.Row  # Enable dictionary-like row access
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed BOOLEAN DEFAULT FALSE
    )
    """
)
conn.commit()


@app.post("/tasks", response_model=dict)
def create_task(task: Task):
    cur.execute(
        "INSERT INTO tasks (title, completed) VALUES (?, ?)",
        (task.title, task.completed)
    )
    conn.commit()
    task_id = cur.lastrowid
    return {"id": task_id, "title": task.title, "completed": task.completed}


@app.get("/tasks", response_model=List[TaskResponse])
def get_all_tasks():
    cur.execute("SELECT id, title, completed FROM tasks")
    rows = cur.fetchall()
    return [dict(row) for row in rows]

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    cur.execute("SELECT id, title, completed FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return dict(row)

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updated_task: Task):
    cur.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="Task for update not found")
    
    cur.execute(
        "UPDATE tasks SET title = ?, completed = ? WHERE id = ?",
        (updated_task.title, updated_task.completed, task_id)
    )
    conn.commit()
    
    return {"id": task_id, "title": updated_task.title, "completed": updated_task.completed}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    """Delete a task"""
    # Check if task exists
    cur.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="Task for delete not found")
    
    # Delete the task
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    
    return {"status": "deleted", "id": task_id}

@app.get("/")
def read_root():
    return {"message": "To-Do Server API", "docs": "/docs"}