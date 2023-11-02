"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# validacion de los password 
def set_password(password):
    return generate_password_hash(password)


def check_password(hash_password, password):
    return check_password_hash(hash_password, password)


# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


@app.route("/user", methods=["POST"])
def add_user():
    body = request.json

    email = body.get("email")
    password= body.get("password")



    if email is None or password is None:
        return jsonify({"message": "You need and email a password"}), 400

    
    # vadamos que el usuario no exista y es un usuario nuevo nuevo
    user = User.query.filter_by(email=email).one_or_none()

    if user is not None:
        return jsonify({"message": "user exists"}), 400

    else:
        password = set_password(password)
        user = User(email=email, password=password)
        db.session.add(user)

        try:
            db.session.commit()
            return jsonify({"message":"user created"}), 201
        except Exception as error:
            print(error)
            db.session.rollback()
            return jsonify({"message": f"error: {error}" }) 

    return jsonify([]), 200



@app.route("/login", methods=["POST"])
def handle_login():
    body = request.json

    email = body.get("email")
    password= body.get("password")

    if email is None or password is None:
        return jsonify({"message": "You need and email a password"}), 400
    
    else:
        user = User.query.filter_by(email=email).one_or_none()

        if user is None:
            return jsonify({"message":"Bad credentials"}), 400
        else:
            if check_password(user.password, password):
                # debemos crear el token y responderlo
                return jsonify({"message":"exitooooo"}), 200
            else:
                return jsonify({"message":"Bad credentials"}), 400





# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
