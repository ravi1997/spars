from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from app.util.sms_service import send_otp
from app import db
from app.model import User, Otp
from app.schemas import user_schema
from app.util.generator import generate_jwt_token
from datetime import datetime
from . import auth_ns

# Models for Swagger documentation
otp_request_model = auth_ns.model('OtpRequest', {
    'mobile': fields.String(required=True, description='Mobile number to request OTP', default="9899378106")
})

otp_verify_model = auth_ns.model('OtpVerify', {
    'mobile': fields.String(required=True, description='Mobile number to verify OTP', default="9899378106"),
    'otp': fields.String(required=True, description='OTP received by the user')
})

# Responses for better documentation
otp_response_model = auth_ns.model('OtpResponse', {
    'message': fields.String(description='Response message'),
})

login_response_model = auth_ns.model('LoginResponse', {
    'message': fields.String(description='Response message'),
    'token': fields.String(description='JWT Token for authentication'),
    'user': fields.Raw(description='User object containing user details')
})


@auth_ns.route('/request_otp')
class RequestOtp(Resource):
    @auth_ns.expect(otp_request_model)
    @auth_ns.response(200, 'OTP sent successfully.', otp_response_model)
    @auth_ns.response(400, 'Mobile number is required.', otp_response_model)
    def post(self):
        """Request an OTP for login"""
        data = request.json
        if not data or 'mobile' not in data:
            db.session.rollback()
            return {"message": "Mobile number is required."}, 400

        mobile = data["mobile"]
        otp_value = Otp.create_otp(mobile)
        status = send_otp(mobile, otp_value)

        if status == 200:
            return {"message": "OTP sent successfully."}, 200
        return {"message": "Something went wrong, please try after some time."}, 400


@auth_ns.route('/verify_otp')
class VerifyOtp(Resource):
    @auth_ns.expect(otp_verify_model)
    @auth_ns.response(200, 'OTP verified successfully, login successful.', login_response_model)
    @auth_ns.response(400, 'Mobile number and OTP are required.', otp_response_model)
    @auth_ns.response(400, 'Invalid OTP or OTP already used.', otp_response_model)
    @auth_ns.response(400, 'OTP has expired.', otp_response_model)
    def post(self):
        """Verify the OTP and login the user"""
        data = request.json
        if not data or 'mobile' not in data or 'otp' not in data:
            db.session.rollback()
            return {"message": "Mobile number and OTP are required."}, 400

        otp = Otp.query.filter_by(mobile=data['mobile'], otp=data['otp'], is_verified=False).first()
        if not otp:
            db.session.rollback()
            return {"message": "Invalid OTP or OTP already used."}, 400

        if otp.expiration_time < datetime.utcnow():
            db.session.rollback()
            return {"message": "OTP has expired."}, 400

        otp.is_verified = True

        user = User.query.filter_by(mobile=data['mobile']).first()
        if not user:
            user = User(mobile=data['mobile'])
            db.session.add(user)

        db.session.commit()

        token = generate_jwt_token(user)

        return {
            "message": "OTP verified successfully, login successful.",
            "token": token,
            "user": user_schema.dump(user)
        }, 200
