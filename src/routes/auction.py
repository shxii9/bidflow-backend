from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.product import Product
from src.models.auction import Auction
from src.models.bid import Bid
from datetime import datetime

auction_bp = Blueprint('auction', __name__)

@auction_bp.route('/auctions', methods=['GET'])
def get_auctions():
    """استرجاع قائمة بالمزادات"""
    try:
        auctions = Auction.query.all()
        return jsonify([auction.to_dict() for auction in auctions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auction_bp.route('/auctions/<auction_id>', methods=['GET'])
def get_auction(auction_id):
    """استرجاع تفاصيل مزاد معين مع المزايدات"""
    try:
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        # استرجاع المزايدات مرتبة حسب الوقت
        bids = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_time.desc()).all()
        
        auction_data = auction.to_dict()
        auction_data['bids'] = [bid.to_dict() for bid in bids]
        
        return jsonify(auction_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auction_bp.route('/auctions/<product_id>/start', methods=['POST'])
def start_auction(product_id):
    """بدء مزاد لمنتج معين"""
    try:
        # التحقق من وجود المنتج
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        
        # التحقق من عدم وجود مزاد نشط للمنتج
        existing_auction = Auction.query.filter_by(
            product_id=product_id, 
            status='active'
        ).first()
        
        if existing_auction:
            return jsonify({'error': 'يوجد مزاد نشط بالفعل لهذا المنتج'}), 400
        
        # إنشاء مزاد جديد
        auction = Auction(
            product_id=product_id,
            user_id=product.user_id,
            starting_price=product.starting_price,
            status='active',
            start_time=datetime.utcnow()
        )
        
        # تحديث حالة المنتج
        product.status = 'active'
        
        db.session.add(auction)
        db.session.commit()
        
        return jsonify(auction.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auction_bp.route('/auctions/<auction_id>/end', methods=['POST'])
def end_auction(auction_id):
    """إنهاء مزاد وتحديد الفائز"""
    try:
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        if auction.status != 'active':
            return jsonify({'error': 'المزاد غير نشط'}), 400
        
        # العثور على أعلى مزايدة
        highest_bid = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_amount.desc()).first()
        
        # تحديث حالة المزاد
        auction.status = 'ended'
        auction.end_time = datetime.utcnow()
        
        if highest_bid:
            auction.winner_bid_id = highest_bid.id
            auction.current_highest_bid = highest_bid.bid_amount
            
            # تحديث حالة المزايدة الفائزة
            highest_bid.is_winning_bid = True
            
            # تحديث حالة المنتج
            product = Product.query.get(auction.product_id)
            if product:
                product.status = 'sold'
        
        db.session.commit()
        
        result = auction.to_dict()
        if highest_bid:
            result['winner_bid'] = highest_bid.to_dict()
        
        return jsonify(result), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auction_bp.route('/auctions/<auction_id>/bid', methods=['POST'])
def place_bid(auction_id):
    """تسجيل مزايدة جديدة"""
    try:
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        if auction.status != 'active':
            return jsonify({'error': 'المزاد غير نشط'}), 400
        
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['bidder_name', 'bidder_phone', 'bid_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        bid_amount = float(data['bid_amount'])
        
        # التحقق من أن المزايدة أكبر من السعر الحالي
        current_highest = auction.current_highest_bid or auction.starting_price
        if bid_amount <= current_highest:
            return jsonify({'error': f'يجب أن تكون المزايدة أكبر من {current_highest}'}), 400
        
        # إنشاء المزايدة الجديدة
        bid = Bid(
            auction_id=auction_id,
            bidder_name=data['bidder_name'],
            bidder_phone=data['bidder_phone'],
            bid_amount=bid_amount,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # تحديث المزاد
        auction.current_highest_bid = bid_amount
        auction.total_bids += 1
        
        db.session.add(bid)
        db.session.commit()
        
        return jsonify(bid.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auction_bp.route('/users/<user_id>/auctions', methods=['GET'])
def get_user_auctions(user_id):
    """استرجاع مزادات مستخدم معين"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        auctions = Auction.query.filter_by(user_id=user_id).order_by(Auction.created_at.desc()).all()
        return jsonify([auction.to_dict() for auction in auctions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

