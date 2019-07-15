from flask import Flask,redirect,render_template,request,session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from hashutils import make_pw_hash, check_pw_hash
from datetime import datetime


app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:password@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = False
app.secret_key = "asdfgh"

db = SQLAlchemy(app)



class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120),nullable=False)
    body = db.Column(db.Text)
    date_created = db.Column(db.DateTime)
    private = db.Column(db.Boolean)
    owner = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    def __init__(self,title,body,private,owner):
        self.title = title
        self.body = body
        self.date_created = datetime.now()
        self.private = private
        self.owner = owner

    def __repr__(self):
        return '<Blog %r/>' % self.title

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_name = db.Column(db.String(120),nullable=False,unique=True)
    pw_hash = db.Column(db.String(120),nullable=False)
    email = db.Column(db.String(120),nullable=False,unique=True)
    blog = db.relationship('Blog',backref='User',lazy=True)
    
    def __init__(self,user_name,email,password):
        self.user_name = user_name
        self.pw_hash = make_pw_hash(password)
        self.email = email


class Navbar():
    
    def __init__(self,link,text,active,class_name,l_or_r):
        self.link = link
        self.text = text
        self.active = active
        self.class_name = class_name
        self.l_or_r = l_or_r


def build_bar(active_link):

    active_link = active_link
    links = ['/','/blog','/new-blog','/logout']
    text = ['Users','Blogz','New Blog','Logout']
    class_name = ['users','blog','new_blog','logout']
    l_or_r = ['left','left','left','right']

    nav = []
    for i, link in enumerate(links):
        if link == active_link:
            nav += [Navbar(link,text[i],True,class_name[i],l_or_r[i])]
        else:
            nav += [Navbar(link,text[i],False,class_name[i],l_or_r[i])]
    return nav

@app.before_request
def required_login():
    allowed_routes = ['login_user', 'register_user']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return render_template('login.html')

@app.route('/', methods=["GET"])
def index():
    nav = build_bar('/')
    route = 'users'
    users = User.query.all()
    return render_template('index.html',nav=nav,route=route,users=users)

@app.route('/blog',methods=['GET','POST'])
def blog_page():
    route = 'Blog'
    blogs = Blog.query.filter((Blog.private == False) | (Blog.owner == User.query.filter_by(user_name=session['user']).first().id))
    nav = build_bar('/blog')
    user = User.query.all()
    return render_template('blog.html',blogs=blogs,route=route,nav=nav,User=user)
    #TODO - get blogs render blog page

@app.route('/new-blog',methods=['GET','POST'])
def post_new_blog():
    blogs = ''
    error = ''
    title = ''
    body = ''
    owner = ''
    route = 'new-blog'
    private = False
    
    if request.method =='POST':
        title = request.form['title']
        body = request.form['body']
        #set private
        if request.form['private'] == 'on':
            private = True
        else:
            private = False
        owner = db.session.query(User.id).filter_by(user_name = session['user']).first()
        new_blog = Blog(title,body,private,owner.id)
        if Blog.query.filter_by(title=new_blog.title).first():
            error = 'Blog title already exists'
        elif  not title or not body or not owner:
            error = 'Please make sure that you have a title, and there is content in the body.'
        else:
            db.session.add(new_blog)
            db.session.commit()
            return redirect('/blog')
    nav = build_bar('/new-blog')
    return render_template('newpost.html', error=error,route=route,nav=nav)
    #TODO - make blog post form, that submits then redirect to /blog

@app.route('/<blog>')
def selected_blog(blog):
    route = blog
    blogs = Blog.query.filter_by(title=blog).all()
    nav = build_bar('/blog')
    return render_template('blog.html',blogs=blogs,route=route,nav=nav)

@app.route('/blog/<user_name>')
def selected_user(user_name):
    route = user_name
    if user_name == session['user']:
        blogs = Blog.query.filter_by(owner =User.query.filter_by(user_name=user_name).first().id).all()
    else:
        blogs = Blog.query.filter_by(owner =User.query.filter_by(user_name=user_name).first().id,private=False).all()
    nav = build_bar('blog')
    return render_template('blog.html',blogs=blogs,route=route,nav=nav)

@app.route('/register',methods=['GET','POST'])
def register_user():
    # if request method = post then run
    route = 'register'
    if request.method == 'POST':

        #set user info and verify_password
        user = User(request.form['user_name'],request.form['email'],request.form['password'])
        verify = request.form['verify']
        
        #set error strings
        user_err = ''
        email_err =''
        password_err =''
        verify_err = ''


        # test user data
        if User.query.filter_by(user_name = user.user_name).first():
            user_err = "User name already in use."
        if len(user.user_name) < 3 or len(user.user_name) > 20:
            user_err = "Please input a valid username"
        if User.query.filter_by(email=user.email).first():
            email_err = "Email address already in use."
        if user.email == "":
            email_err = 'Please input an email address'
        if len(request.form['password']) < 3 or len(request.form['password']) > 20:
            password_err = "Please input a valid password"
        if str(request.form['password']) != str(verify):
            verify_err = "Passwords don't match"
        if user_err == "" and email_err == "" and password_err == "" and verify_err == "":
            #if no errors add to database send to login
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
        # else re-render site with errors
        return render_template('register.html',user_name=user.user_name,email=user.email,
        user_err=user_err,email_err=email_err,password_err=password_err,verify_err=verify_err,
        route=route)

    return render_template('register.html')


@app.route('/login',methods=['GET','POST'])
def login_user():
    route = 'login'
    error = ''
    if request.method == 'POST':
        user = User.query.filter_by(user_name=request.form['user_name']).first()
        password = request.form['password']
        if user and check_pw_hash(password,user.pw_hash):
            session['user'] = user.user_name
            return redirect('/blog')
        else:
            error='User name and or password are incorrect'
        
    return render_template('login.html', error=error,route=route)


@app.route('/logout',methods=['GET'])
def logout_user():
    del session['user']
    return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)
