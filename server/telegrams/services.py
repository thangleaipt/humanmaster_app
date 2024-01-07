from flask import request, jsonify
from server.extension import db_session
from server.ma_schemas import TelegramsSchema
from server.models import Telegram
from server.utils import telegram_send_text_message

telegrams_schema = TelegramsSchema(many=True)

def create_telegram(chat_id, name):
  session = db_session()

  try:
    count = session.query(Telegram).filter(Telegram.chat_id == chat_id).count()
    if count == 0:
      telegram = Telegram(chat_id, name, 1)
      session.add(telegram)
  except Exception as e:
    session.rollback()
  finally:
    session.commit()
    session.close()

def get_list_telegrams_db():
      try:
        session = db_session()
        telegrams = session.query(Telegram).filter(Telegram.status == 1).all()
        return telegrams
      except Exception as ex:
        raise Exception('Lỗi ', ex)
      finally:
        session.close()

def delete_telegram_service(telegram_id):
  session = db_session()
  telegram = session.query(Telegram).filter(Telegram.chat_id == telegram_id)

  if telegram.count() == 1:
    telegram_name = telegram.first().name
    telegram.delete()
    session.commit()
  session.close()

def update_status_telegram_service(telegram_id):
  session = db_session()
  telegram = session.query(Telegram).filter(Telegram.chat_id == telegram_id)

  if telegram.count() == 1:
    telegram_name = telegram.first().name
    current_status = telegram.first().status
    
    if  current_status == 1:
      telegram.update({Telegram.status: 0})

    else:
      telegram.update({Telegram.status: 1})

    session.commit()

  session.close()

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