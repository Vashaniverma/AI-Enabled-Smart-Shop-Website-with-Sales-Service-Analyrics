
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.utils import secure_filename
from flask import send_from_directory
import os
from models import Product
import json
import warnings
from joblib import load

# -------------------------------
# Load models safely
# -------------------------------
try:
    # Ignore version mismatch warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    vectorizer = load("models/vectorizer.pkl")  # or .joblib if renamed
    naive_bayes_model = load("models/naive_bayes_model.pkl")
    faq_model=load("models/faq_model.pkl")

    print("✅ Models loaded successfully")
except Exception as e:
    print("❌ Error loading models:", e)
    vectorizer = None
    naive_bayes_model = None


# ----------------- APP CONFIG -----------------
app = Flask(__name__)
app.secret_key = "your_secret_key"

# --- Two separate databases ---
app.config['SQLALCHEMY_BINDS'] = {
    'orders': 'sqlite:///user.db',   # Users + Orders
    'products': 'sqlite:///products.db', # Products
    'services': 'sqlite:///services.db',
    'order': 'sqlite:///order.db'# Products
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Upload config ---
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------- DATABASE MODELS -----------------
class User(db.Model):
    __bind_key__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Product(db.Model):
    __bind_key__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    image = db.Column(db.String(200))
    price_range = db.Column(db.String(50))


class ServiceOrder(db.Model):
    __bind_key__ = 'services'   # separate DB or can remove if you want same db
    id = db.Column(db.Integer, primary_key=True)

    # User/service details
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)

    # Product details (copied from products.db at install time)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

class ContactMessage(db.Model):
    __bind_key__ = "order"   # storing in user.db
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)  # positive/negative/neutral

# ----------------- CREATE DATABASE -----------------
with app.app_context():
    db.create_all(bind_key="orders")
    db.create_all(bind_key="products")
    db.create_all(bind_key="services")
    db.create_all(bind_key="order")

@app.route("/index")
def index():
    return render_template("index.html")
# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")

# ---------- AUTH ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    next_page = request.args.get("next")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # --- Admin (not in DB, hardcoded) ---
        if username == "admin" and password == "admin123":
            session["logged_in"]=True
            session["user_name"]="Admin"
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        # --- Normal user (check from DB) ---
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session["logged_in"] = True
            session["is_admin"] = False
            session["user_name"]=user.username
            return redirect(next_page or url_for("products"))

        return render_template("login.html", error="❌ Invalid username or password! Please check again or register first.")

    return render_template("login.html", next=next_page)


@app.route("/user-information")
def user_information():
    users = User.query.all()
    return render_template("user_information.html", users=users)

