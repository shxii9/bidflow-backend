from flask import Blueprint, request, jsonify
from src.models.user import db, User
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__)

# مفتاح سري للتوقيع (يجب أن يكون في متغير بيئة في الإنتاج)
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

def token_required(f):
    """ديكوريتر للتحقق من صحة التوكن"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'التوكن مطلوب'}), 401
        
        try:
            # إزالة "Bearer " من بداية التوكن
            if token.startswith('Bearer '):
                token = token[7:]
            
            # فك تشفير التوكن
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # التحقق من وجود المستخدم
            current_user = User.query.get(current_user_id)
            if not current_user:
                return jsonify({'error': 'مستخدم غير صالح'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'التوكن منتهي الصلاحية'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'توكن غير صالح'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """تسجيل مستخدم جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم أو البريد الإلكتروني
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'اسم المستخدم أو البريد الإلكتروني موجود بالفعل'}), 400
        
        # إنشاء المستخدم الجديد
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            phone_number=data.get('phone_number', ''),
            business_name=data.get('business_name', '')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # إنشاء توكن للمستخدم الجديد
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'message': 'تم إنشاء الحساب بنجاح',
            'user': user.to_dict(),
            'access_token': token,
            'token_type': 'bearer'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """تسجيل دخول المستخدم"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'اسم المستخدم وكلمة المرور مطلوبان'}), 400
        
        # البحث عن المستخدم
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'اسم المستخدم أو كلمة المرور غير صحيحة'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'الحساب غير مفعل'}), 401
        
        # إنشاء توكن
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=30)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({
            'message': 'تم تسجيل الدخول بنجاح',
            'user': user.to_dict(),
            'access_token': token,
            'token_type': 'bearer'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """استرجاع معلومات المستخدم الحالي"""
    return jsonify(current_user.to_dict()), 200

@auth_bp.route('/auth/change-password', methods=['PUT'])
@token_required
def change_password(current_user):
    """تغيير كلمة المرور"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['current_password', 'new_password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # التحقق من كلمة المرور الحالية
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'كلمة المرور الحالية غير صحيحة'}), 400
        
        # تحديث كلمة المرور
        current_user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'تم تغيير كلمة المرور بنجاح'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/update-profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """تحديث معلومات المستخدم"""
    try:
        data = request.get_json()
        
        # تحديث الحقول المرسلة فقط
        if 'full_name' in data:
            current_user.full_name = data['full_name']
        if 'phone_number' in data:
            current_user.phone_number = data['phone_number']
        if 'business_name' in data:
            current_user.business_name = data['business_name']
        if 'email' in data:
            # التحقق من عدم وجود بريد إلكتروني مكرر
            existing_user = User.query.filter(User.email == data['email'], User.id != current_user.id).first()
            if existing_user:
                return jsonify({'error': 'البريد الإلكتروني موجود بالفعل'}), 400
            current_user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'تم تحديث المعلومات بنجاح',
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

