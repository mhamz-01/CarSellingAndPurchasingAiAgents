from flask import Flask, request, jsonify , make_response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from models import db, User, CarDetails,BuyerAiAgent,SellerAiAgent
from flask import jsonify
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash
from flask_jwt_extended import create_access_token, JWTManager,jwt_required,get_jwt_identity
from groq import Groq
import socketio
import eventlet
import os
from werkzeug.utils import secure_filename
from datetime import datetime

eventlet.monkey_patch()

UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}



pymysql.install_as_MySQLdb()

groq_api_key="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"
# Initialize the Flask app
groq_client = Groq(api_key=groq_api_key)
sio = socketio.Server(cors_allowed_origins=['http://localhost:3000'])

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'aiagentselling123'  # Change this to a secure secret key
jwt = JWTManager(app)


CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
  # enable cross-origin for React


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:omniverse123@127.0.0.1:3306/Ai_Agent_carSellingAndPurchasing'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

db.init_app(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:3000")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print("Received registration data:", data)  # Debug log
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        # Validate required fields
        if not all([username, email, password, role]):
            print("Missing required fields")  # Debug log
            return jsonify({
                'message': 'All fields are required'
            }), 400

        # Check if user exists
        if User.query.filter_by(username=username).first():
            print(f"Username {username} already exists")  # Debug log
            return jsonify({
                'message': 'Username already exists'
            }), 409

        # Create new user
        try:
            
            new_user = User(
                username=username,
                email=email,
                password_hash=password,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Generate token
            access_token = create_access_token(identity=username)
            
            return jsonify({
                'message': 'Registration successful',
                'token': access_token
            }), 201

        except Exception as db_error:
            print("Database error:", str(db_error))  # Debug log
            db.session.rollback()
            return jsonify({
                'message': 'Database error occurred'
            }), 500

    except Exception as e:
        print("Registration error:", str(e))  # Debug log
        return jsonify({
            'message': 'Server error occurred',
            'error': str(e)
        }), 500
    


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("Received login data:", data)

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'message': 'Missing username or password'
            }), 400

        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.password_hash == data['password']:  
            # Create access token
            access_token = create_access_token(identity=user.username)
            return jsonify({
                'message': 'Login successful',
                'token': access_token,
                'username': user.username
            })
        
        return jsonify({
            'message': 'Invalid username or password'
        }), 401

    except Exception as e:
        print("Login error:", str(e))
        return jsonify({
            'message': 'Server error occurred'
        }), 500 
    
