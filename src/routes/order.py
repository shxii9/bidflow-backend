from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.order import Order
from src.models.auction import Auction
from src.models.bid import Bid

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders', methods=['GET'])
def get_orders():
    """استرجاع قائمة بجميع الطلبات"""
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """استرجاع تفاصيل طلب معين"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'الطلب غير موجود'}), 404
        return jsonify(order.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders', methods=['POST'])
def create_order():
    """إنشاء طلب جديد من مزايدة فائزة"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['auction_id', 'bid_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # التحقق من وجود المزاد والمزايدة
        auction = Auction.query.get(data['auction_id'])
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        bid = Bid.query.get(data['bid_id'])
        if not bid:
            return jsonify({'error': 'المزايدة غير موجودة'}), 404
        
        # التحقق من أن المزايدة تنتمي للمزاد
        if bid.auction_id != auction.id:
            return jsonify({'error': 'المزايدة لا تنتمي لهذا المزاد'}), 400
        
        # التحقق من عدم وجود طلب مسبق لهذه المزايدة
        existing_order = Order.query.filter_by(bid_id=bid.id).first()
        if existing_order:
            return jsonify({'error': 'يوجد طلب بالفعل لهذه المزايدة'}), 400
        
        # إنشاء الطلب الجديد
        order = Order(
            auction_id=auction.id,
            bid_id=bid.id,
            user_id=auction.user_id,
            customer_name=bid.bidder_name,
            customer_phone=bid.bidder_phone,
            final_price=bid.bid_amount,
            delivery_address=data.get('delivery_address', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(order)
        db.session.commit()
        
        return jsonify(order.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    """تحديث تفاصيل طلب موجود"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'الطلب غير موجود'}), 404
        
        data = request.get_json()
        
        # تحديث الحقول المرسلة فقط
        if 'delivery_address' in data:
            order.delivery_address = data['delivery_address']
        if 'status' in data:
            order.status = data['status']
        if 'payment_status' in data:
            order.payment_status = data['payment_status']
        if 'notes' in data:
            order.notes = data['notes']
        
        db.session.commit()
        
        return jsonify(order.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    """حذف طلب"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'الطلب غير موجود'}), 404
        
        db.session.delete(order)
        db.session.commit()
        
        return jsonify({'message': 'تم حذف الطلب بنجاح'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@order_bp.route('/users/<user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """استرجاع طلبات مستخدم معين"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/auctions/<auction_id>/orders', methods=['GET'])
def get_auction_orders(auction_id):
    """استرجاع طلبات مزاد معين"""
    try:
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        orders = Order.query.filter_by(auction_id=auction_id).order_by(Order.created_at.desc()).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@order_bp.route('/orders/manifest/<auction_id>', methods=['GET'])
def get_auction_manifest(auction_id):
    """إنشاء قائمة الطلبات النهائية لمزاد معين"""
    try:
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        # استرجاع جميع الطلبات للمزاد
        orders = Order.query.filter_by(auction_id=auction_id).all()
        
        manifest = {
            'auction_id': auction_id,
            'auction_status': auction.status,
            'total_orders': len(orders),
            'total_value': sum(float(order.final_price) for order in orders),
            'orders': [order.to_dict() for order in orders]
        }
        
        return jsonify(manifest), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

