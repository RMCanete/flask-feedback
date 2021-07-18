from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import UserForm, LoginForm, EditUserForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:2118@localhost/users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'asdfghjkl'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)

@app.route('/')
def homepage():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register_user():

    if 'username' in session:
        return redirect(f"/users/{session['username']}")

    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username is already taken, please choose another Username.')
            return render_template('register.html', form=form)

        session['username'] = new_user.username
        flash(f"Welcome!")
        return redirect(f"/users/{new_user.username}")

    return render_template('/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login_user():

    if 'username' in session:
        return redirect(f"users/{session['username']}")

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome back {username}!")
            session['username'] = username
            return redirect(f"/users/{username}")

        else:
            form.username.errors = ['Invalid Credentials']
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)

@app.route('/users/<username>')
def show_user(username):

    if "username" not in session or username !=session['username']:
        flash("Please login")
        return redirect('/login')

    user = User.query.get(username)    
    form = EditUserForm()
    return render_template('show_user.html', user=user, form=form)
        
@app.route('/logout')
def logout_user():
    session.pop('username')
    flash(f"Goodbye!")
    return redirect('/')

@app.route('/users/<username>/delete', methods=["POST"])
def delete_user(username):
    if "username" not in session or username !=session['username']:
        flash("Please login")
        return redirect('/')

    user = User.query.get(username)   
    db.session.delete(user)
    db.session.commit()
    session.pop("username")
    flash("User deleted")
    return redirect('/')

@app.route('/users/<username>/feedback/add', methods=["GET", "POST"])
def add_feedback(username):
    if "username" not in session or username !=session['username']:
        flash("Please login")
        return redirect('/login')

    form=FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(
            title = title,
            content=content,
            username=username)
        db.session.add(feedback)
        db.session.commit()
        return redirect(f"/users/{feedback.username}")

    else:
        return render_template('/add_feedback.html', form=form)

@app.route('/feedback/<feedback_id>/update', methods=["GET", "POST"])
def update_feedback(feedback_id):

    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username !=session['username']:
        flash("Please login")
        return redirect('/login')

    form=FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        return redirect(f"/users/{feedback.username}")

    return render_template('/edit_feedback.html', form=form, feedback=feedback)

@app.route('/feedback/<int:feedback_id>/delete', methods=["POST"])
def delete_feedback(feedback_id):

    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username !=session['username']:
        flash("Please login")
        return redirect('/login')
        
    db.session.delete(feedback)
    db.session.commit()

    return redirect(f"/users/{feedback.username}")