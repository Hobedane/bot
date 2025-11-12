from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    image1_path = Column(String(500))  # First image sent after payment
    image2_path = Column(String(500))  # Second image sent after payment
    coordinates = Column(String(255))  # Coordinates sent after payment
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    customer_id = Column(Integer, nullable=False)
    customer_username = Column(String(255))
    customer_crypto_address = Column(String(255), nullable=False)
    payment_token = Column(String(10), nullable=False)  # USDT or USDC
    blockchain = Column(String(20), nullable=False)  # polygon, solana, or bsc
    transaction_hash = Column(String(255))
    status = Column(String(20), default='pending')  # pending, confirmed, rejected, completed
    created_at = Column(DateTime, default=datetime.now)
    confirmed_at = Column(DateTime)
    admin_id = Column(Integer)

# Database setup
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'shop_bot.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
engine = create_engine(f'sqlite:///{db_path}')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
