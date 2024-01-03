from flask import Blueprint
from flask_jwt_extended import jwt_required
from .services import *

telegrams = Blueprint('telegrams', __name__)

@telegrams.route('/create-telegram', methods=["POST"]) 
@jwt_required()
def create_telegram():
  return create_telegram_service()

@telegrams.route('/get-telegrams', methods=["GET"]) 
@jwt_required()
def get_telegrams():
  return get_telegrams_service()

@telegrams.route('/delete-telegram/<int:telegram_id>', methods=["delete"]) 
@jwt_required()
def delete_telegram(telegram_id):
  return delete_telegram_service(telegram_id)

@telegrams.route('/update-status-telegram/<int:telegram_id>', methods=["PUT"]) 
@jwt_required()
def update_status_telegram(telegram_id):
  return  update_status_telegram_service(telegram_id)

@telegrams.route('/send-message-test-telegram/<int:telegram_id>', methods=["POST"]) 
@jwt_required()
def send_message_test_telegram(telegram_id):
  return send_message_test_telegram_service(telegram_id)