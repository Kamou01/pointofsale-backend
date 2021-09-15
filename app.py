import hmac
import sqlite3

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS


# This function create dictionaries out of SQL rows, so that the data follows JSON format
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class user_info(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def fetch_users():
    with sqlite3.connect('pointofsale.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(user_info(data[0], data[3], data[4]))
    return new_data


def init_usertable():
    conn = sqlite3.connect('pointofsale.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")

    conn.commit()
    print("user table created successfully.")


init_usertable()
users = fetch_users()

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return username_table.get(user_id, None)


def products_table():
    with sqlite3.connect('pointofsale.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "description TEXT NOT NULL,"
                     "category TEXT NOT NULL,"
                     "image TEXT NOT NULL)")
        print("products table create successfully.")


init_usertable()
products_table()

users = fetch_users()


app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = 'super-secret'

jwt = JWT(app, authenticate, identity)
CORS(app)


@app.route('/protected')
@jwt_required
def protected():
    return '%s' % current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        username = request.json['username']
        password = request.json['password']

        print(first_name, username, password, last_name)

        with sqlite3.connect('pointofsale.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user("
                           "first_name,"
                           "last_name,"
                           "username,"
                           "password) VALUES(?, ?, ?, ?)", (first_name, last_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201

    return response


#   Route for the user to login.
@app.route("/user_login/", methods=["POST"])
#   Function to register user
def user_login():
    response = {}

    if request.method == "POST":
        entered_username = request.json['username']
        entered_password = request.json['password']

        with sqlite3.connect("pointofsale.db") as connection:

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM user WHERE username=? AND password=?", (entered_username,
                                                                                   entered_password))
            table_info = cursor.fetchone()

            response["status_code"] = 200
            response["message"] = "User logged in successfully"
            response["user"] = table_info
        return response

    else:
        response["status_code"] = 404
        response["user"] = "user not found"
        response["message"] = "User logged in unsuccessfully"
    return response


@app.route('/adding_product/', methods=["POST"])
def add_products():
    response = {}

    if request.method == "POST":
        name = request.json['name']
        price = request.json['price']
        description = request.json['description']
        category = request.json['category']
        image = request.json['image']

        with sqlite3.connect('pointofsale.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO products("
                               "name,"
                               "price,"
                               "description,"
                               "category,"
                               "image) VALUES(?, ?, ?, ?, ?)", (name, price, description, category, image))
                conn.commit()
                response["status_code"] = 201
                response['description'] = "Product added successfully"
        return response


@app.route('/delete_product/<int:product_id>/')
def delete_products(product_id):
    response = {}

    with sqlite3.connect('pointofsale.db') as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products WHERE id=" + str(product_id))
        connection.commit()
        response['status code'] = 200
        response['message'] = "Product deleted."
    return response


@app.route('/view_products/', methods=["GET"])
def view_products():
    response = {}
    if request.method == "GET":
        with sqlite3.connect('pointofsale.db') as conn:
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM products')
            conn.commit()

            products = cursor.fetchall()
            response["status_code"] = 201
            response["products"] = products
            response['description'] = "Here are the products"

    return response


@app.route('/updating_product/<int:id>/', methods=["PUT"])
def update_products(id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('pointofsale.db') as conn:
            print(request.json)
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")

                with sqlite3.connect('pointofsale.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE products SET name =? WHERE id", (put_data["name"], id))

                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200

            elif incoming_data.get("price") is not None:
                put_data["price"] = incoming_data.get("price")

                with sqlite3.connect('pointofsale.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE products SET price =? WHERE id =?", (put_data["price"], id))

                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200

            elif incoming_data.get("description") is not None:
                put_data["description"] = incoming_data.get("description")

                with sqlite3.connect('pointofsale.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE products SET description =? WHERE id", (put_data["description"], id))

                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200

            elif incoming_data.get("category") is not None:
                put_data["category"] = incoming_data.get("category")

                with sqlite3.connect('pointofsale.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE products SET category =? WHERE id", (put_data["category"], id))
                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200

            elif incoming_data.get("image") is not None:
                put_data["image"] = incoming_data.get("image")

                with sqlite3.connect('pointofsale.db') as connection:
                    cursor = connection.cursor()
                    cursor.execute("UPDATE products SET image =? WHERE id", (put_data["image"], id))
                    conn.commit()
                    response['message'] = "Update was successful"
                    response['status_code'] = 200
    return response


@app.route('/view_product/<int:product_id>')
def view_product(product_id):
    response = {}

    with sqlite3.connect('pointofsale.db') as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id =? ', (str(product_id),))
        product = cursor.fetchone()
        conn.commit()

        response['status code'] = 201
        response['description'] = "Here is the selected product"
        response['data'] = product

    return response


if __name__ == '__main__':
    app.run()
