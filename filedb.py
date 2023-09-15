import os

from sqlalchemy import Column, String, CHAR, Integer, Text, Boolean, DateTime, func
import BaseSQL
from BaseSQL import base, engine, Session
from sqlalchemy import not_, and_, or_

USER_TABLE_NAME = "FileInfo"
from basefunction import *

class FileInfo(base):
    __tablename__ = USER_TABLE_NAME
    __table_args__ = {'extend_existing': True}
    file_id = Column(Integer, autoincrement=True, primary_key=True, nullable=False)
    filename = Column(String(50), default=None, nullable=False)
    filepath = Column(Text, default=None, nullable=False)
    privilege = Column(String(20), default=None, nullable=False)
    owner = Column(CHAR(10), default=None, nullable=False)


class FileOperator(object):
    def __init__(self):
        self.session = Session()
        has_table = engine.dialect.has_table(engine.connect(), USER_TABLE_NAME)
        if not has_table:
            del_list = [FileInfo.__table__]
            base.metadata.create_all(engine, tables=del_list)
            print("create table UserInfo success")
            self.add('public','./static','共享','root')

    def add(self, filename, filepath, privilege, owner):
        if self.is_text_id(filename,filepath):
            return
        self.session.add(FileInfo(filename=filename, filepath=filepath, privilege=privilege, owner=owner))
        self.session.commit()
        self.session.close()

    def is_text_id(self,filename,filepath):
        texts = self.session.query(FileInfo).filter(FileInfo.filename == filename,FileInfo.filepath == filepath)
        self.session.close()
        for text in texts:
            # print(user.id,user.pwd,user.privilege)
            return True
        return False

    def get_FileInfo(self, filename,filepath):
        if not self.is_text_id(filename,filepath):
            return
        result = self.session.query(FileInfo).filter(FileInfo.filename == filename,FileInfo.filepath==filepath).first()
        self.session.close()
        return result

    def get_owner(self, filename,filepath):
        if not self.is_text_id(filename,filepath):
            return
        result = self.session.query(FileInfo).filter(FileInfo.filename == filename,FileInfo.filepath==filepath).first()
        self.session.close()
        return result.owner

    def get_privilege(self, filename,filepath):
        if not self.is_text_id(filename,filepath):
            return
        result = self.session.query(FileInfo).filter(FileInfo.filename == filename,FileInfo.filepath==filepath).first()
        self.session.close()
        return result.privilege

    def delete(self,filename,filepath):
        if self.is_text_id(filename,filepath):
            result = self.session.query(FileInfo).filter(FileInfo.filename == filename,FileInfo.filepath==filepath).first()
            self.session.delete(result)
            self.session.commit()
            self.session.close()
            return True
        return False

    def revise_filename(self,filename, filepath, new_filename):
        if self.is_text_id(filename, filepath):
            fileinfo = self.session.query(FileInfo).filter(FileInfo.filename == filename,FileInfo.filepath == filepath).first()
            fileinfo.filename = new_filename
            self.session.add(fileinfo)
            self.session.commit()
            self.session.close()
            return True
        return False

    def addpath(self,dirpath, privilege, owner):
        dir = os.path.dirname(dirpath)

        while len(dir) and dir[-1] == '/':
            dir = dir[:-1]
        while len(dirpath) and dirpath[-1] == '/':
            dirpath = dirpath[:-1]

        self.add(filename=os.path.basename(dirpath),filepath=dir,privilege=privilege,owner=owner)
        del_list = os.listdir(dirpath)
        for f in del_list:
            file_path = dirpath + '/' + f
            if os.path.isfile(file_path):
                self.add(filename=f, filepath=dirpath, privilege=privilege, owner=owner)
            else:
                self.addpath(file_path,privilege,owner)

    def close(self):
        self.session.close()

    def connect(self):
        self.session = Session()
