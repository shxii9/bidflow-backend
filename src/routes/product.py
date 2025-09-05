from flask import Blueprint, request, jsonify
from src.models.user import db, User
from src.models.product import Product
import uuid

product_bp = Blueprint('product', __name__)

@product_bp.route('/products', methods=['GET'])
def get_products():
    """استرجاع قائمة بجميع المنتجات"""
    try:
        # يمكن إضافة فلترة حسب المستخدم لاحقاً
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """استرجاع تفاصيل منتج معين"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/products', methods=['POST'])
def create_product():
    """إضافة منتج جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['name', 'starting_price', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'الحقل {field} مطلوب'}), 400
        
        # التحقق من وجود المستخدم
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        # إنشاء المنتج الجديد
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            starting_price=data['starting_price'],
            category=data.get('category', ''),
            image_url=data.get('image_url', ''),
            user_id=data['user_id']
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """تحديث تفاصيل منتج موجود"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        
        data = request.get_json()
        
        # تحديث الحقول المرسلة فقط
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'starting_price' in data:
            product.starting_price = data['starting_price']
        if 'category' in data:
            product.category = data['category']
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'status' in data:
            product.status = data['status']
        
        db.session.commit()
        
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """حذف منتج"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({'message': 'تم حذف المنتج بنجاح'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/users/<user_id>/products', methods=['GET'])
def get_user_products(user_id):
    """استرجاع منتجات مستخدم معين"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'المستخدم غير موجود'}), 404
        
        products = Product.query.filter_by(user_id=user_id).all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

