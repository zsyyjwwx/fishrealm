from sqlalchemy import Column, String, CHAR, Integer, Text, Boolean, DateTime, func
import BaseSQL
from BaseSQL import base, engine, Session
from sqlalchemy import not_, and_, or_
from datetime import datetime,timedelta

USER_TABLE_NAME = "chat_info"

class ChatInfo(base):
    __tablename__ = USER_TABLE_NAME
    __table_args__ = {'extend_existing': True}
    file_id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    send_id = Column(CHAR(10), default=None, nullable=False)
    receive_id = Column(CHAR(10), default=None, nullable=False)
    message = Column(Text,default=None,nullable=False)
    is_read = Column(Boolean, default=None, nullable=False)
    date = Column(DateTime, default=None, nullable=False)


class ChatOperator(object):
    def __init__(self):
        self.session = Session()
        has_table = engine.dialect.has_table(engine.connect(), USER_TABLE_NAME)
        if not has_table:
            del_list = [ChatInfo.__table__]
            base.metadata.create_all(engine, tables=del_list)
            print("create table UserInfo success")

    def add(self, send_id, receive_id, message):
        self.session.add(ChatInfo(send_id=send_id,receive_id=receive_id,message=message,is_read=False,date=datetime.now()))
        self.session.commit()



    def set_history(self,receive_id,send_id):
        self.session.query(ChatInfo).filter(ChatInfo.send_id == send_id,ChatInfo.receive_id == receive_id,ChatInfo.is_read == False).update({ChatInfo.is_read : True})
        self.session.commit()


    def show(self,messages):
        for message in messages:
            print(message.send_id,message.receive_id,message.message,message.is_read,message.date)

    def get_user_receive(self,receive_id):
        messages = self.session.query(ChatInfo).filter(ChatInfo.receive_id == receive_id)

        return  messages

    def get_recently_message(self,receive_id,send_id):
        message = self.session.query(ChatInfo).filter(or_(and_(ChatInfo.receive_id==receive_id,ChatInfo.send_id==send_id),and_(ChatInfo.receive_id==send_id,ChatInfo.send_id==receive_id))).order_by(ChatInfo.date.desc()).first()

        return message

    def get_unread_count(self,receive_id,send_id):
        count = self.session.query(ChatInfo).filter(ChatInfo.receive_id == receive_id,ChatInfo.send_id == send_id,ChatInfo.is_read == False).count()
        return count

    def get_message_list(self,receive_id,send_id,N):
        messages = self.session.query(ChatInfo).filter(or_(and_(ChatInfo.receive_id==receive_id,ChatInfo.send_id==send_id),and_(ChatInfo.receive_id==send_id,ChatInfo.send_id==receive_id))).order_by(ChatInfo.date.desc()).limit(N).all()
        return messages


    def close(self):
        self.session.close()

    def connect(self):
        self.session = Session()
