from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)

# Configure the database URI based on environment variables or defaults
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hello.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

from app import routes, models, auth

if __name__ == '__main__':
    db.create_all()  # Create all tables in the database
    app.run(debug=True)  # Run the Flask application in debug mode