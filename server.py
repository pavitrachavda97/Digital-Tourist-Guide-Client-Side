import base64
import io
import numpy as np
from PIL import Image
from feature_extractor import FeatureExtractor
from datetime import datetime
from flask import Flask, request, render_template, session
from pathlib import Path
import mysql.connector
from pathlib import WindowsPath
import os

app = Flask(__name__)
app.secret_key = 'gs_project'

fe = FeatureExtractor()
features = []
img_paths = []
for feature_path in Path("./static/feature").glob("*.npy"):
    features.append(np.load(feature_path))
    img_paths.append(Path("./static/img") / (feature_path.stem + ".jpg"))

features = np.array(features)

# initial run
@app.route("/")

def index():
    if request.method == "POST":
        return render_template("index.html")
    else:
        return render_template("index.html")

@app.route("/index.html")

def home():
    if request.method == "POST":
        return render_template("index.html")
    else:
        return render_template("index.html")
    
# find place by image
@app.route("/find.html", methods=["GET", "POST"])

def find():
    return render_template("find.html")
    
@app.route("/search", methods=["GET", "POST"])

def search():
    if request.method == "POST":
        data = request.get_json()
        image_data = data['image']
        # processing the image data
        img = Image.open(io.BytesIO(base64.b64decode(image_data.split(',')[1])))

        if img.mode == 'RGBA':
            img = img.convert('RGB')
            
        # save image to uploaded folder to compare image
        uploaded_img_path = "static/uploaded/" + datetime.now().isoformat().replace(":", ".") + "_.jpg"
        img.save(uploaded_img_path)

        query = fe.extract(img)
        dists = np.linalg.norm(features-query, axis=1)
        ids = np.argsort(dists)[:1]
        scores = [(dists[id], img_paths[id]) for id in ids]

        # for file name from database
        filename = scores[0][1].name
        p_name = os.path.splitext(filename)[0]

        conn = mysql.connector.connect(host="localhost", user="root", password="root_123", database="gs")
        cursor = conn.cursor()

        sql1 = "SELECT * FROM place WHERE p_name LIKE %(search_query1)s"
        search_query1 = '%' + p_name + '%'
        cursor.execute(sql1, {"search_query1": search_query1})
        results1 = cursor.fetchall()

        found1 = False
        data1 = []
        if(len(results1) > 0):
            found1 = True
            for result in results1:
                data1.append(result[1])
                data1.append(result[2])
                data1.append(result[3])
                data1.append(result[4])
        else:
            found1 = False

        sql2 = "SELECT * FROM item WHERE location LIKE %(search_query2)s"
        search_query2 = '%' + p_name + '%'
        cursor.execute(sql2, {"search_query2": search_query2})
        results2 = cursor.fetchall()

        found2 = False
        data2 = []
        if(len(results2) > 0):
            found2 = True
            for result in results2:
                info = []
                info.append(result[2])
                info.append(result[3])
                data2.append(info)
        else:
            found2 = False

        cursor.close()
        conn.close()

        return render_template("find.html", found1=found1, data1=data1, found2=found2, data2=data2, scores=scores)
        # return render_template("find.html", query_path=uploaded_img_path, scores=scores)
    else:
        return render_template("find.html")

# request to add item to database
@app.route("/addItem.html", methods=["GET", "POST"])

def addItem():
    # return render_template("addItem.html")
    if 'user_id' in session:
        return render_template("addItem.html")
    else:
        return render_template("login.html")

@app.route("/submit", methods=["GET", "POST"])

def submit():
    if request.method == "POST":
        location = request.form['location']
        name = request.form['name']
        description = request.form['description']

        addItemToDatabase(location, name, description)

        return render_template("addItem.html")
    else:
        return render_template("addItem.html")

def addItemToDatabase(location, name, description):
    cnx = mysql.connector.connect(host='localhost', database='gs', user='root', password='root_123')
    cursor = cnx.cursor()

    query = "INSERT INTO add_item(location, i_name, i_description) VALUES (%s, %s, %s)"
    values = (location, name, description)
    cursor.execute(query, values)

    cnx.commit()
    cursor.close()
    cnx.close()

# request to add place to database
@app.route("/addPlace.html", methods=["GET", "POST"])

def addPlace():
    # return render_template("addPlace.html")
    if 'user_id' in session:
        return render_template("addPlace.html")
    else:
        return render_template("login.html")

@app.route("/place", methods=["GET", "POST"])

def place():
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']

        addPlaceToDatabase(name, description)        

        return render_template("addPlace.html")
    else:
        return render_template("addPlace.html")

def addPlaceToDatabase(name, description):
    cnx = mysql.connector.connect(host='localhost', database='gs', user='root', password='root_123')
    cursor = cnx.cursor()

    query = "INSERT INTO add_place(p_name, p_description) VALUES (%s, %s)"
    values = (name, description)
    cursor.execute(query, values)

    cnx.commit()
    cursor.close()
    cnx.close()

# for registration in website
@app.route("/registration.html", methods=["GET", "POST"])

def registration():
    return render_template("registration.html")

@app.route('/register', methods=['GET','POST'])

def register():
    mydb = mysql.connector.connect(host="localhost", user="root", password="root_123", database="gs")
    mycursor = mydb.cursor()
    # Collect user input
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    # Validate user input
    while len(password) < 8 or password != confirm_password:
        return "Your password must be at least 8 characters long and match the confirmation."
    
    # Insert registration details into database
    sql = "INSERT INTO user (username, email, password) VALUES (%s, %s, %s)"
    val = (name, email, password)
    mycursor.execute(sql, val)

    mydb.commit()

    # Print registration details
    return render_template("registration.html")

# to login in website
@app.route("/login.html", methods=["GET", "POST"])

def login():
    if 'user_id' in session:
        session.clear()
        return render_template("index.html")
    else:
        return render_template("login.html")

@app.route('/login', methods=['GET','POST'])

def logIn():
    mydb = mysql.connector.connect(host="localhost", user="root", password="root_123", database="gs")
    mycursor = mydb.cursor()
    if request.method == 'POST':
        # Collect user input
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Find user in the database
        sql = "SELECT * FROM user WHERE username = %s AND email = %s AND password = %s"
        val = (username, email, password)
        mycursor.execute(sql, val)
        user = mycursor.fetchone()

        # Validate user input
        if user is None:
            return "User not found."
        elif password != user[3]:
            return "Incorrect password."
        else:
            # Set user session
            session['user_id'] = user[0]
            print("Session is created :: ", session['user_id'])
        return render_template('index.html')
    else:
        print("Session is not created")
        return render_template('login.html')

# to run main server
if __name__ == "__main__":
    app.run()