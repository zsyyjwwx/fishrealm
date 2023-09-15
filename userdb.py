from sqlalchemy import Column, String,CHAR,Integer,Text
import BaseSQL
from BaseSQL import base,engine,Session
from sqlalchemy import not_,and_,or_
USER_TABLE_NAME = "user_info"

class UserInfo(base):
    __tablename__ = USER_TABLE_NAME
    __table_args__ = {'extend_existing': True}

    id = Column(CHAR(10), primary_key=True, unique=True)
    pwd = Column(CHAR(10), default=None, nullable=False)
    privilege = Column(Integer, default=None, nullable=False)
    link = Column(Text, default=None, nullable=True)
class UserOperator(object):
    def __init__(self):
        self.session = Session()
        has_table = engine.dialect.has_table(engine.connect(),USER_TABLE_NAME)
        if not has_table:
            del_list =[UserInfo.__table__]
            base.metadata.create_all(engine,tables=del_list)
            print("create table UserInfo success")

    def add(self,id,pwd,privilege):
        self.session.add(UserInfo(id=id,pwd=pwd,privilege=privilege,link='NULL'))
        self.session.commit()
        self.close()

    def get_id_list(self):
        user_list = self.session.query(UserInfo).filter()
        id_list = []
        for user in user_list:
            id_list.append(user.id)
        return id_list


    def reset_privilege(self,id,privilege):
        if not self.isid(id):
            return False
        user = self.session.query(UserInfo).filter(UserInfo.id == id).first()
        user.privilege =privilege
        self.session.add(user)
        self.session.commit()
        self.close()

    def is_link(self,id):
        if not self.isid(id):
            return False
        user = self.session.query(UserInfo).filter(UserInfo.id == id).first()
        self.close()
        return user.link

    def set_link(self,id,link):
        if not  self.isid(id):
            return False
        user = self.session.query(UserInfo).filter(UserInfo.id == id).first()
        user.link = link
        self.session.add(user)
        self.session.commit()
        self.close()



    #判断是否已存在id
    def isid(self,id):
        users = self.session.query(UserInfo).filter(UserInfo.id==id)
        self.close()
        for user in users:
            #print(user.id,user.pwd,user.privilege)
            return True
        return False

    def isid_pwd(self,id,pwd):
        users = self.session.query(UserInfo).filter(UserInfo.id == id,UserInfo.pwd==pwd)
        for user in users:
            #print(user.id, user.pwd, user.privilege)
            return True
        return False

    def delete_user(self,id):
        if self.isid(id):
            user = self.session.query(UserInfo).filter(UserInfo.id == id).first()
            self.session.delete(user)
            self.session.commit()
            self.close()
            return True
        return False

    def login(self,id,pwd):
        if self.isid_pwd(id,pwd):
            return True
        return False

    def register(self,id,pwd):
        if self.isid(id):
            return False
        self.add(id,pwd,0)
        return True

    def reset_pwd(self,id,old_pwd,new_pwd):
        if self.isid_pwd(id,old_pwd):
            user = self.session.query(UserInfo).filter(UserInfo.id == id,UserInfo.pwd == old_pwd).first()
            user.pwd = new_pwd
            self.session.add(user)
            self.session.commit()
            self.close()
            return True
        return False
        
    def close(self):
        self.session.close()
        
    def connect(self):
        self.session = Session()
        
        
    def get_privilege_text(self,id):
        if self.isid(id):
            user = self.session.query(UserInfo).filter((UserInfo.id == id)).first()
            if user.privilege == 1:
                return 'Fish Member'
            elif user.privilege == 2:
                return  'FishCouncilor'
            elif user.privilege == 3:
                return 'Administrator'
        return 'Unknown'


