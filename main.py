from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import werkzeug
import json
import os

from werkzeug.utils import secure_filename

with open("config.json","r") as json_file:
    params = json.load(json_file)['params']

local = True
app = Flask(__name__)
app.secret_key = ""
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER="smtp.sendgrid.net",
    MAIL_PORT=587,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)
if (local):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_server']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_server']

#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/thedevopguy"
db = SQLAlchemy(app)

class User(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(80), unique=False, nullable=False)
    lastname = db.Column(db.String(80), unique=False, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    address = db.Column(db.String(200), unique=True, nullable=False)
    country = db.Column(db.String(80), unique=False, nullable=False)
    state = db.Column(db.String(80), unique=False, nullable=False)
    number = db.Column(db.Integer, unique=True, nullable=False)

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=False, nullable=False)
    title = db.Column(db.String(100), unique=False, nullable=False)
    content = db.Column(db.String(2000), unique=True, nullable=False)
    date = db.Column(db.String(20), unique=True, nullable=False)

@app.route("/")
def main():
    posts = Posts.query.order_by(Posts.date)[0:params['number_of_posts']]

    page = request.args.get('page', 1, type=int)  # get ?page= from URL
    per_page = 4  # number of posts per page

    pagination = Posts.query.paginate(page=page, per_page=per_page)
    posts = pagination.items

    return render_template("jinja.html",params = params,posts=posts, pagination=pagination)

@app.route("/uploader", methods=["GET", "POST"])
def upload():
    if 'username' in session and session['username'] == params['admin_user']:
        if request.method == "POST":
            f = request.files["myfile"]
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Upload Success"

    posts = Posts.query.filter_by().all()[0:params['number_of_posts']]
    return render_template('admin.html', params=params, posts=posts)


@app.route("/admin",methods=["POST","GET"])
def admin():

#    if 'username' in session and session['username'] == params['admin_user']:
#        posts = Posts.query.filter_by().all()[0:params['number_of_posts']]
#         return render_template('admin.html', params=params,posts=posts)

    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username == params['admin_user'] and password == params['admin_password']:
            session['username'] = params['admin_user']
            posts = Posts.query.filter_by().all()[0:params['number_of_posts']]
            return render_template('admin.html', params=params,posts=posts)
    else:
        pass

    return render_template('sign.html')

@app.route("/post/<slug>", methods=["GET"])
def post_route(slug):
#    return f"This is my first slug: {slug}"
    post = Posts.query.filter_by(slug=slug).first()
    return render_template('post.html',params = params,post = post)

@app.route("/about")
def about():
    return render_template('about.html',params = params)

@app.route("/logout")
def logout():
    session.pop('username')
    return redirect("/admin")

@app.route("/delete/<string:id>")
def delete(id):
    if 'username' in session and session['username'] == params['admin_user']:
        db.session.delete(Posts.query.filter_by(id=id).first())
        db.session.commit()
    return redirect("/admin")

@app.route("/contact",methods=["GET","POST"])
def contact():
    if request.method == "POST":
        firstname = request.form.get("fname")
        lastname = request.form.get("lname")
        username = request.form.get("uname")
        email = request.form.get("email")
        address = request.form.get("address")
        country = request.form.get("country")
        state = request.form.get("state")
        number = request.form.get("number")

        entry = User(firstname=firstname, lastname=lastname, username=username, email=email, address=address,country=country,state=state,number=number)
        db.session.add(entry)
        db.session.commit()
        # Integrate celery and process the mail async
        mail.send_message(sender=email, recipients=params['gmail-user'],
                          body=f'Hello {firstname} {lastname}!',
                          subject=f'Hello {firstname} {lastname}!')
    return render_template('contact.html',params = params)

app.run(debug=True)
