import math

from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail
from werkzeug.datastructures import  FileStorage

app = Flask(__name__)
app.secret_key = 'super-secret-key'

with open('static/config.json','r') as c:
    params = json.load(c)["params"]

local_server = True
app.config['UPLOAD_FOLDER'] = params['upload_location']

app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    '''
    sno, name, email_addr, phone_num, message, data_time
    '''
    sno: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=False, nullable=True)
    email_addr: Mapped[str] = mapped_column(String, nullable=True)
    phone_num: Mapped[str] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(String, nullable=True)
    date_time: Mapped[str] = mapped_column(String, nullable=True)


class Posts(db.Model):
    '''
    sno, title, tag_line, slug, content, img_file, date_time, created_by
    '''
    sno: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    tag_line: Mapped[str] = mapped_column(String, nullable=True)
    slug: Mapped[str] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(String, nullable=True)
    img_file: Mapped[str] = mapped_column(String, nullable=True)
    date_time: Mapped[str] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String, nullable=True)


@app.route("/")
def home():
    # flash("Subscribe my blog","success")
    # flash("like my video","danger")
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]
    last = math.ceil(len(posts)/params['no_of_posts'])
    # Pagination Logic
    page = request.args.get('page')
    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    # First Page
    if page == 1:
        prev = "#"
        next1 = "/?page=" + str(page + 1)
    elif page == last:
        # Last
        prev = "/?page=" + str(page - 1)
        next1 = "#"
    else:
        # Middle
        prev = "/?page=" + str(page - 1)
        next1 = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts = posts, prev=prev, next=next1)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)



@app.route("/about")
def about():
    return render_template("about.html", params=params)

@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['uplfile']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            flash("Uploaded Successfully","success")
            return redirect("/dashboard")
    else:
        return render_template("login.html", params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_tag_line = request.form.get('tag_line')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            box_image_file = request.form.get('image_file')
            box_created_by = request.form.get('created_by')


            if sno=='0':
                if box_title is not None and box_tag_line is not None and box_slug is not None and box_content is not None and box_image_file is not None and box_created_by is not None:
                    post = Posts(title=box_title, tag_line=box_tag_line, slug=box_slug, content=box_content, img_file = box_image_file, date_time=datetime.now(), created_by = box_created_by)
                    db.session.add(post)
                    db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = box_title
                post.tag_line=box_tag_line
                post.slug = box_slug,
                post.content = box_content
                post.img_file = box_image_file
                post.created_by = box_created_by
                post.date_time=datetime.now()
                db.session.commit()
                return redirect('/edit/' + sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html", params=params, post=post,sno=sno)
    else:
        return redirect("/dashboard")


@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)
    else:
        if request.method == 'POST':
            # Redirect to Admin Panel
            username = request.form.get("uname")
            userpass = request.form.get("password")
            if (username == params['admin_user'] and userpass == params['admin_password']):
                # Set the session variable
                session['user'] = username
                posts = Posts.query.all()
                return render_template("dashboard.html", params=params, posts=posts)
    return render_template("login.html", params=params)


# @app.route("/post")
# def post_route(post_slug):
#     return render_template("post.html", params=params)




@app.route("/contact", methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, email_addr=email, phone_num=phone, message=message, date_time=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail_user']],
                          body = message + "\n" + phone
                          )
        flash("Thanks for submitting your details. We will get back to you soon.", "success")
        flash("Error sending message!","danger")

    return render_template("contact.html", params=params)


app.run(debug=True)