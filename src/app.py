from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .flaskenv
load_dotenv()

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, url_for, session, render_template, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "random secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
oauth = OAuth(app)
socketio = SocketIO(app)
db = SQLAlchemy(app)

# OAuth configuration
google = oauth.register(
    name="google",
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    client_kwargs={"scope": "email profile"},
    redirect_uri="http://127.0.0.1:5000/authorize"
)

# Database model
class Stream(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Stream {self.title}>'

# Routes
@app.route("/")
def home():
    return "Welcome to the Flask OAuth Example"

@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/authorize")
def authorize():
    token = google.authorize_access_token()
    resp = google.get("https://www.googleapis.com/oauth2/v1/userinfo")
    user_info = resp.json()
    session["user"] = user_info
    return f"Hello, {user_info['name']}!"

@app.route("/stream")
def stream():
    return render_template('stream.html')

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)
    emit('response', {'data': data}, broadcast=True)

@app.route('/create_stream', methods=['POST'])
def create_stream():
    title = request.form['title']
    description = request.form['description']
    new_stream = Stream(title=title, description=description)
    db.session.add(new_stream)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    db.create_all()
    socketio.run(app, debug=True)
