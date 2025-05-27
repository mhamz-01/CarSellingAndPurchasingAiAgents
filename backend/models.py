import mysql.connector
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash



db = SQLAlchemy()

# -----USER TABLE-----

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(1000), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'buyer' or 'seller'

# -----USER TABLE-----






# -----CAR DETAILS TABLE-----

class CarDetails(db.Model):
    __tablename__ = 'car_details'
    
    car_id = db.Column(db.Integer, primary_key=True)
    # Foreign key to link with User table
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_company = db.Column(db.String(100), nullable=False)
    car_model = db.Column(db.String(100), nullable=False)
    car_bided_price = db.Column(db.Float, nullable=False)
    car_condition = db.Column(db.String(100), nullable=False)
    car_mileage = db.Column(db.Float, nullable=False)
    car_color = db.Column(db.String(100), nullable=False)
    car_images = db.Column(db.JSON)
    phone_number = db.Column(db.String(20), nullable=False)
    
    # Relationship with User model
    seller = db.relationship('User', backref=db.backref('cars', lazy=True))

    

# -----CAR DETAILS TABLE-----







# -----SELLER AI AGENT TABLES-----

class SellerAiAgent(db.Model):
    __tablename__ = 'seller_ai_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key to link with CarDetails table
    car_id = db.Column(db.Integer, db.ForeignKey('car_details.car_id'), nullable=False)
    car_upper_price_range = db.Column(db.Integer, nullable=False)
    car_lower_price_range = db.Column(db.Integer, nullable=False)
    keypoints = db.Column(db.String(100), nullable=False)

    # Relationship with CarDetails model
    car_details = db.relationship('CarDetails', backref=db.backref('ai_agent', lazy=True))

    # This allows you to access car and seller details through relationships
    @property
    def seller_username(self):
        return self.car_details.seller.username

    @property
    def car_model(self):
        return self.car_details.car_model

    @property
    def car_company(self):
        return self.car_details.car_company

    @property
    def car_condition(self):
        return self.car_details.car_condition

    @property
    def car_listed_price(self):
        return self.car_details.car_bided_price

    @property
    def car_mileage(self):
        return self.car_details.car_mileage

# -----SELLER AI AGENT TABLES-----






# -----BUYER AI AGENT TABLES-----

class BuyerAiAgent(db.Model):
    __tablename__ = 'buyer_ai_agent'
    
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key to link with CarDetails table
    car_id = db.Column(db.Integer, db.ForeignKey('car_details.car_id'), nullable=False)
    my_upper_range = db.Column(db.Integer, nullable=False)
    my_lower_range = db.Column(db.Integer, nullable=False)
    my_comments = db.Column(db.String(500), nullable=True)

    # Relationship with CarDetails model
    car_details = db.relationship('CarDetails', backref=db.backref('buyer_ai_agent', lazy=True))

    # Properties to access CarDetails information
    @property
    def car_company(self):
        return self.car_details.car_company

    @property
    def car_model(self):
        return self.car_details.car_model

    @property
    def asking_price(self):
        return self.car_details.car_bided_price

    @property
    def car_mileage(self):
        return self.car_details.car_mileage

    @property
    def car_condition(self):
        return self.car_details.car_condition
    
# -----BUYER AI AGENT TABLES-----



# Database connection

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='omniverse123',
        database='Ai_Agent_carSellingAndPurchasing'
    )
    return connection
