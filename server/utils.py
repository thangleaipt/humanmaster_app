from server.config import SECRET_KEY, SENDER_EMAIL, PASSWORD_EMAIL, SMTP_SERVER, SMTP_PORT, TELEGRAM_TOKEN
import jwt
import telepot

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

bot = telepot.Bot(TELEGRAM_TOKEN) 
    
def verify_authorization(token):
  try:
    token = f"{token}".replace('Bearer ', '')
    data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    
    if data is not None:
      return True
    else:
      return False
  except Exception:
    return False
  
def get_file_extension(filename):
  return f"{filename}".split(".")[::-1][0]

def send_email(recipient_email, subject, content):
  msg = MIMEMultipart()
  msg['Subject'] = subject
  msg['From'] = SENDER_EMAIL
  msg['To'] = recipient_email
  msg['Content-Language'] = 'vi'
  msg.attach(MIMEText(content, 'html'))

  with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
    smtp.starttls()
    smtp.login(SENDER_EMAIL, PASSWORD_EMAIL)
    smtp.sendmail(SENDER_EMAIL, [recipient_email], msg.as_string())

def get_file_extension(filename):
  return f"{filename}".split(".")[::-1][0]

def telegram_send_text_message(text_message, telegrams):
  try:
    for telegram in telegrams:
      formatted_message = f"_{text_message}_"
      bot.sendMessage(telegram.chat_id, formatted_message , parse_mode= 'Markdown' )  

  except Exception as ex:
    raise Exception('Lỗi ', ex)
