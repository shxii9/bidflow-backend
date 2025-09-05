from flask import Blueprint, request, jsonify, send_file
import qrcode
from io import BytesIO
import base64
from ..models.auction import Auction
from ..models.product import Product
from ..models.user import db

qr_bp = Blueprint('qr', __name__)

@qr_bp.route('/auctions/<auction_id>/qr', methods=['GET'])
def generate_auction_qr(auction_id):
    """توليد QR Code للمزاد"""
    try:
        # التحقق من وجود المزاد
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        # الحصول على معلومات المنتج
        product = Product.query.get(auction.product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        
        # إنشاء رابط المزاد
        auction_url = f"http://localhost:5174/auction/{auction_id}"
        
        # إنشاء QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(auction_url)
        qr.make(fit=True)
        
        # إنشاء الصورة
        img = qr.make_image(fill_color="black", back_color="white")
        
        # تحويل الصورة إلى bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # إرجاع الصورة كـ base64 أو ملف
        format_type = request.args.get('format', 'file')
        
        if format_type == 'base64':
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            return jsonify({
                'qr_code': f"data:image/png;base64,{img_base64}",
                'auction_url': auction_url,
                'product_name': product.name,
                'auction_id': auction_id
            })
        else:
            return send_file(
                img_buffer,
                mimetype='image/png',
                as_attachment=False,
                download_name=f'auction_{auction_id[:8]}_qr.png'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_bp.route('/auctions/<auction_id>/qr-info', methods=['GET'])
def get_qr_info(auction_id):
    """الحصول على معلومات QR Code للمزاد"""
    try:
        # التحقق من وجود المزاد
        auction = Auction.query.get(auction_id)
        if not auction:
            return jsonify({'error': 'المزاد غير موجود'}), 404
        
        # الحصول على معلومات المنتج
        product = Product.query.get(auction.product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        
        # إنشاء رابط المزاد
        auction_url = f"http://localhost:5174/auction/{auction_id}"
        
        return jsonify({
            'auction_id': auction_id,
            'auction_url': auction_url,
            'product_name': product.name,
            'product_description': product.description,
            'starting_price': float(auction.starting_price),
            'current_highest_bid': float(auction.current_highest_bid) if auction.current_highest_bid else None,
            'status': auction.status,
            'qr_download_url': f"/api/qr/auctions/{auction_id}/qr",
            'qr_base64_url': f"/api/qr/auctions/{auction_id}/qr?format=base64"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@qr_bp.route('/products/<product_id>/qr-preview', methods=['GET'])
def generate_product_qr_preview(product_id):
    """توليد QR Code معاينة للمنتج (قبل بدء المزاد)"""
    try:
        # التحقق من وجود المنتج
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'المنتج غير موجود'}), 404
        
        # إنشاء رابط معاينة
        preview_url = f"http://localhost:5174/product/{product_id}/preview"
        
        # إنشاء QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(preview_url)
        qr.make(fit=True)
        
        # إنشاء الصورة
        img = qr.make_image(fill_color="black", back_color="white")
        
        # تحويل الصورة إلى bytes
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # إرجاع الصورة كـ base64 أو ملف
        format_type = request.args.get('format', 'file')
        
        if format_type == 'base64':
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            return jsonify({
                'qr_code': f"data:image/png;base64,{img_base64}",
                'preview_url': preview_url,
                'product_name': product.name,
                'product_id': product_id
            })
        else:
            return send_file(
                img_buffer,
                mimetype='image/png',
                as_attachment=False,
                download_name=f'product_{product_id[:8]}_preview_qr.png'
            )
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

