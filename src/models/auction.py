from src.models.user import db
from datetime import datetime
import uuid

class Auction(db.Model):
    __tablename__ = 'auctions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, ended, cancelled
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    starting_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_highest_bid = db.Column(db.Numeric(10, 2))
    winner_bid_id = db.Column(db.String(36))
    total_bids = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'starting_price': float(self.starting_price) if self.starting_price else 0,
            'current_highest_bid': float(self.current_highest_bid) if self.current_highest_bid else None,
            'winner_bid_id': self.winner_bid_id,
            'total_bids': self.total_bids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Auction {self.id} for Product {self.product_id}>'

