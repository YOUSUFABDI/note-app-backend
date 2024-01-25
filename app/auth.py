from app import app
from flask import request, jsonify
import mysql.connector
from dotenv import load_dotenv, dotenv_values
import os
import bcrypt
import random, string
from flask_mail import Message, Mail

load_dotenv()

mail = Mail(app)

# DB connection
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

db = mysql.connector.connect(host=db_host, port=db_port, username=db_username, password=db_password, database=db_name)

@app.route('/api/register', methods=['POST'])
def register():
    full_name = request.json.get('full_name')
    age = request.json.get('age')
    address = request.json.get('address')
    gmail = request.json.get('gmail')
    username = request.json.get('username')
    password = request.json.get('password')
    phone_number = request.json.get('phone_number')

    cursor = db.cursor()

    # check if username is already taken
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    isUsername = cursor.fetchone()
    if isUsername:
        return jsonify({"message": "Username already exists", "status": "error"})

    # check if phone is already taken
    cursor.execute("SELECT * FROM users WHERE phone_number = %s", (phone_number,))
    isPhone = cursor.fetchone()
    if isPhone:
        return jsonify({"message": "Phone already exists", "status": "error"})

    # check if gmail is already taken
    cursor.execute("SELECT * FROM users WHERE gmail = %s", (gmail,))
    isGmail = cursor.fetchone()
    if isGmail:
        return jsonify({"message": "Gmail already exists", "status": "error"})

    # hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Generate OTP code
    otp_code = ''.join(random.choices(string.digits, k=4))

    # register user
    cursor.execute("DELETE FROM otp_codes WHERE gmail = %s", (gmail,))
    cursor.execute("INSERT INTO otp_codes (full_name, age, address, gmail, username, password, otp_code, phone_number) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (full_name, age, address, gmail, username, hashed_password, otp_code, phone_number))

    # send otp code to check gmail exists
    subject = 'Welcome to Note Taker App!'
    body = f'Your OTP code is: {otp_code}'
    sender = os.getenv('MAIL_DEFAULT_SENDER')
    message = Message(subject=subject, body=body, recipients=[gmail], sender=sender)
    mail.send(message)

    db.commit()

    return jsonify({"message": "success 🥳", "status": "success"})


@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    gmail = request.json.get('gmail')
    otp_code = request.json.get('otp_code')

    cursor = db.cursor()

    # verify otp code
    cursor.execute("SELECT * FROM otp_codes WHERE gmail = %s AND otp_code = %s", (gmail, otp_code))
    userData = cursor.fetchone()
    if userData:
        columns = [column[0] for column in cursor.description]
        user_data_dict = dict(zip(columns, userData))
        
        cursor.execute("INSERT INTO users (full_name, age, address, gmail, username, password, phone_number) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (user_data_dict['full_name'], user_data_dict['age'], user_data_dict['address'], user_data_dict['gmail'], user_data_dict['username'], user_data_dict['password'], user_data_dict['phone_number']))

        cursor.execute("DELETE FROM otp_codes WHERE gmail = %s", (gmail,))

        db.commit()

        return jsonify({"message": "User registered successfully", "status": "success"})
    else:
        return jsonify({"message": "Invalid OTP code", "status": "error"})
        

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get("password")

    cursor = db.cursor()

    # check if username and password are correct
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[6].encode('utf-8')):
        db.commit()

        return jsonify({"message": "logged in succesfuly", "status": "success"})
    else:
        return jsonify({"message": "Invalid username or password", "status": "error"})

@app.route('/api/get_user', methods=['POST'])
def get_user():
    username = request.json.get('username')

    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "User not found", "status": "error"})

    user_info = {
        "id": user[0],
        "full_name": user[1],
        "age": user[2],
        "address": user[3],
        "gmail": user[4],
        "username": user[5],
        "phone_number": user[7]
    }

    db.commit() 
    
    return jsonify({"message": user_info, "status": "success"})