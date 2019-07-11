from flask import Flask,redirect,render_template,request,session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://build-a-blog:password@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = "asdfgh"

db = SQLAlchemy(app)



class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120),nullable=False,unique=True)
    body = db.Column(db.Text)
    owner = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)

    def __init__(self,title,body,owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    user_name = db.Column(db.String(120),nullable=False,unique=True)
    password = db.Column(db.String(120),nullable=False)
    email = db.Column(db.String(120),nullable=False,unique=True)
    blog = db.relationship('Blog',backref='User',lazy=True)
    
    def __init__(self,user_name,email,password):
        self.user_name = user_name
        self.password = password
        self.email = email

@app.before_request
def required_login():
    
    allowed_routes = ['login_user', 'register_user']
    if request.endpoint not in allowed_routes and 'user' not in session:
        print(request.endpoint)
        return redirect('/login ')

@app.route('/',methods=['GET','POST'])
def blog_page():
    blogs = Blog.query.all()
    return render_template('blog.html',blogs=blogs)
    #TODO - get blogs render blog page

@app.route('/new-blog',methods=['GET','POST'])
def post_new_blog():
    error = ''
    if request.method =='post':
        title = request.form['title']
        body = request.form['body']
        owner = User.query.filter_by(user_name=session['user'])
        if not title and not body and not owner:
            return "<h1>Error</h1>"
            error = 'Please make sure that you have a title, and there is contents in the body.'
        else:
            new_blog = Blog(title,body,owner)
            db.session.add(new_blog)
            db.session.commit()
            return redirect('/')

    return render_template('newpost.html', error=error)
    #TODO - make blog post form, that submits then redirect to /blog

@app.route('/<blog>')
def selected_blog(blog):
    print('this is the thin being printed please dont miss ####### ',blog)
    blogs = Blog.query.filter_by(title=blog).all()
    return render_template('blog.html',blogs=blogs)

@app.route('/register',methods=['GET','POST'])
def register_user():
    # if request method = post then run
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
        if len(user.password) < 3 or len(user.password) > 20:
            password_err = "Please input a valid password"
        if str(user.password) != str(verify):
            verify_err = "Passwords don't match"
        if user_err == "" and email_err == "" and password_err == "" and verify_err == "":
            #if no errors add to database send to login
            db.session.add(user)
            db.session.commit()
            return redirect('/login')
        # else re-render site with errors
        return render_template('register.html',user_name=user.user_name,email=user.email,user_err=user_err,email_err=email_err,password_err=password_err,verify_err=verify_err)

    return render_template('register.html')


@app.route('/login',methods=['GET','POST'])
def login_user():

    error = ''
    if request.method == 'POST':
        user = User.query.filter_by(user_name=request.form['user_name']).first()
        password = request.form['password']
        if user and user.password == password:
            session['user'] = user.user_name
            return redirect('/')
        else:
            error='User name and or password are incorrect'
        
    return render_template('login.html', error=error)


@app.route('/logout',methods=['GET'])
def logout_user():
    del session['user']
    return redirect('/login')

if __name__ == "__main__":
    app.run()
