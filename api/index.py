from flask import Flask, jsonify, request
import mysql.connector
from dotenv import load_dotenv, dotenv_values
import os
import bcrypt
import random, string
from flask_mail import Message, Mail

app = Flask(__name__)

# DB connection
db_host = "srv1241.hstgr.io"
db_username = "u708286975_yusuf"
db_password = "+C3qHb1GkQ3^"
db_name = "u708286975_noteTakerDB"

db = mysql.connector.connect(host=db_host, username=db_username, password=db_password, database=db_name)

@app.route('/')
def home():
    return jsonify({"message" :'Hello, World!'})

@app.route('/notes', methods=['GET'])
def notes():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notes")
    rows = cursor.fetchall()
    return jsonify(rows)