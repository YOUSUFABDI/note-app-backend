from app import app
from dotenv import load_dotenv, dotenv_values
import os

load_dotenv()

port = os.getenv('PORT')

if __name__ == '__main__':
    
    app.run(debug=True, port=port, host='0.0.0.0')