from src.models.user import db
from datetime import datetime
import uuid

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    auction_id = db.Column(db.String(36), db.ForeignKey('auctions.id'), nullable=False)
    bid_id = db.Column(db.String(36), db.ForeignKey('bids.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    delivery_address = db.Column(db.Text)
    final_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, refunded
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'auction_id': self.auction_id,
            'bid_id': self.bid_id,
            'user_id': self.user_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'delivery_address': self.delivery_address,
            'final_price': float(self.final_price) if self.final_price else 0,
            'status': self.status,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Order {self.id} for {self.customer_name}>'