@app.route('/api/car-details', methods=['POST'])
@jwt_required()
def add_car_details():
    try:
        # Get current user's username from JWT
        current_user_username = get_jwt_identity()
        
        # Get user's ID from database
        user = User.query.filter_by(username=current_user_username).first()
        if not user:
            return jsonify({
                'message': 'User not found'
            }), 404

        data = request.form
        images = request.files.getlist('images')
        image_paths = []

        # Handle image uploads
        for image in images:
            if image and allowed_file(image.filename):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(f"{timestamp}_{image.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                image_paths.append(os.path.join('static', 'images', filename))

        # Create car details record with user.id instead of username
        new_car = CarDetails(
            seller_id=user.id,  # Use user.id instead of username
            car_company=data['car_company'],
            car_model=data['car_model'],
            car_bided_price=float(data['car_bided_price']),
            car_condition=data['car_condition'],
            car_mileage=float(data['car_mileage']),
            car_color=data['car_color'],
            phone_number=data['phone_number'],
            car_images=image_paths
        )

        db.session.add(new_car)
        db.session.commit()

        return jsonify({
            'message': 'Car details saved successfully',
            'car_id': new_car.car_id,
            'image_urls': [f"http://localhost:5000/{path}" for path in image_paths]
        }), 201

    except Exception as e:
        print("Error saving car details:", str(e))
        db.session.rollback()
        return jsonify({
            'message': 'Failed to save car details',
            'error': str(e)
        }), 500

@app.route('/api/cars', methods=['GET'])
def get_cars():
    try:
        # Query all cars from the database
        cars = CarDetails.query.all()
        
        # Convert cars to JSON-serializable format
        cars_list = []
        for car in cars:
            cars_list.append({
                'car_id': car.car_id,
                'car_company': car.car_company,
                'car_model': car.car_model,
                'car_bided_price': car.car_bided_price,
                'car_condition': car.car_condition,
                'car_mileage': car.car_mileage,
                'car_color': car.car_color,
                'car_images': car.car_images,
                'phone_number': car.phone_number,
                # Include seller details if needed
                'seller_username': car.seller.username if car.seller else None
            })

        return jsonify({
            'message': 'Cars fetched successfully',
            'cars': cars_list
        }), 200

    except Exception as e:
        print("Error fetching cars:", str(e))
        return jsonify({
            'message': 'Failed to fetch cars',
            'error': str(e)
        }), 500
    

@app.route('/api/cars/<int:car_id>', methods=['GET'])
def get_car_details(car_id):
    try:
        print(f"Fetching car with ID: {car_id}")  # Debug log
        car = CarDetails.query.get(car_id)
        
        if not car:
            print(f"No car found with ID: {car_id}")  # Debug log
            return jsonify({
                'message': f'Car with ID {car_id} not found'
            }), 404

        print(f"Found car: {car.car_company} {car.car_model}")  # Debug log

        return jsonify({
            'car': {
                'car_id': car.car_id,
                'car_company': car.car_company,
                'car_model': car.car_model,
                'car_bided_price': car.car_bided_price,
                'car_condition': car.car_condition,
                'car_mileage': car.car_mileage,
                'car_color': car.car_color,
                'car_images': car.car_images,
                'phone_number': car.phone_number,
                'seller_username': car.seller.username if car.seller else None
            }
        }), 200

    except Exception as e:
        print("Error fetching car details:", str(e))
        return jsonify({
            'message': 'Failed to fetch car details'
        }), 500
    
@app.route('/api/buyer-agent', methods=['POST'])
@jwt_required()
def create_buyer_agent():
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['car_id', 'my_upper_range', 'my_lower_range']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields'}), 400
            
        new_agent = BuyerAiAgent(
            car_id=data['car_id'],
            my_upper_range=data['my_upper_range'],
            my_lower_range=data['my_lower_range'],
            my_comments=data.get('my_comments', '')
        )
        
        db.session.add(new_agent)
        db.session.commit()
        
        return jsonify({
            'message': 'Buyer agent created successfully',
            'agent_id': new_agent.id
        }), 201
        
    except Exception as e:
        print("Error creating buyer agent:", str(e))
        db.session.rollback()
        return jsonify({
            'message': 'Failed to create buyer agent',
            'error': str(e)
        }), 500   


@app.route('/api/seller-agent', methods=['POST'])
@jwt_required()
def create_seller_agent():
    try:
        # Get current user from JWT token
        current_user = get_jwt_identity()
        seller = User.query.filter_by(username=current_user).first()

        if not seller or seller.role != 'seller':
            return jsonify({
                'message': 'Unauthorized - Seller access required'
            }), 403

        data = request.get_json()
        
        # Validate required fields
        required_fields = ['car_id', 'car_upper_price_range', 'car_lower_price_range', 'keypoints']
        if not all(field in data for field in required_fields):
            return jsonify({
                'message': 'Missing required fields'
            }), 400

        # Create seller agent
        new_agent = SellerAiAgent(
            car_id=data['car_id'],
            car_upper_price_range=data['car_upper_price_range'],
            car_lower_price_range=data['car_lower_price_range'],
            keypoints=data['keypoints']
        )

        db.session.add(new_agent)
        db.session.commit()

        return jsonify({
            'message': 'Seller agent created successfully',
            'agent_id': new_agent.id
        }), 201

    except Exception as e:
        print("Error creating seller agent:", str(e))
        db.session.rollback()
        return jsonify({
            'message': 'Failed to create seller agent',
            'error': str(e)
        }), 500
    


@app.route('/api/negotiation-details/<int:car_id>/<int:buyer_agent_id>', methods=['GET'])
@jwt_required()
def get_negotiation_details(car_id, buyer_agent_id):
    try:
        # Get all required details in one query
        seller_agent = SellerAiAgent.query.filter_by(car_id=car_id).first()
        buyer_agent = BuyerAiAgent.query.get(buyer_agent_id)
        car = CarDetails.query.get(car_id)

        if not all([seller_agent, buyer_agent, car]):
            return jsonify({
                'message': 'Required details not found'
            }), 404

        # Compile all details
        negotiation_data = {
            'car_details': {
                'company': car.car_company,
                'model': car.car_model,
                'asking_price': car.car_bided_price,
                'condition': car.car_condition,
                'mileage': car.car_mileage,
                'color': car.car_color
            },
            'seller_agent': {
                'id': seller_agent.id,
                'upper_range': seller_agent.car_upper_price_range,
                'lower_range': seller_agent.car_lower_price_range,
                'keypoints': seller_agent.keypoints
            },
            'buyer_agent': {
                'id': buyer_agent.id,
                'upper_range': buyer_agent.my_upper_range,
                'lower_range': buyer_agent.my_lower_range,
                'comments': buyer_agent.my_comments
            }
        }

        # Initialize Groq chat with context
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an AI mediator managing a car negotiation:
                        Car: {car.car_company} {car.car_model}
                        Current Price: ${car.car_bided_price}
                        Condition: {car.car_condition}
                        Mileage: {car.car_mileage}km

                        Seller's Range: ${seller_agent.car_lower_price_range}-${seller_agent.car_upper_price_range}
                        Seller's Key Points: {seller_agent.keypoints}

                        Buyer's Range: ${buyer_agent.my_lower_range}-${buyer_agent.my_upper_range}
                        Buyer's Comments: {buyer_agent.my_comments}
                    """
                },
                {
                    "role": "user",
                    "content": "Begin the negotiation between buyer and seller."
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        # Add initial AI message to response
        negotiation_data['initial_message'] = chat_completion.choices[0].message.content

        return jsonify(negotiation_data), 200

    except Exception as e:
        print("Error fetching negotiation details:", str(e))
        return jsonify({
            'message': 'Failed to fetch negotiation details'
        }), 500

# WebSocket handlers for real-time chat
@sio.on('connect')
def connect(sid, environ):
    print(f'Client connected: {sid}')

@sio.on('negotiate')
def handle_negotiation(sid, data):
    try:
        # Get context from data
        car_id = data['car_id']
        buyer_agent_id = data['buyer_agent_id']
        message = data['message']

        # Fetch current context
        seller_agent = SellerAiAgent.query.filter_by(car_id=car_id).first()
        buyer_agent = BuyerAiAgent.query.get(buyer_agent_id)
        car = CarDetails.query.get(car_id)

        # Continue chat with context
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Continue the car negotiation based on previous context."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        response = chat_completion.choices[0].message.content
        sio.emit('negotiation_response', {'response': response}, room=sid)

    except Exception as e:
        print(f"Error in negotiation: {str(e)}")
        sio.emit('error', {'message': 'Negotiation error occurred'}, room=sid)

@sio.on('disconnect')
def disconnect(sid):
    print(f'Client disconnected: {sid}')



if __name__ == '__main__':
    with app.app_context():
          
        db.create_all()
        print("Database tables created successfully!")  # Debug message
    eventlet.wsgi.server(
        eventlet.listen(('0.0.0.0', 5000)), 
        app,
        debug=True
    )    
    app.run(debug=True)