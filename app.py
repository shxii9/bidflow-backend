# <-- التغيير هنا: استيراد المكتبات اللازمة لإدارة متغيرات البيئة
import os
from dotenv import load_dotenv

# <-- التغيير هنا: تحميل المتغيرات من ملف .env في بداية تشغيل التطبيق
load_dotenv()

import jwt
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from dateutil.parser import parse
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

# -----------------------------------------------------------------------------
# 1. إعداد التطبيق (App Setup)
# -----------------------------------------------------------------------------
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# <-- التغيير هنا: قراءة إعدادات قاعدة البيانات والمفتاح السري من متغيرات البيئة
# يتم توفير قيمة افتراضية في حال لم يتم العثور على المتغير، وهذا مناسب لبيئة التطوير
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-default-secret-key-for-development-only')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------------------------------------------------
# 2. ربط قاعدة البيانات والإضافات (DB and Extensions Init)
# -----------------------------------------------------------------------------
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# -----------------------------------------------------------------------------
# 3. تعريف نماذج قاعدة البيانات (Database Models)
# -----------------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    role = db.Column(db.String(20), nullable=False, default='bidder')
    items = db.relationship('Item', backref='owner', lazy=True)
    bids = db.relationship('Bid', backref='bidder', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    starting_price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), nullable=False, default='draft')
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    auction = db.relationship('Auction', backref='item', uselist=False, lazy=True)

class Auction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), unique=True, nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    bids = db.relationship('Bid', backref='auction', lazy=True)

class Bid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    auction_id = db.Column(db.Integer, db.ForeignKey('auction.id'), nullable=False)
    bidder_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# -----------------------------------------------------------------------------
# إعداد لوحة التحكم Flask-Admin
# -----------------------------------------------------------------------------
class AdminModelView(ModelView):
    pass

admin = Admin(app, name='BidFlow Control Panel', template_mode='bootstrap3')
admin.add_view(AdminModelView(User, db.session))
admin.add_view(AdminModelView(Item, db.session))
admin.add_view(AdminModelView(Auction, db.session))
admin.add_view(AdminModelView(Bid, db.session))

# -----------------------------------------------------------------------------
# 4. المهمة المجدولة (Scheduled Job)
# -----------------------------------------------------------------------------
def check_auctions():
    with app.app_context():
        now = datetime.now(timezone.utc)
        pending_auctions = Auction.query.filter_by(status='pending').filter(Auction.start_time <= now).all()
        for auction in pending_auctions:
            auction.status = 'active'
            auction.item.status = 'active'
        active_auctions = Auction.query.filter_by(status='active').filter(Auction.end_time <= now).all()
        for auction in active_auctions:
            auction.status = 'ended'
            highest_bid = Bid.query.filter_by(auction_id=auction.id).order_by(Bid.amount.desc()).first()
            if highest_bid:
                auction.winner_id = highest_bid.bidder_id
                auction.item.status = 'sold'
            else:
                auction.item.status = 'ended'
        db.session.commit()

# -----------------------------------------------------------------------------
# 5. الديكورات (Decorators)
# -----------------------------------------------------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.session.get(User, data['user_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        if not current_user:
            return jsonify({'message': 'User not found!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = args[0]
            if current_user.role != role_name:
                return jsonify({'message': f'Access denied: Requires {role_name} role!'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -----------------------------------------------------------------------------
# 6. مسارات التطبيق (Routes / Endpoints)
# -----------------------------------------------------------------------------
# ... (جميع مساراتك تبقى كما هي، لا حاجة لتغييرها) ...
@app.route('/')
def index():
    return "مرحباً بك في الخادم الخلفي لنظام المزادات!"

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"error": "الرجاء إدخال اسم المستخدم والبريد الإلكتروني وكلمة المرور"}), 400
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "اسم المستخدم هذا موجود بالفعل"}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "هذا البريد الإلكتروني مسجل بالفعل"}), 409
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        username=data['username'], email=data['email'], password_hash=hashed_password,
        full_name=data.get('full_name'), phone_number=data.get('phone_number'),
        role=data.get('role', 'bidder')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({
        "message": "تم تسجيل المستخدم بنجاح!",
        "user": {"id": new_user.id, "username": new_user.username, "email": new_user.email, "role": new_user.role}
    }), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "الرجاء إدخال اسم المستخدم وكلمة المرور"}), 400
    user = User.query.filter_by(username=data['username']).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "اسم المستخدم أو كلمة المرور غير صحيحة"}), 401
    token = jwt.encode({
        'user_id': user.id, 'username': user.username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return jsonify({"message": "تم تسجيل الدخول بنجاح!", "access_token": token}), 200

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        "id": current_user.id, "username": current_user.username,
        "email": current_user.email, "full_name": current_user.full_name,
        "role": current_user.role
    })

@app.route('/api/items', methods=['GET'])
def get_all_items():
    items = Item.query.all()
    output = []
    for item in items:
        item_data = {
            'id': item.id, 'name': item.name, 'description': item.description,
            'starting_price': item.starting_price, 'status': item.status,
            'owner_id': item.owner_id,
            'image_url': f"/uploads/{item.image_url}" if item.image_url else None
        }
        output.append(item_data)
    return jsonify({'items': output})