@app.route("/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("❌ User deleted successfully", "danger")
    return redirect(url_for("user_information"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # create new user
        new_user = User(
            username=username,
            email=email,
            password=password,  # ⚠️ ideally hash it!

        )

        db.session.add(new_user)
        db.session.commit()

        flash("✅ Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin_dashboard():
    # Total products
    total_products = Product.query.count()

    # Categories
    categories = db.session.query(
        Product.category, func.count(Product.id)
    ).group_by(Product.category).all()

    # Fetch services
    services = ServiceOrder.query.order_by(ServiceOrder.id.desc()).all()

    # Total Orders = last service ID (or 0 if no services yet)
    last_service = ServiceOrder.query.order_by(ServiceOrder.id.desc()).first()
    total_orders = ServiceOrder.query.count()
    # Total Revenue = sum of all prices
    total_revenue = db.session.query(func.sum(ServiceOrder.price)).scalar() or 0

    return render_template(
        "admin.html",
        total_products=total_products,
        categories=categories,
        services=services,
        total_orders=total_orders,
        total_revenue=total_revenue
    )



# Delete service
@app.route("/delete-service/<int:service_id>", methods=["POST"])
def delete_service(service_id):
    service = ServiceOrder.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash("Service deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))

# ---------- PRODUCTS MANAGEMENT ----------
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/add-product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        price = float(request.form["price"])
        description = request.form["description"]

        # Handle image upload
        image_file = request.files.get("image")
        image_path = None
        if image_file and image_file.filename != "" and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)

        # Auto price range
        if price < 10000:
            price_range = "under10000"
        elif price < 20000:
            price_range = "10000to20000"
        else:
            price_range = "above20000"

        # Save product
        new_product = Product(
            name=name,
            category=category,
            price=price,
            description=description,
            image=image_path,
            price_range=price_range
        )
        db.session.add(new_product)
        db.session.commit()
        flash("✅ Product added successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html")


@app.route("/manage-products")
def manage_products():
    products = Product.query.all()
    return render_template("manage_products.html", products=products)

@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash("❌ Product deleted successfully", "danger")
    return redirect(url_for("manage_products"))

@app.route("/update-product/<int:product_id>", methods=["GET", "POST"])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.name = request.form["name"]
        product.category = request.form["category"]
        product.price = float(request.form["price"])
        product.description = request.form["description"]

        # Handle image update
        image_file = request.files.get("image")
        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image_file.save(image_path)
            product.image = image_path

        db.session.commit()
        flash("✅ Product updated successfully", "success")
        return redirect(url_for("manage_products"))

    return render_template("update_product.html", product=product)


with open("data/chat.json", "r") as f:
    data = json.load(f)
    faqs = data["faq"]

# Optional: prepare a list of "questions" or "keywords" for your model
questions = [" ".join(faq["keywords"]) for faq in faqs]
answers = [faq["answer"] for faq in faqs]


def get_answer(user_input, threshold=0.4):
    user_input = user_input.lower().strip()

    try:
        # Get probabilities for each class
        probs = faq_model.predict_proba([user_input])[0]
        max_prob = max(probs)
        predicted_answer = faq_model.predict([user_input])[0]

        # Only accept if confidence is high enough
        if max_prob >= threshold:
            return predicted_answer
        else:
            # fallback: keyword search
            for faq in faqs:
                for keyword in faq['keywords']:
                    if keyword.lower() in user_input:
                        return faq['answer']
            return "❌ Sorry, I don't understand."

    except Exception as e:
        print("Error in prediction:", e)
        return "❌ Sorry, I don't understand."





@app.route("/get_answer", methods=["POST"])
def answer():
    user_input = request.json.get("message")
    ans = get_answer(user_input)
    return jsonify({"answer": ans})

# ---------- FRONTEND PAGES ----------
@app.route("/products")
def products():
    return render_template("products.html")

# ---------- API ENDPOINT ----------
@app.route("/api/products")
def api_products():
    products = Product.query.all()
    product_list = []
    for p in products:
        product_list.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "description": p.description,
            # Store relative path for image
            "image": url_for("static", filename=f"uploads/{os.path.basename(p.image)}") if p.image else None
        })
    return jsonify(product_list)

@app.route("/orders")
def orders():
    return render_template("orders.html")


@app.route("/install/<int:product_id>")
def install(product_id):
    # 🔒 Require login for installation
    if not session.get("logged_in"):
        return redirect(url_for("login", next=url_for("install", product_id=product_id)))

    product = Product.query.get_or_404(product_id)

    # Pre-fill product info and redirect to services form
    return render_template(
        "services.html",
        product_name=product.name,
        product_price=product.price,
        product_image = product.image
    )


@app.route("/services", methods=["GET", "POST"])
def services():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        service_type = request.form.get("service")
        date = request.form.get("date")
        address = request.form.get("address")

        product_name = request.form.get("product_name")
        product_price = request.form.get("product_price")
        product_image = request.files.get("product_image")

        order = ServiceOrder(
            name=name,
            phone=phone,
            service_type=service_type,
            date=date,
            address=address,
            product_name=product_name,
            price=product_price
        )
        db.session.add(order)
        db.session.commit()
        return redirect(url_for("thank_you"))

    return render_template("services.html")

def get_sentiment(message):
    if not isinstance(message, str):
        message = str(message)

    if vectorizer is None or naive_bayes_model is None:
        return "Error: Model not loaded"

    X = vectorizer.transform([message])
    prediction = naive_bayes_model.predict(X)[0]
    return prediction

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        print("Received:", name, email, message)

        # Vectorize + Predict sentiment
        prediction = get_sentiment(message)
        print("Predicted sentiment:", prediction)  # 🔹 Debug

        # Save to DB
        new_msg = ContactMessage(
            name=name,
            email=email,
            message=message,
            sentiment=prediction
        )
        db.session.add(new_msg)
        db.session.commit()

        print("Saved to DB ✅")  # 🔹 Debug
        flash("✅ Your message has been sent successfully!", "success")
        return render_template("thank.html")

    # Handle GET request: render contact page
    return render_template("contact.html")


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/thank-you")
def thank_you():
    return render_template("thank_you.html")

# ---------- USER MESSAGES MANAGEMENT ----------
@app.route("/user_message")
def user_message():
    messages = ContactMessage.query.order_by(ContactMessage.id.desc()).all()
    return render_template("user_message.html", messages=messages)


@app.route("/delete_message/<int:msg_id>", methods=["POST"])
def delete_message(msg_id):
    # Use SQLAlchemy to delete
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Message deleted successfully!", "success")
    return redirect(url_for("user_message"))

@app.route("/thank")
def thank():
    return render_template("thank")
# ----------------- RUN -----------------
if __name__ == "__main__":
    app.run(debug=True)
