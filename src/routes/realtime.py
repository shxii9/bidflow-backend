from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from ..models.notification import Notification
from ..models.user import db
import json
from datetime import datetime

realtime_bp = Blueprint('realtime', __name__)

# سيتم تهيئة SocketIO في main.py
socketio = None

def init_socketio(app):
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('connected', {'message': 'متصل بنجاح'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')
    
    @socketio.on('join_merchant')
    def handle_join_merchant(data):
        merchant_id = data.get('merchant_id')
        if merchant_id:
            join_room(f'merchant_{merchant_id}')
            emit('joined', {'message': f'انضممت لغرفة التاجر {merchant_id}'})
    
    @socketio.on('leave_merchant')
    def handle_leave_merchant(data):
        merchant_id = data.get('merchant_id')
        if merchant_id:
            leave_room(f'merchant_{merchant_id}')
            emit('left', {'message': f'غادرت غرفة التاجر {merchant_id}'})

def send_notification_to_merchant(merchant_id, notification_data):
    """إرسال إشعار للتاجر في الوقت الفعلي"""
    if socketio:
        socketio.emit('new_notification', notification_data, room=f'merchant_{merchant_id}')

def send_bid_update(auction_id, bid_data):
    """إرسال تحديث المزايدة لجميع المتابعين"""
    if socketio:
        socketio.emit('bid_update', {
            'auction_id': auction_id,
            'bid_data': bid_data
        }, room=f'auction_{auction_id}')

@realtime_bp.route('/notifications/send', methods=['POST'])
def send_notification():
    """إرسال إشعار جديد"""
    try:
        data = request.get_json()
        
        # إنشاء الإشعار في قاعدة البيانات
        notification = Notification(
            user_id=data['user_id'],
            title=data['title'],
            message=data['message'],
            type=data.get('type', 'info'),
            data=json.dumps(data.get('data', {}))
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # إرسال الإشعار في الوقت الفعلي
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'created_at': notification.created_at.isoformat(),
            'data': json.loads(notification.data) if notification.data else {}
        }
        
        send_notification_to_merchant(data['user_id'], notification_data)
        
        return jsonify({
            'success': True,
            'notification': notification_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@realtime_bp.route('/notifications/broadcast', methods=['POST'])
def broadcast_notification():
    """بث إشعار لجميع المستخدمين المتصلين"""
    try:
        data = request.get_json()
        
        if socketio:
            socketio.emit('broadcast_notification', {
                'title': data['title'],
                'message': data['message'],
                'type': data.get('type', 'info')
            })
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@realtime_bp.route('/auctions/<auction_id>/join', methods=['POST'])
def join_auction_room(auction_id):
    """الانضمام لغرفة مزاد معين لتلقي التحديثات"""
    try:
        # هذا سيتم تنفيذه عبر WebSocket في الواقع
        return jsonify({
            'success': True,
            'message': f'انضممت لمتابعة المزاد {auction_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@realtime_bp.route('/system/stats', methods=['GET'])
def get_system_stats():
    """إحصائيات النظام في الوقت الفعلي"""
    try:
        # حساب إحصائيات سريعة
        from ..models.auction import Auction
        from ..models.bid import Bid
        from ..models.order import Order
        
        active_auctions = Auction.query.filter_by(status='active').count()
        total_bids_today = Bid.query.filter(
            Bid.bid_time >= datetime.now().date()
        ).count()
        pending_orders = Order.query.filter_by(status='pending').count()
        
        stats = {
            'active_auctions': active_auctions,
            'total_bids_today': total_bids_today,
            'pending_orders': pending_orders,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

