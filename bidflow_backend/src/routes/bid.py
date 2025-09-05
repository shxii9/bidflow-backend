from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.bid import Bid
from src.models.auction import Auction

bid_bp = Blueprint('bid', __name__)

@bid_bp.route('/bids', methods=['GET'])
def get_bids():
    """استرجاع قائمة بجميع المزايدات"""
    try:
        bids = Bid.query.order_by(Bid.bid_time.desc()).all()
        return jsonify([bid.to_dict() for bid in bids]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bid_bp.route('/bids/<bid_id>', methods=['GET'])
def get_bid(bid_id):
    """استرجاع تفاصيل مزايدة معينة"""
    try:
        bid = Bid.query.get(bid_id)
        if not bid:
            return jsonify({'error': 'المزايدة غير موجودة'}), 404
        return jsonify(bid.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bid_bp.route('/auctions/<auction_id>/bids', methods=['GET'])
def get_auction_bids(auction_id):
    """استرجاع جميع المزايدات لمزاد معين"""
    try:
        # التحقق من وجود المزاد
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        # استرجاع المزايدات مرتبة حسب المبلغ (الأعلى أولاً)
        bids = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_amount.desc()).all()
        return jsonify([bid.to_dict() for bid in bids]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bid_bp.route('/auctions/<auction_id>/bids/highest', methods=['GET'])
def get_highest_bid(auction_id):
    """استرجاع أعلى مزايدة لمزاد معين"""
    try:
        # التحقق من وجود المزاد
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        # العثور على أعلى مزايدة
        highest_bid = Bid.query.filter_by(auction_id=auction_id).order_by(Bid.bid_amount.desc()).first()
        
        if not highest_bid:
            return jsonify({'message': 'لا توجد مزايدات لهذا المزاد'}), 404
        
        return jsonify(highest_bid.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bid_bp.route('/bids/<bid_id>', methods=['DELETE'])
def delete_bid(bid_id):
    """حذف مزايدة (للإدارة فقط)"""
    try:
        bid = Bid.query.get(bid_id)
        if not bid:
            return jsonify({'error': 'المزايدة غير موجودة'}), 404
        
        # التحقق من أن المزاد لا يزال نشطاً
        auction = Auction.query.get(bid.auction_id)
        if auction and auction.status != 'active':
            return jsonify({'error': 'لا يمكن حذف مزايدة من مزاد منتهي'}), 400
        
        # تحديث إحصائيات المزاد
        if auction:
            auction.total_bids -= 1
            
            # إذا كانت هذه أعلى مزايدة، نحتاج لإعادة حساب أعلى مزايدة
            if auction.current_highest_bid == bid.bid_amount:
                remaining_bids = Bid.query.filter_by(auction_id=bid.auction_id).filter(Bid.id != bid_id).order_by(Bid.bid_amount.desc()).first()
                if remaining_bids:
                    auction.current_highest_bid = remaining_bids.bid_amount
                else:
                    auction.current_highest_bid = auction.starting_price
        
        db.session.delete(bid)
        db.session.commit()
        
        return jsonify({'message': 'تم حذف المزايدة بنجاح'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bid_bp.route('/bids/search', methods=['GET'])
def search_bids():
    """البحث في المزايدات حسب رقم الهاتف أو الاسم"""
    try:
        phone = request.args.get('phone')
        name = request.args.get('name')
        
        query = Bid.query
        
        if phone:
            query = query.filter(Bid.bidder_phone.like(f'%{phone}%'))
        
        if name:
            query = query.filter(Bid.bidder_name.like(f'%{name}%'))
        
        bids = query.order_by(Bid.bid_time.desc()).all()
        return jsonify([bid.to_dict() for bid in bids]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

