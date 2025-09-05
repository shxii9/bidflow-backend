from src.models.user import db
from datetime import datetime
import uuid

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    starting_price = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    qr_code_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='draft')  # draft, active, sold, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'starting_price': float(self.starting_price) if self.starting_price else 0,
            'category': self.category,
            'image_url': self.image_url,
            'qr_code_url': self.qr_code_url,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'

