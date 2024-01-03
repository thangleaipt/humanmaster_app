from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from server.extension import db_session
from server.ma_schemas import TelegramsSchema
from server.models import Telegram, User
from server.utils import telegram_send_text_message

telegrams_schema = TelegramsSchema(many=True)


def query_telegrams_by_user():
  user_id = get_jwt_identity()['user_id']

  session = db_session()
  telegrams = session.query(
    Telegram.id.label('id'),
    Telegram.name.label('name'),
    Telegram.status,
    Telegram.chat_id,
    User.name.label('user_created')
  ).join(
    User, Telegram.user_id == User.id
  ).filter(
    Telegram.user_id == user_id
  ).all()
  
  session.close()

  return telegrams_schema.dump(telegrams)

def create_telegram_service(chat_id, user_id, name):
  session = db_session()

  try:
    count = session.query(Telegram).filter(Telegram.chat_id == chat_id).count()
    if count == 0:
      telegram = Telegram(chat_id, name, 1, user_id)
      session.add(telegram)
      session.commit()

      data = query_telegrams_by_user()

      return jsonify({
        "message": f"Thêm telegram {name} thành công",
        "telegrams": data
      })
    
    else:
      return jsonify({
        "message": f"Telegram {chat_id} đã tồn tại",
        "error": f"Telegram {chat_id} đã tồn tại"
      }), 400
  
  except KeyError:
    return jsonify({"message": "Bad request !"}), 400
  
  except Exception as e:
    return jsonify({
      "message": "Bad request !",
      "error": f"{e.args}"
    }), 400

  finally:
    session.close()

def get_telegrams_service():
  return query_telegrams_by_user(), 200

def get_telegrams():
      session = db_session()
      telegrams = session.query(Telegram).filter(Telegram.status == 1).all()
      session.close()
      return telegrams

def delete_telegram_service(telegram_id):
  session = db_session()
  telegram = session.query(Telegram).filter(Telegram.id == telegram_id)

  if telegram.count() == 1:
    telegram_name = telegram.first().name
    telegram.delete()
    session.commit()

    data = query_telegrams_by_user()
    res = jsonify({
      "message": f"Xóa telegram {telegram_name} thành công",
      "telegrams": data
    }), 200
  
  else:
    res = jsonify({
      "message": f"Bad request !",
      "error": f"Không tìm thấy telegram #{telegram_id}"
    }), 400

  session.close()
  return res

def update_status_telegram_service(telegram_id):
  session = db_session()
  telegram = session.query(Telegram).filter(Telegram.id == telegram_id)

  if telegram.count() == 1:
    telegram_name = telegram.first().name
    current_status = telegram.first().status
    
    if  current_status == 1:
      telegram.update({Telegram.status: 0})

    else:
      telegram.update({Telegram.status: 1})

    session.commit()

    data = query_telegrams_by_user()
    res = jsonify({
      "message": f"Cập nhật trạng thái telegram {telegram_name} thành công",
      "telegrams": data
    }), 200

  else:
    res = jsonify({
      "message": f"Không tìm thấy telegram #{telegram_id}",
      "error": f"Không tìm thấy telegram #{telegram_id}"
    }), 400

  session.close()
  return res

def send_message_test_telegram_service(telegram_id):
  session = db_session()
  telegram = session.query(Telegram).filter(Telegram.id == telegram_id)

  if telegram.count() == 1:
    text_message = 'Vehicle Master xin chào !'
    telegram_send_text_message(text_message, telegram)
    res = jsonify({"message": f"Đã gửi tin nhắn test đến telegram {telegram.first().name}"}), 200
    
  else:
    res = jsonify({
      "message": f"Không tìm thấy telegram #{telegram_id}",
      "error": f"Không tìm thấy telegram #{telegram_id}"
    }), 400

  session.close()
  return res