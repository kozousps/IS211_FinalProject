from flask import Flask, render_template, url_for, flash, redirect, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import (LoginManager, login_user, current_user, logout_user,
                         UserMixin, login_required)


app = Flask(__name__)
app.config['SECRET_KEY'] = '24794279fewofs'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(userid))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    post = db.relationship('Post', backref='blogger', lazy=True)

    def __repr__(self):
        return "User('{}')".format(self.username)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.content}', '{self.date}')"


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=5, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=5, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class BlogForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=40)])
    blog = TextAreaField('Blog', validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField('Post')


# posts = [
#     {"blogger": "You",
#      "title": "Your Blog",
#      "content": "For your fun",
#      "date": "04/23/2020"
#      },
#     {"blogger": "You",
#      "title": "Your Diary",
#      "content": "For yourself",
#      "date": "04/22/2020"
#      }
# ]


@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
        posts = Post.query.order_by(Post.date.desc()).all()
        return render_template('home.html', posts=posts)
    else:
        return render_template('home.html')


@app.route('/dashboard')
def dashboard():
    posts = Post.query.order_by(Post.date.desc()).all()
    return render_template('dashboard.html', posts=posts)


@app.route("/register", methods=['GET', 'POST'])
def register():
    regform = RegistrationForm()
    if regform.validate_on_submit():
        user = User(username=regform.username.data,
                    password=regform.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registered!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=regform)


@app.route("/login", methods=['GET', 'POST'])
def login():
    logform = LoginForm()
    if logform.validate_on_submit():
        login = User.query.filter_by(username=logform.username.data).first()
        if login and (login.password == logform.password.data):
            login_user(login)
            flash("Logged In!", 'success')
            return redirect(url_for('home'))
        else:
            flash("Could not log in", 'danger')
    return render_template('login.html', title='Login', form=logform)


@app.route("/logout")
def logout():
    logout_user()
    flash('Logged out', 'success')
    return redirect(url_for('home'))


@app.route("/write", methods=['GET', 'POST'])
def write():
    blogform = BlogForm()
    if blogform.validate_on_submit():
        blog = Post(blogger=current_user, title=blogform.title.data,
                    content=blogform.blog.data
                    )
        db.session.add(blog)
        db.session.commit()
        flash("Blog Posted", 'success')
        return redirect(url_for('home'))
    return render_template('write.html', title='New Post', form=blogform)


@app.route('/edit/<blogid>', methods=['GET', 'POST'])
@login_required
def edit(blogid):
    blog = Post.query.get_or_404(blogid)
    blogid = blog.id
    blogform = BlogForm()
    if request.method == 'POST':
        if blogform.validate_on_submit():
            blog.title = blogform.title.data
            blog.content = blogform.blog.data
            db.session.commit()
            flash('Blog updated', 'success')
            return redirect(url_for('home', blogid=blog.id))
    elif request.method == 'GET':
        blogform.title.data = blog.title
        blogform.blog.data = blog.content
    return render_template('edit.html', title='Edit Post', form=blogform,
                           blogid=blogid)


@app.route('/delete/<blogid>', methods=['POST'])
@login_required
def delete(blogid):
    blog = Post.query.get_or_404(blogid)
    db.session.delete(blog)
    db.session.commit()
    flash('Your post has been deleted', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
