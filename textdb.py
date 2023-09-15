from sqlalchemy import Column, String,CHAR,Integer,Text,Boolean,DateTime,func
import BaseSQL
from BaseSQL import base,engine,Session
from sqlalchemy import not_,and_,or_
USER_TABLE_NAME = "text_md"

class Textmd(base):
    
    __tablename__ = USER_TABLE_NAME
    __table_args__ = {'extend_existing': True}

    text_id = Column(Integer,autoincrement=True,primary_key=True,nullable=False)
    user_id = Column(CHAR(10),default=None,nullable=False)
    title = Column(String(50),default=None,nullable=False)
    content = Column(Text,default=None,nullable=False)
    ispublic = Column(Boolean,default=None,nullable=False)
    date = Column(DateTime,default=None,nullable=False)


class TextmdOperator(object):
    def __init__(self):
        self.session = Session()
        has_table = engine.dialect.has_table(engine.connect(),USER_TABLE_NAME)
        if not has_table:
            del_list =[Textmd.__table__]
            base.metadata.create_all(engine,tables=del_list)
            print("create table UserInfo success")

    def add(self,user_id,title,content,ispublic,date):
        self.session.add(Textmd(user_id=user_id,title=title,content=content,ispublic=ispublic,date=date))
        self.session.commit()
        self.session.close()

    def is_text_id(self,text_id):
        texts = self.session.query(Textmd).filter(Textmd.text_id == text_id)
        self.session.close()
        for text in texts:
            # print(user.id,user.pwd,user.privilege)
            return True
        return False

    def get_text(self,text_id):
        result = self.session.query(Textmd).filter(Textmd.text_id==text_id).first()
        self.session.close()
        return result
    #个人查询
    def query_user_id(self,user_id):
        texts = self.session.query(Textmd).filter(Textmd.user_id == user_id)
        self.session.close()
        return texts

    def query_title(self,title):
        texts = self.session.query(Textmd).filter(Textmd.title == title)
        self.session.close()
        return texts
    #公开查询
    def query_public_user_id(self,user_id):
        texts = self.session.query(Textmd).filter(Textmd.user_id == user_id,Textmd.ispublic==True)
        self.session.close()
        return texts

    def query_public_title(self,title):
        texts = self.session.query(Textmd).filter(Textmd.title == title,Textmd.ispublic==True)
        self.session.close()
        return texts

    def count(self):
        result = self.session.query(func.count(Textmd.text_id)).scalar()
        self.session()
        return result
        
    def count_public(self):
        result = self.session.query(func.count(Textmd.text_id)).filter(Textmd.ispublic==True).scalar()
        self.session.close()
        return result
        
    def count_user(self,user_id):
        result = self.session.query(func.count(Textmd.text_id)).filter(Textmd.user_id==user_id).scalar()
        self.session.close()
        return result
        
    def count_public_user(self,user_id):
        result = self.session.query(func.count(Textmd.text_id)).filter(Textmd.user_id==user_id,Textmd.ispublic == True).scalar()
        self.session.close()
        return result
        
    def get_public_item(self,first,num):
        result = self.session.query(Textmd).filter(Textmd.ispublic==True).order_by(Textmd.text_id.desc()).offset(first).limit(num).all()
        self.session.close()
        return result
        
    def get_user_item(self,user_id):
        result = self.session.query(Textmd).filter(Textmd.user_id==user_id).order_by(Textmd.date.desc()).all()
        self.session.close()
        return result
        
    def delete(self,text_id):
        if self.is_text_id(text_id):
            text = self.session.query(Textmd).filter(Textmd.text_id == text_id).first()
            self.session.delete(text)
            self.session.commit()
            self.session.close()
            return True
        return False

    def setpublic(self,text_id):
        if self.is_text_id(text_id):
            text = self.session.query(Textmd).filter(Textmd.text_id == text_id).first()
            text.ispublic = not text.ispublic
            self.session.add(text)
            self.session.commit()
            self.session.close()
            return True
        return False

    def revise(self,text_id,title,content,ispublic,date):
        if self.is_text_id(text_id):
            text = self.session.query(Textmd).filter(Textmd.text_id == text_id).first()
            text.title=title
            text.content=content
            text.ispublic=ispublic
            text.date=date
            self.session.add(text)
            self.session.commit()
            self.session.close()
            return True
        return False


    def close(self):
        self.session.close()
        
    def connect(self):
        self.session = Session()
