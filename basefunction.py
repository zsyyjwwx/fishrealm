from time import sleep
from flask import session,jsonify
from datetime import datetime
import pytz
import os
import string
import random
import shutil
import zipfile


def wait_web(s=1.2):
    sleep(s)
def is_session():
    return session.get('id') and session.get('pwd')

def is_session_path():
    return session.get('filepath') and session.get('filename')

def set_session(id,pwd):

    if is_session():
        session.pop('id')
        session.pop('pwd')
    session['id'] = id
    session['pwd'] =pwd

def set_session_path(filepath,filename):

    if is_session_path():
        session.pop('filepath')
        session.pop('filename')
    session['filepath'] = filepath
    session['filename'] = filename

def get_session_path():
    filepath = session.get('filepath')
    filename = session.get('filename')
    return (filepath,filename)

def delete_session_path():
    if is_session_path():
        session.pop('filepath')
        session.pop('filename')

def get_session():
    id = session.get('id')
    pwd =session.get('pwd')
    return (id,pwd)

def delete_session():
    if is_session():
        session.pop('id')
        session.pop('pwd')
        
def get_user_path(id):
    path_1 = './static/upload/' + id + '/user_avatar/'
    path_2 = './static/upload/' + id + '/website_background/'
    user_avatar_path = '../static/image/user_avatar.PNG'
    website_background_path ='../static/music/Eve.mp3'
    if os.path.exists(path_1):
        user_avatar_path = '../static/upload/' + id + '/user_avatar/' + os.listdir(path_1)[0]
    if os.path.exists(path_2):
        website_background_path = '../static/upload/' + id + '/website_background/' + os.listdir(path_2)[0]

    return (user_avatar_path,website_background_path)

def add_user_dir(id):
    path = './static/upload/' + id
    if not os.path.exists(path):
        os.makedirs(path, 0o777)

def clear_path(path):
    if not os.path.exists(path):
        os.makedirs(path, 0o777)
        return
    del_list = os.listdir(path)
    for f in del_list:
        file_path = os.path.join(path, f)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            shutil.rmtree(file_path)


def zipDir(dirpath, outdir,Name):
    """
    压缩指定文件夹
    :param dirpath: 目标文件夹路径
    :param outFullName: 压缩文件保存路径+xxxx.zip
    :return: 无
    """
    clear_path(outdir)
    outFullName = outdir + Name
    zip = zipfile.ZipFile(outFullName, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(dirpath):
        # 去掉目标跟路径，只对目标文件夹下边的文件及文件夹进行压缩
        fpath = path.replace(dirpath, '')

        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()


def unzip(file_name):
    """
    解压缩zip文件至同名文件夹
    """
    outfilename = file_name.replace('.zip','')
    tmp = outfilename
    i = 0
    while os.path.exists(tmp):
        i = i + 1
        tmp = outfilename + '(' + str(i) + ')'
    outfilename = tmp

    zip_ref = zipfile.ZipFile(file_name) # 创建zip 对象
    os.mkdir(outfilename,0o777) # 创建同名子文件夹
    zip_ref.extractall(outfilename) # 解压zip文件内容到子文件夹
    zip_ref.close() # 关闭zip文件

    return outfilename


def delete_fileordir(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            clear_path(path)
            shutil.rmtree(path)
        else:
            os.remove(path)

def get_privilege(path,id):
    if path.find('./static/upload/' + id) != -1:
        return '私有'
    if path.find('./static/upload/') != -1:
        return '私有'
    if path.find('./static/public/') != -1:
        return '共享'

    return '未知'

def add_random_path(path):

    random_string = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8))
    random_string = '新建文件夹'+ random_string
    filepath = path + '/' + random_string
    if not os.path.exists(filepath):
        os.makedirs(filepath, 0o777)
        print("创建成功", filepath)
    return random_string

def dir_and_file_tree(path,temp_list):
    path_tree = os.listdir(path)     #获取当前目录下的文件和目录
    for item in path_tree:
        subtree= path+'\\'+item
        if os.path.isdir(subtree):      #判断是否为目录
            x1=[]
            item_dict={'name':item,'children':x1}
            temp_list.append(item_dict)
            dir_and_file_tree(subtree,x1)   #递归深度优先遍历
        else:
            temp_list.append({'name':item})
    return temp_list

def hum_convert(value):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size

def get_filename_list(id,path,file_operator):

    path_list = os.listdir(path)  # 获取当前目录下的文件和目录
    data = []
    item = {}
    for filename in path_list:
        pathTmp = os.path.join(path, filename)  # 获取path与filename组合后的路径

        item['filename'] = filename
        if os.path.isdir(pathTmp):  # 判断是否为目录
            datasize = '文件夹'
        elif os.path.isfile(pathTmp):  # 判断是否为文件
            datasize = os.path.getsize(pathTmp)  # 如果是文件，则获取相应文件的大小
            datasize = hum_convert(datasize)
        ctime = os.path.getctime(pathTmp)  # 创建时间
        ctime_string = datetime.fromtimestamp(int(ctime),pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M")
        mtime = os.path.getmtime(pathTmp)  # 修改时间
        mtime_string = datetime.fromtimestamp(int(mtime),pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M")
        data.append({
            'filename':filename,
            'datasize' :datasize,
            'cdatetime':ctime_string,
            'mdatetime': mtime_string,
            'privilege':  file_operator.get_privilege(filename=filename,filepath=path),
            'owner': file_operator.get_owner(filename=filename,filepath=path),
            'path': path
        })
    return data

def get_root_filelist(id):
    pathTmp = './static/public'
    ctime = os.path.getctime(pathTmp)  # 创建时间
    ctime_string = datetime.fromtimestamp(int(ctime), pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M")
    mtime = os.path.getmtime(pathTmp)  # 修改时间
    mtime_string = datetime.fromtimestamp(int(mtime), pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M")

    spathTmp = './static/public'
    sctime = os.path.getctime(spathTmp)  # 创建时间
    sctime_string = datetime.fromtimestamp(int(sctime), pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M")
    smtime = os.path.getmtime(spathTmp)  # 修改时间
    smtime_string = datetime.fromtimestamp(int(smtime), pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M")

    data = [            {'filename': 'public',
                        'datasize': '文件夹',
                        'cdatetime': ctime_string,
                        'mdatetime': mtime_string,
                        'privilege': '共享',
                        'owner': '公共文件夹',
                        'path': './static/'},
                        {'filename': id,
                        'datasize': '文件夹',
                        'cdatetime': sctime_string,
                        'mdatetime': smtime_string,
                        'privilege': '私有',
                        'owner': id,
                        'path': './static/upload/'}]
    return data