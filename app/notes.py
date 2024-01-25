from app import app
from flask import request, jsonify
import mysql.connector
from dotenv import load_dotenv, dotenv_values
import os

# DB connection
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

db = mysql.connector.connect(host=db_host, port=db_port, username=db_username, password=db_password, database=db_name)

@app.route('/api/create_note', methods=['POST'])
def create_note():
    title = request.json.get('title')
    description = request.json.get('description')
    created_dt = request.json.get("created_dt") 
    user_id = request.json.get("user_id")

    cursor = db.cursor()

    # create a new note
    cursor.execute("INSERT INTO notes (title, description, createdDT, user_id) VALUES(%s, %s, %s, %s)", (title, description, created_dt, user_id))

    db.commit()

    return jsonify({"message": "Note created successfully", "status": "success"})

@app.route('/api/get_notes', methods=['POST'])                   
def get_notes():
    username = request.json.get('username')

    cursor = db.cursor(dictionary=True)

    # get all notes
    cursor.execute("SELECT notes.id, notes.title, notes.description, notes.createdDT, notes.updatedDT FROM notes JOIN users ON notes.user_id = users.id WHERE users.username = %s", (username,))

    notes = cursor.fetchall()
    if not notes:
        return jsonify({"message": "No notes found", "status": "error"})
        db.commit()
    else: return jsonify({"message": notes, "status": "success", "length": len(notes)})

@app.route('/api/delete_note/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    cursor = db.cursor()

    cursor.execute("DELETE FROM notes WHERE id = %s", (note_id,))
    isDeleted = cursor.rowcount > 0
    if isDeleted:
        return  jsonify({"message":"deleted successfully","status":'success'})
        db.commit()
    else:
        return jsonify({"message": "Note not found", "status": "error"})

@app.route('/api/update_note/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    cursor = db.cursor(dictionary=True)

    cursor.execute('SELECT * FROM notes WHERE id = %s', (note_id,))

    existing_note = cursor.fetchone()
    if not existing_note:
        return jsonify({"message": "Note not found", "status": "error"})

    # Get the updated details from the request
    updated_title = request.json.get('title', existing_note['title'])
    updated_description = request.json.get('description', existing_note['description'])
    updated_dt = request.json.get('updated_dt', existing_note['updatedDT'])

    update_query = "UPDATE notes SET title = %s, description = %s, updatedDT = %s WHERE id = %s"
    update_values = (updated_title, updated_description, updated_dt, note_id)

    cursor.execute(update_query, update_values)

    db.commit()

    return jsonify({"message": "Note updated successfully", "status": "success"})