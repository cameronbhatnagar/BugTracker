# FLASK Tutorial 1 -- We show the bare bones code to get an app up and running

# imports
import os                 # os is used to get environment variables IP & PORT
from flask import Flask   # Flask is the web app that we will customize
from flask import render_template
from flask import request
from flask import redirect, url_for
from database import db
from models import Note as Note
from models import User as User
from forms import RegisterForm
from flask import session
import bcrypt
from forms import LoginForm
from models import Comment as Comment
from forms import RegisterForm, LoginForm, CommentForm

app = Flask(__name__)     # create an app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_note_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
#  Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# Setup models
with app.app_context():
    db.create_all()   # run under the app context

# @app.route is a decorator. It gives the function "index" special powers.
# In this case it makes it so anyone going to "your-url/" makes this function
# get called. What it returns is what is shown as the web page


@app.route('/')
@app.route('/index')
def index():
    if session.get('user'):
        return render_template("index.html", user=session['user'])
    return render_template('index.html')


@app.route('/notes')
def get_notes():
    if session.get('user'):
        my_notes = db.session.query(Note).filter_by(user_id=session['user_id']).all()
        return render_template('notes.html', notes=my_notes, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/notes/<note_id>')
def get_note(note_id):
    if session.get('user'):
        my_note = db.session.query(Note).filter_by(id=note_id).one()

        form = CommentForm()

        return render_template('note.html', note = my_note, user = session['user'], form=form)
    else:
        return render_template('login')


@app.route('/notes/new', methods=['GET', 'POST'])
def new_note():

    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['noteText']
            from datetime import date
            today = date.today()
            today = today.strftime("%m-%d-%Y")
            new_record = Note(title, text, today, session['user_id'])
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('get_notes', user = session['user']))
        else:
            return render_template('new.html', user = session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/notes/edit/<note_id>', methods=['GET', 'POST'])
def update_note(note_id):
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['noteText']
            note = db.session.query(Note).filter_by(id=note_id).one()
            note.title = title
            note.text = text
            db.session.add(note)
            db.session.commit()
            return redirect(url_for('get_notes', note_id=note_id))
        else:
            my_note = db.session.query(Note).filter_by(id=note_id).one()

            return render_template('new.html', note=my_note, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/notes/delete/<note_id>', methods=['POST'])
def delete_note(note_id):
    if session.get('user'):
        my_note = db.session.query(Note).filter_by(id=note_id).one()
        db.session.delete(my_note)
        db.session.commit()
        return redirect(url_for('get_notes'))
    else:
        return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        password_hash = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        new_record = User(first_name, last_name, request.form['email'], password_hash)
        db.session.add(new_record)
        db.session.commit()
        session['user'] = first_name
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        session['user_id'] = the_user.id

        return redirect(url_for('get_notes'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    # validate_on_submit only validates using POST
    if login_form.validate_on_submit():
        # we know user exists. We can use one()
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # user exists check password entered matches stored password
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):
            # password match add user info to session
            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            # render view
            return redirect(url_for('get_notes'))

        # password check failed
        # set error message to alert user
        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        # form did not validate or GET request
        return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    if session.get('user'):
        session.clear()
    return redirect(url_for('index'))


@app.route('/notes/<note_id>/comment', methods=['POST'])
def new_comment(note_id):
    if session.get('user'):
        comment_form = CommentForm()
        # validate_on_submit only validates using POST
        if comment_form.validate_on_submit():
            # get comment data
            comment_text = request.form['comment']
            new_record = Comment(comment_text, int(note_id), session['user_id'])
            db.session.add(new_record)
            db.session.commit()

        return redirect(url_for('get_note', note_id=note_id))

    else:
        return redirect(url_for('login'))


@app.route('/notes/delete/<note_id>/<comment_id>', methods=['POST'])
def delete_comment(note_id, comment_id):
    if session.get('user'):
        my_comment = db.session.query(Comment).filter_by(id=comment_id).one()
        db.session.delete(my_comment)
        db.session.commit()
        return redirect(url_for('get_note', note_id=note_id))
    else:
        return redirect(url_for('login'))


@app.route('/notes/edit/<note_id>/<comment_id>', methods=['GET', 'POST'])
def update_comment(note_id, comment_id):
    if session.get('user'):
        if request.method == 'POST':
            comment_text = request.form['comment']
            comment = db.session.query(Comment).filter_by(id=comment_id).one()
            comment.content = comment_text
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for('get_note', note_id=note_id))
        else:
            my_note = db.session.query(Note).filter_by(id=note_id).one()
            my_comment = db.session.query(Comment).filter_by(id=comment_id).one()

            return render_template("edit_comment.html", note=my_note, comment=my_comment, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/notes/<note_id>/rate', methods=['POST'])
def rate_note(note_id):
    if session.get('user'):
        if request.method == 'POST':
            rate = request.form['rating']
            note = db.session.query(Note).filter_by(id=note_id).one()
            note.rate = rate
            db.session.add(note)
            db.session.commit()
            return redirect(url_for('get_note', note_id=note_id))
    else:
        return redirect(url_for('login'))


@app.route('/notes/sort/title')
def sort_notes_title():
    if session.get('user'):
        my_notes = db.session.query(Note).filter_by(user_id=session['user_id']).order_by(Note.title).all()
        return render_template('notes.html', notes=my_notes, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/notes/sort/date')
def sort_notes_date():
    if session.get('user'):
        my_notes = db.session.query(Note).filter_by(user_id=session['user_id']).order_by(Note.date).all()
        return render_template('notes.html', notes=my_notes, user=session['user'])
    else:
        return redirect(url_for('login'))


app.run(host=os.getenv('IP', '127.0.0.1'),port=int(os.getenv('PORT', 5000)),debug=True)
app.config['SECRET_KEY'] = 'SE3155'

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000

# Note that we are running with "debug=True", so if you make changes and save it
# the server will automatically update. This is great for development but is a
# security risk for production.
