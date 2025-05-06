from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    dob = db.Column(db.String(10), nullable=False)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)


class Donate(db.Model):
    __tablename__ = "donate"

    aadhaar = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(100))
    weight = db.Column(db.Integer)
    gender = db.Column(db.String(100))
    address = db.Column(db.String(100))
    bloodgroup = db.Column(db.String(100))

    def __repr__(self):
        return f"Aadhaar: {self.aadhaar} Name: {self.name} Age: {self.age} Weight: {self.weight} Gender: {self.gender} Address: {self.address} Blood Group:  {self.bloodgroup}"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------- Flask Web Routes ----------
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        dob = request.form['dob']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or Email already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(first_name=first_name, last_name=last_name, email=email, dob=dob, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can log in now.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route("/donate", methods=["GET", "POST"])
@login_required
def donate():
    if request.method == "POST":
        aadhaar = request.form.get("aadhaar")
        name = request.form.get("name")
        age = request.form.get("age")
        weight = request.form.get("weight")
        gender = request.form.get("gender")
        address = request.form.get("address")
        bloodgroup = request.form.get("bloodgroup")

        donate = Donate(name=name, aadhaar=aadhaar, age=age, weight=weight, gender=gender, address=address, bloodgroup=bloodgroup)
        db.session.add(donate)
        db.session.commit()
        return redirect(url_for("donate"))

    donate = Donate.query.all()
    return render_template("donate.html")


@app.route('/about')
def about():
    return render_template('aboutus.html')


# ---------- API Routes ----------
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    required_fields = ['first_name', 'last_name', 'email', 'dob', 'username', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({"status": "error", "message": "Username or email already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        dob=data['dob'],
        username=data['username'],
        password=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "success", "message": "User registered"}), 201




@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(username=data.get("username")).first()
    if user and bcrypt.check_password_hash(user.password, data.get("password")):
        return jsonify({"status": "success", "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }})
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401


@app.route('/api/dashboard/<username>', methods=['GET'])
def api_dashboard(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({
        "status": "success",
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "dob": user.dob,
            "username": user.username
        }
    })


@app.route('/api/donate', methods=['POST'])
def api_donate():
    data = request.json
    required_fields = ['aadhaar', 'name', 'age', 'weight', 'gender', 'address', 'bloodgroup']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
    donation = Donate(**data)
    db.session.add(donation)
    db.session.commit()
    return jsonify({"status": "success", "message": "Donation recorded"}), 201


@app.route('/api/donations', methods=['GET'])
def get_donations():
    donations = Donate.query.all()
    data = [{
        "aadhaar": d.aadhaar,
        "name": d.name,
        "age": d.age,
        "weight": d.weight,
        "gender": d.gender,
        "address": d.address,
        "bloodgroup": d.bloodgroup
    } for d in donations]
    return jsonify(data)


@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        "status": "success",
        "message": "api working"
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
