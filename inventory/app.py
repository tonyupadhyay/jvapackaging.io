# inventory/app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from flask_cors import CORS 

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_secret_key_for_inventory_app_12345_!@#$%^&*()')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

CORS(app, supports_credentials=True)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    products = db.relationship('Product', backref='owner', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float, nullable=False, default=0.0)
    category = db.Column(db.String(50), nullable=True)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

# --- Database Initialization ---
with app.app_context():
    db.create_all()
   
    if not User.query.filter_by(username='admin').first():
        print("Creating default admin user: admin/password")
        admin_user = User(username='admin', email='admin@example.com')
        admin_user.set_password('password') 
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin user created. Login with username 'admin' and password 'password'.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the request is an specific API call
        if request.path.startswith('/api/'):
            if 'user_id' not in session:
                return jsonify({"message": "Authentication required"}), 401
            return f(*args, **kwargs)
        else: 
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
   
    products = Product.query.filter_by(user_id=session['user_id']).all()
    
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if user.username == 'admin': 
                session['user_id'] = user.id
                session['username'] = user.username
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Only admin users are allowed to log in via this form.', 'danger')
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
   
    return render_template('login.html')

@app.route('/logout')
def logout():
   
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    # Redirect to the frontend's index.html, assuming it's served on port 5500
    return redirect("http://127.0.0.1:5500/index.html")
    

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        category = request.form['category']
        sku = request.form['sku']
        current_user_id = session['user_id']
        if sku:
            existing_sku = Product.query.filter_by(sku=sku, user_id=current_user_id).first()
            if existing_sku:
                flash('SKU already exists for your inventory. Please use a unique SKU.', 'danger')
                # Ensure you have 'templates/add_edit_product.html'
                return render_template('add_edit_product.html', product=None)

        new_product = Product(name=name, description=description,
                              quantity=quantity, price=price,
                              category=category, sku=sku, user_id=current_user_id)
        db.session.add(new_product)
        db.session.commit()
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_edit_product.html', product=None)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
   
    product = Product.query.get_or_404(product_id)
    if product.user_id != session['user_id']:
        flash('You are not authorized to edit this product.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.quantity = int(request.form['quantity'])
        product.price = float(request.form['price'])
        product.category = request.form['category']
        new_sku = request.form['sku']
        if new_sku and new_sku != product.sku:
            existing_sku = Product.query.filter_by(sku=new_sku, user_id=session['user_id']).first()
            if existing_sku:
                flash('SKU already exists for your inventory. Please use a unique SKU.', 'danger')
               
                return render_template('add_edit_product.html', product=product)

        product.sku = new_sku
        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)
    if product.user_id != session['user_id']:
        flash('You are not authorized to delete this product.', 'danger')
        return redirect(url_for('index'))

    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" deleted successfully!', 'info')
    return redirect(url_for('index'))

@app.route('/print_inventory')
@login_required
def print_inventory():
    products = Product.query.filter_by(user_id=session['user_id']).all()
    username = session.get('username', 'Admin')
 
    return render_template('inventory_print.html', products=products, username=username)


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() 
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        if user.username == 'admin': 
            session['user_id'] = user.id
            session['username'] = user.username
          
            return jsonify({"message": "Login successful!", "user": user.username}), 200
        else:
            return jsonify({"message": "Only admin users are allowed to log in."}), 403 
    else:
        return jsonify({"message": "Invalid username or password."}), 401 

@app.route('/api/logout', methods=['POST'])
@login_required 
def api_logout():
   
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"message": "Successfully logged out"}), 200

@app.route('/api/products', methods=['GET'])
@login_required # Protect this API endpoint
def api_get_products():
  
    products = Product.query.filter_by(user_id=session['user_id']).all()
  
    products_data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "quantity": p.quantity,
            "price": p.price,
            "category": p.category,
            "sku": p.sku
        } for p in products
    ]
    return jsonify(products_data), 200

@app.errorhandler(404)
def page_not_found(error):
    flash("The requested URL was not found on this server.", "error")
    return render_template('404.html'), 404

if __name__ == '__main__':

    if not os.path.exists('static'):
        os.makedirs('static')
    if not os.path.exists('templates'):
        os.makedirs('templates')

    app.run(debug=True, port=5000) # Run on port 5000, enable debug mode for development
