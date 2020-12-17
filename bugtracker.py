# imports
import os
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for
from database import db
from models import Project as Project
from models import User as User
from forms import RegisterForm
from flask import session
import bcrypt
from forms import LoginForm
from models import Bug as Bug
from forms import RegisterForm, LoginForm, BugForm

# Creates the application
app = Flask(__name__)

# Sets up the databases
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask_project_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

# Binds DB to the app
db.init_app(app)

# Setup models
with app.app_context():
    db.create_all()

#
# Homepage/ Index
#
@app.route('/')
@app.route('/index')
def index():
    if session.get('user'):
        return render_template("index.html", user=session['user'])
    return render_template('index.html')

@app.route('/projects')
def get_projects():
    if session.get('user'):
        my_projects = db.session.query(Project).filter_by(user_id=session['user_id']).all()
        return render_template('projects.html', projects=my_projects, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/<project_id>')
def get_project(project_id):
    if session.get('user'):
        my_project = db.session.query(Project).filter_by(id=project_id).one()

        form = BugForm()

        return render_template('project.html', project = my_project, user = session['user'], form=form)
    else:
        return render_template('login')


@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():

    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['projectText']
            from datetime import date
            today = date.today()
            today = today.strftime("%m-%d-%Y")
            new_record = Project(title, text, today, session['user_id'])
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('get_projects', user = session['user']))
        else:
            return render_template('new.html', user = session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/edit/<project_id>', methods=['GET', 'POST'])
def update_project(project_id):
    if session.get('user'):
        if request.method == 'POST':
            title = request.form['title']
            text = request.form['projectText']
            project = db.session.query(Project).filter_by(id=project_id).one()
            project.title = title
            project.text = text
            db.session.add(project)
            db.session.commit()
            return redirect(url_for('get_projects', project_id=project_id))
        else:
            my_project = db.session.query(Project).filter_by(id=project_id).one()

            return render_template('new.html', project=my_project, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    if session.get('user'):
        my_project = db.session.query(Project).filter_by(id=project_id).one()
        db.session.delete(my_project)
        db.session.commit()
        return redirect(url_for('get_projects'))
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

        return redirect(url_for('get_projects'))
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
            return redirect(url_for('get_projects'))

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


@app.route('/projects/<project_id>/bug', methods=['POST'])
def new_bug(project_id):
    if session.get('user'):
        bug_form = BugForm()
        # validate_on_submit only validates using POST
        if bug_form.validate_on_submit():
            # get bug data
            bug_text = request.form['bug']
            new_record = Bug(bug_text, int(project_id), session['user_id'])
            db.session.add(new_record)
            db.session.commit()

        return redirect(url_for('get_project', project_id=project_id))

    else:
        return redirect(url_for('login'))


@app.route('/projects/delete/<project_id>/<bug_id>', methods=['POST'])
def delete_bug(project_id, bug_id):
    if session.get('user'):
        my_bug = db.session.query(Bug).filter_by(id=bug_id).one()
        db.session.delete(my_bug)
        db.session.commit()
        return redirect(url_for('get_project', project_id=project_id))
    else:
        return redirect(url_for('login'))


@app.route('/projects/edit/<project_id>/<bug_id>', methods=['GET', 'POST'])
def update_bug(project_id, bug_id):
    if session.get('user'):
        if request.method == 'POST':
            bug_text = request.form['bug']
            bug = db.session.query(Bug).filter_by(id=bug_id).one()
            bug.content = bug_text
            db.session.add(bug)
            db.session.commit()
            return redirect(url_for('get_project', project_id=project_id))
        else:
            my_project = db.session.query(Project).filter_by(id=project_id).one()
            my_bug = db.session.query(Bug).filter_by(id=bug_id).one()

            return render_template("edit_bug.html", project=my_project, bug=my_bug, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/<project_id>/rate', methods=['POST'])
def rate_project(project_id):
    if session.get('user'):
        if request.method == 'POST':
            rate = request.form['rating']
            project = db.session.query(Project).filter_by(id=project_id).one()
            project.rate = rate
            db.session.add(project)
            db.session.commit()
            return redirect(url_for('get_project', project_id=project_id))
    else:
        return redirect(url_for('login'))


@app.route('/projects/sort/title')
def sort_projects_title():
    if session.get('user'):
        my_projects = db.session.query(Project).filter_by(user_id=session['user_id']).order_by(Project.title).all()
        return render_template('projects.html', projects=my_projects, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/projects/sort/date')
def sort_projects_date():
    if session.get('user'):
        my_projects = db.session.query(Project).filter_by(user_id=session['user_id']).order_by(Project.date).all()
        return render_template('projects.html', projects=my_projects, user=session['user'])
    else:
        return redirect(url_for('login'))


app.run(host=os.getenv('IP', '127.0.0.1'),port=int(os.getenv('PORT', 5000)),debug=True)
app.config['SECRET_KEY'] = 'SE3155'

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000

# Project that we are running with "debug=True", so if you make changes and save it
# the server will automatically update. This is great for development but is a
# security risk for production.
