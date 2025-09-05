from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.notification import Notification

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """استرجاع قائمة بجميع الإشعارات"""
    try:
        notifications = Notification.query.order_by(Notification.created_at.desc()).all()
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/notifications/<notification_id>', methods=['GET'])
def get_notification(notification_id):
    """استرجاع تفاصيل إشعار معين"""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'الإشعار غير موجود'}), 404
        return jsonify(notification.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/notifications', methods=['POST'])
def create_notification():
    """إنشاء إشعار جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['user_id', 'type', 'title', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # التحقق من وجود المستخدم
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        # إنشاء الإشعار الجديد
        notification = Notification(
            user_id=data['user_id'],
            type=data['type'],
            title=data['title'],
            message=data['message'],
            related_auction_id=data.get('related_auction_id'),
            related_order_id=data.get('related_order_id')
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify(notification.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/notifications/<notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """تحديد إشعار كمقروء"""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'الإشعار غير موجود'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify(notification.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/notifications/<notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """حذف إشعار"""
    try:
        notification = Notification.query.get(notification_id)
        if not notification:
            return jsonify({'error': 'الإشعار غير موجود'}), 404
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'تم حذف الإشعار بنجاح'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/users/<user_id>/notifications', methods=['GET'])
def get_user_notifications(user_id):
    """استرجاع إشعارات مستخدم معين"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        # يمكن إضافة فلترة حسب الحالة (مقروء/غير مقروء)
        is_read = request.args.get('is_read')
        query = Notification.query.filter_by(user_id=user_id)
        
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            query = query.filter_by(is_read=is_read_bool)
        
        notifications = query.order_by(Notification.created_at.desc()).all()
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/users/<user_id>/notifications/unread/count', methods=['GET'])
def get_unread_notifications_count(user_id):
    """استرجاع عدد الإشعارات غير المقروءة لمستخدم معين"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
        return jsonify({'unread_count': count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notification_bp.route('/users/<user_id>/notifications/mark-all-read', methods=['PUT'])
def mark_all_notifications_read(user_id):
    """تحديد جميع إشعارات المستخدم كمقروءة"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        # تحديث جميع الإشعارات غير المقروءة
        updated_count = Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        
        return jsonify({'message': f'تم تحديد {updated_count} إشعار كمقروء'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

