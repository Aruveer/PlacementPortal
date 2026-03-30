from flask import Flask
from backend.model import db,User 
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///placement.db"
app.config["SECRET_KEY"] = "aruveer"
app.config['UPLOAD_FOLDER'] = 'static/resumes'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all() 
    admin = User.query.filter_by(email="admin@gmail.com").first()
    if not admin:
        admin = User(
            email="admin@gmail.com",
            password="admin123",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

from backend.routes import * 
if __name__ == "__main__":
    app.run(debug=True)