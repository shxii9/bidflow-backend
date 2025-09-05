import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from src.models.user import db
from src.models.product import Product
from src.models.auction import Auction
from src.models.bid import Bid
from src.models.order import Order
from src.models.notification import Notification
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.product import product_bp
from src.routes.auction import auction_bp
from src.routes.bid import bid_bp
from src.routes.order import order_bp
from src.routes.notification import notification_bp
from src.routes.qr import qr_bp
from src.routes.realtime import realtime_bp, init_socketio

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# تمكين CORS لجميع المصادر
CORS(app)

# تهيئة SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")
init_socketio(app)

# تسجيل جميع الـ blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(auction_bp, url_prefix='/api')
app.register_blueprint(bid_bp, url_prefix='/api')
app.register_blueprint(order_bp, url_prefix='/api')
app.register_blueprint(notification_bp, url_prefix='/api')
app.register_blueprint(qr_bp, url_prefix='/api/qr')
app.register_blueprint(realtime_bp, url_prefix='/api/realtime')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
