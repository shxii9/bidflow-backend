from src.models.user import db
from datetime import datetime
import uuid

class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    auction_id = db.Column(db.String(36), db.ForeignKey('auctions.id'), nullable=False)
    bidder_name = db.Column(db.String(100), nullable=False)
    bidder_phone = db.Column(db.String(20), nullable=False)
    bid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    is_winning_bid = db.Column(db.Boolean, default=False)
    bid_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'auction_id': self.auction_id,
            'bidder_name': self.bidder_name,
            'bidder_phone': self.bidder_phone,
            'bid_amount': float(self.bid_amount) if self.bid_amount else 0,
            'is_winning_bid': self.is_winning_bid,
            'bid_time': self.bid_time.isoformat() if self.bid_time else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
    
    def __repr__(self):
        return f'<Bid {self.bid_amount} by {self.bidder_name}>'