@app.route('/api/items', methods=['POST'])
@token_required
@role_required('merchant')
def create_item(current_user):
    if 'name' not in request.form or 'starting_price' not in request.form:
        return jsonify({'message': 'Name and starting price are required in the form data!'}), 400
    if 'image' not in request.files:
        return jsonify({'message': 'No image file part!'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'message': 'No selected file!'}), 400
    image_filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        image_filename = unique_filename
    if not image_filename:
        return jsonify({'message': 'File type not allowed!'}), 400
    new_item = Item(
        name=request.form['name'],
        description=request.form.get('description'),
        starting_price=float(request.form['starting_price']),
        owner_id=current_user.id,
        image_url=image_filename
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({
        'message': 'Item with image created successfully!',
        'item': {
            'id': new_item.id,
            'name': new_item.name,
            'owner_id': new_item.owner_id,
            'image_url': f"/uploads/{new_item.image_url}"
        }
    }), 201

@app.route('/api/auctions', methods=['POST'])
@token_required
def create_auction(current_user):
    data = request.get_json()
    item_id = data.get('item_id')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    if not all([item_id, start_time_str, end_time_str]):
        return jsonify({'message': 'Item ID, start time, and end time are required!'}), 400
    item = db.session.get(Item, item_id)
    if not item:
        return jsonify({'message': 'Item not found!'}), 404
    if item.owner_id != current_user.id:
        return jsonify({'message': 'Forbidden: You do not own this item!'}), 403
    if item.auction:
        return jsonify({'message': 'This item is already in an auction!'}), 409
    try:
        start_time = parse(start_time_str).astimezone(timezone.utc)
        end_time = parse(end_time_str).astimezone(timezone.utc)
    except ValueError:
        return jsonify({'message': 'Invalid date format. Please use ISO 8601 format.'}), 400
    new_auction = Auction(
        item_id=item.id, start_time=start_time, end_time=end_time,
        current_price=item.starting_price
    )
    item.status = 'scheduled'
    db.session.add(new_auction)
    db.session.commit()
    return jsonify({
        'message': 'Auction created successfully!',
        'auction': {
            'id': new_auction.id, 'item_id': new_auction.item_id,
            'start_time': new_auction.start_time.isoformat(),
            'end_time': new_auction.end_time.isoformat(),
            'status': new_auction.status
        }
    }), 201

@app.route('/api/auctions/<int:auction_id>', methods=['GET'])
def get_auction_details(auction_id):
    auction = db.session.get(Auction, auction_id)
    if not auction:
        return jsonify({'message': 'Auction not found!'}), 404
    bids = Bid.query.filter_by(auction_id=auction.id).order_by(Bid.created_at.desc()).all()
    bids_output = []
    for bid in bids:
        bids_output.append({
            'id': bid.id,
            'amount': bid.amount,
            'created_at': bid.created_at.isoformat(),
            'bidder_username': bid.bidder.username
        })
    auction_data = {
        'id': auction.id,
        'start_time': auction.start_time.isoformat(),
        'end_time': auction.end_time.isoformat(),
        'current_price': auction.current_price,
        'status': auction.status,
        'item': {
            'id': auction.item.id,
            'name': auction.item.name,
            'description': auction.item.description,
            'starting_price': auction.item.starting_price,
            'image_url': f"/uploads/{auction.item.image_url}" if auction.item.image_url else None
        },
        'owner_username': auction.item.owner.username,
        'winner_id': auction.winner_id,
        'bids': bids_output
    }
    return jsonify(auction_data)

@app.route('/api/bids', methods=['POST'])
@token_required
def place_bid(current_user):
    data = request.get_json()
    auction_id = data.get('auction_id')
    amount = data.get('amount')
    if not auction_id or amount is None:
        return jsonify({'message': 'Auction ID and amount are required!'}), 400
    auction = db.session.get(Auction, auction_id)
    if not auction:
        return jsonify({'message': 'Auction not found!'}), 404
    if auction.status != 'active':
        return jsonify({'message': f'This auction is not active! Its status is {auction.status}.'}), 403
    if auction.item.owner_id == current_user.id:
        return jsonify({'message': 'You cannot bid on your own item!'}), 403
    if float(amount) <= auction.current_price:
        return jsonify({'message': f'Your bid must be higher than the current price of {auction.current_price}!'}), 400
    new_bid = Bid(
        amount=float(amount), auction_id=auction.id,
        bidder_id=current_user.id
    )
    auction.current_price = float(amount)
    db.session.add(new_bid)
    db.session.commit()
    return jsonify({
        'message': 'Bid placed successfully!',
        'bid': {
            'id': new_bid.id, 'amount': new_bid.amount,
            'auction_id': new_bid.auction_id, 'bidder': current_user.username
        },
        'new_current_price': auction.current_price
    }), 201

# -----------------------------------------------------------------------------
# 7. نقطة انطلاق التطبيق وإعداد الجدولة
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        db.create_all()

    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(check_auctions, 'interval', seconds=60)
    scheduler.start()
    
    print("--- Starting Flask App with Admin Panel and Scheduler ---")
    
    # <-- التغيير هنا: قراءة وضع التصحيح من متغيرات البيئة
    # هذا يضمن عدم تشغيل وضع التصحيح عن طريق الخطأ في بيئة الإنتاج
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
    app.run(debug=debug_mode, use_reloader=False)
