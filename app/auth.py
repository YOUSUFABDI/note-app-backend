from app import app
from flask import request, jsonify, send_from_directory, send_file
import mysql.connector
from dotenv import load_dotenv, dotenv_values
import os
import bcrypt
import random, string
from flask_mail import Message, Mail
from werkzeug.utils import secure_filename

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

    cursor.execute("SELECT image_uri FROM profile_imgs WHERE user_id = %s", (user[0],))
    profile_img = cursor.fetchone()
    if profile_img:
        user_info['profile_image'] = f"http://192.168.1.5:9192/uploads/{profile_img[0]}"
        print("Generated Image URL:", user_info['profile_image'])
    else:
        user_info["profile_image"] = None

    db.commit() 
    
    return jsonify({"message": user_info, "status": "success"})

@app.route('/api/upload/<string:username>', methods=['POST'])
def upload_file(username):
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join('app/uploads', filename))

    cursor = db.cursor()
 
    cursor.execute("SELECT profile_imgs.id, profile_imgs.user_id, profile_imgs.image_uri FROM profile_imgs JOIN users ON profile_imgs.user_id = users.id WHERE users.username = %s", (username ,))
    result = cursor.fetchone()
    user_id = result[1]
    old_image_uri = result[2]
    if result:
        cursor.execute("UPDATE profile_imgs SET image_uri = %s WHERE user_id  = %s", (filename, user_id))

        # delete the old image
        if old_image_uri:
            old_file_path = os.path.join('app/uploads', old_image_uri)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
    else:
        cursor.execute("INSERT INTO profile_imgs (user_id, image_uri) VALUES (%s, %s)", (user_id, filename,))

    db.commit() 

    return jsonify({'success': 'File uploaded successfully'})

# Add a new endpoint to serve images
@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_file(os.path.join('uploads', filename))


# Forgot password api's
@app.route('/api/forgot_password', methods=["POST"])
def forgot_password():
    gmail = request.json.get("gmail")

    cursor = db.cursor()

    # check if gmail is already taken
    cursor.execute("SELECT * FROM users WHERE gmail = %s", (gmail,))
    isGmail = cursor.fetchone()
    if not isGmail:
        return jsonify({"message": "Gmail not found", "status": "error"})
    
    # Generate OTP code
    otp_code = ''.join(random.choices(string.digits, k=4))

    # Store OTP code in the DB
    cursor.execute("DELETE FROM forgot_pass WHERE gmail = %s", (gmail,))
    cursor.execute("INSERT INTO forgot_pass (gmail, otp_code) VALUES (%s, %s)", (gmail, otp_code))

    # Send OTP code as gmail to check if user belongs the gmail
    subject = 'Password reset OTP Note Taker App!'
    body = f'Your OTP code for password reset is: {otp_code}'
    sender = os.getenv('MAIL_DEFAULT_SENDER')
    message = Message(subject=subject, body=body, recipients=[gmail], sender=sender)
    mail.send(message)

    db.commit()

    return jsonify({"message": "Send Password reset OTP code successfully", "status": "success"})

# Verifies reset OTP code
@app.route('/api/verify_reset_otp', methods=["POST"])
def verify_reset_otp():
    gmail = request.json.get('gmail')
    otp_code = request.json.get('otp_code')

    cursor = db.cursor()

    cursor.execute('SELECT * FROM forgot_pass WHERE gmail = %s AND otp_code = %s', (gmail, otp_code))
    result = cursor.fetchone()

    # Remove the entry from the OTP table
    cursor.execute("DELETE FROM forgot_pass WHERE gmail = %s", (gmail,))

    db.commit()

    if not result:
        return jsonify({"message": "Invalid OTP code", "status": "error"})
    else:
        return jsonify({"message": "Success valid OTP", "status": "success"})

@app.route('/api/reset_password', methods=["POST"])
def reset_password():
    new_password = request.json.get("new_password")
    gmail = request.json.get('gmail')

    cursor = db.cursor()

    # Check if gmail exists
    cursor.execute("SELECT * FROM users WHERE gmail = %s", (gmail,))
    isGmail = cursor.fetchone()
    if not isGmail:
        return jsonify({"message": "Gmail not found", "status": "error"})

    # Hash the password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute('UPDATE users SET password = %s WHERE gmail = %s', (hashed_password, gmail))

    db.commit()

    return jsonify({"message": "Password changed successfully", "status": "success"})