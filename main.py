#-*- coding:utf-8 -*-
import json

from flask import Flask,render_template,request,redirect,url_for,Response,jsonify,send_from_directory
from gevent import pywsgi
import pymysql
from flask_sqlalchemy import SQLAlchemy
from BaseSQL import CONFIG_KEY,CONFIG_VALUE
from userdb import UserOperator
from textdb import TextmdOperator
from filedb import FileOperator
from chatdb import ChatOperator
from basefunction import *
import os
from datetime import datetime,timedelta
import time
from flask_apscheduler import APScheduler
import shutil
import zipfile
from jinja2 import Environment,PackageLoader
from watchdog.events import EVENT_TYPE_OPENED
app = Flask(__name__)
app.config[CONFIG_KEY] = CONFIG_VALUE
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds = 1)
app.config['JSON_AS_ASCII'] = False
app.secret_key = CONFIG_VALUE
user_operator = UserOperator()
text_operator = TextmdOperator()
file_operator = FileOperator()
chat_operator = ChatOperator()
scheduler = APScheduler()
scheduler.init_app(app)


#防止session失效,每隔一小时调用一次session,session在默认情况下不使用八小时后失效
@scheduler.task('interval', id='job_1', args=None,seconds=60*60)
def reconnect():
    user_operator.connect()
    text_operator.connect()
    text_operator.is_text_id(1)
    user_operator.isid('root')
    chat_operator.close()

@app.route('/')
def index():
    post = {
        'islogin': False,
        'id': None
    }
    (id, pwd) = get_session()
    if user_operator.login(id, pwd):
        post['islogin'] = True
        post['id'] = id
    return render_template('index.html',post = post)



@app.route('/User/<user_name>',methods=['GET','POST'])
def myweb(user_name):
    (id, pwd) = get_session()
    if (not user_operator.login(id, pwd)) and id != user_name:
        return redirect(url_for('login'))

    if request.method == "POST":
        formid = request.form['formid']
        if formid == '1':
            avatar = request.files['avatar']
            if avatar.filename != '':
                path = './static/upload/' + id + '/user_avatar/'
                clear_path(path)
                avatar.save(path + avatar.filename)

        elif formid == '2':
            background = request.files['background']
            if background.filename != '':
                path = './static/upload/' + id + '/website_background/'
                clear_path(path)
                background.save(path + background.filename)


    return render_template('myweb.html',post = {'islogin':True,
                                                'id':id,
                                                'privilege':user_operator.get_privilege_text(id)}
                           )



@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')

    if request.method == "POST":
        id = request.form['name']
        pwd = request.form['pwd']

        if user_operator.login(id,pwd):
            set_session(id,pwd)
            wait_web()
            return redirect(url_for('index'))
        else:
            return render_template('login.html',error = '账号或密码错误，请重试')

@app.route('/logout',methods=['POST'])
def logout():
    delete_session()
    return redirect(url_for('login'))



@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == "GET":
        return render_template('register.html')

    if request.method == "POST":
        id = request.form['name']
        pwd = request.form['pwd']
        user_operator.register(id,pwd)
    wait_web()
    return redirect(url_for('login'))

@app.route('/resetpwd',methods=['GET','POST'])
def resetpwd():
    if request.method == "GET":
        return render_template('resetpwd.html')

    if request.method == "POST":
        id = request.form['name']
        pwd = request.form['pwd']
        print(id)
        print(pwd)
    wait_web()
    return redirect(url_for('login'))

@app.route('/edit')
def edit():
    (id,pwd) = get_session()
    if not user_operator.login(id,pwd):
        return redirect(url_for('login'))
    return render_template('blogedit.html',post = {
        'islogin': True,
        'id': id,
        'content':""
    })

@app.route('/upload', methods =['POST'])
def upload():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    file =  request.files.get('editormd-image-file')
    if not file:
        res = {
            'success' : 0,
            'message' : '上传失败'
        }
    else:
        filename = datetime.now().strftime('%Y%m%d%H%M%S') + file.filename
        path = './upload/' + id + '/image/'
        if not os.path.exists(path):
            os.makedirs(path,0o777)
            print("创建成功",path)
        file.save(path+filename)
        res = {
            'success' : 1,
            'message' : '上传成功',
            'url' : url_for('image', name = filename)
        }
        print(url_for('image', name = filename))
    return jsonify(res)

@app.route('/image/<name>')
def image(name):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    path = './upload/' + id + '/image/'
    if os.path.exists(path):
        with open(os.path.join(path, name), 'rb') as f:
            resp = Response(f.read(), mimetype="image/jpeg")
            return resp
    return Response()

@app.route('/save', methods=['POST'])
def save():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        text_operator.add(user_id=id,title=title,content=content,ispublic=False,date=datetime.now())
    #写入数据库
    return redirect(url_for('blog_list'))

@app.route('/revise_save', methods=['POST'])
def revise_save():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        text_id = request.form.get('text_id')
        text = text_operator.get_text(text_id=text_id)
        if text.user_id != id:
            return redirect(url_for('login'))
        text_operator.revise(text_id=text_id,title=title,content=content,ispublic=False,date=datetime.now())
    #写入数据库
    return redirect(url_for('blog_list'))


@app.route('/user/bloglist',methods=['GET','POST'])
def blog_list():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    if request.method == "POST":
        text_id = request.form['text_id']
        text_operator.setpublic(text_id)

    texts = text_operator.get_user_item(user_id=id)
    count = text_operator.count_user(id)
    return render_template('blog_list.html',post ={
        'islogin': True,
        'id': id,
        'texts':texts,
        'count': count
    })

@app.route('/blog/<int:text_id>')
def blog_detail(text_id):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    text = text_operator.get_text(text_id=text_id)

    if text.ispublic or id == text.user_id :
        count = text_operator.count_public_user(text.user_id)
        return render_template('blog_detail.html',post ={
            'islogin': True,
            'id': id,
            'text':text,
            'count':count
        })
    return redirect(url_for('login'))
@app.route('/forum/<int:page>')
def forum(page):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    num = 6 #一页最多显示十条帖子
    count = text_operator.count_public()

    if page*num > count:
        return redirect(url_for('forum',page = count//num))
    min = count - page*num if (count-page*num)<num else num
    texts = text_operator.get_public_item(page*num,min)
    
    
    return render_template('forum.html',post ={
        'islogin': True,
        'id': id,
        'texts':texts,
        'page':page
    })

@app.route('/file/data')
def filedata():

    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if is_session_path():
        (filepath,filename) = get_session_path()
        if filename == '//':
            data = {"code":0,"msg":"","count":1000,"data":get_root_filelist(id)}
            return jsonify(data)

        if filename == '/':
            if filepath == './static/upload' or filepath == './static/upload/' or filepath == './static/' or filepath == './static':
                data = {"code": 0, "msg": "", "count": 1000, "data": get_root_filelist(id)}
                return jsonify(data)
            else:
                filelist = get_filename_list(id, filepath , file_operator)
                filelist.insert(0, {'filename': '/',
                                    'datasize': '返回上一级目录',
                                    'cdatetime': '',
                                    'mdatetime': ' ',
                                    'privilege': ' ',
                                    'owner': ' ',
                                    'path':  os.path.dirname(filepath)})
                filelist.insert(0, {'filename': '//',
                                    'datasize': '返回根目录',
                                    'cdatetime': ' ',
                                    'mdatetime': ' ',
                                    'privilege': ' ',
                                    'owner': ' ',
                                    'path': './static'})
                data = {"code": 0, "msg": "", "count": 1000, "data": filelist}
                return jsonify(data)


        while len(filepath) and filepath[-1] == '/':
            filepath = filepath[:-1]
        while len(filename) and filename[-1] == '/':
            filename = filename[:-1]

        filelist = get_filename_list(id, filepath +'/'+ filename,file_operator)
        filelist.insert(0,{'filename': '/',
                        'datasize': '返回上一级目录',
                        'cdatetime': '',
                        'mdatetime': ' ',
                        'privilege': ' ',
                        'owner': ' ',
                        'path': filepath})
        filelist.insert(0,{'filename': '//',
                        'datasize': '返回根目录',
                        'cdatetime': ' ',
                        'mdatetime': ' ',
                        'privilege': ' ',
                        'owner': ' ',
                        'path': './static'})
        data = {"code":0,"msg":"","count":1000,"data":filelist}
        return jsonify(data)
    data = {"code": 0, "msg": "", "count": 1000, "data": get_root_filelist(id)}
    return jsonify(data)

@app.route('/delete/files',methods=['POST'])
def delete_files():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        filename = request.form['filename']
        filepath = request.form['filepath']
        privilege = request.form['privilege']
        owner = request.form['owner']
        while filepath[-1] == '/':
            filepath = filepath[:-1]
        path = filepath + '/' + filename

        if filename == '//' or filename == '/':
            return redirect(url_for('files'))

        if path == './static' or path == './static/public' or path == ('./static/upload/' + id):
            return redirect(url_for('files'))
        print(path)
        if owner == id:
            delete_fileordir(path)
            file_operator.delete(filename = filename,filepath = filepath)
        elif user_operator.get_privilege_text(id) == 'FishCouncilor' or user_operator.get_privilege_text(id) == 'Administrator':
            delete_fileordir(path)
            file_operator.delete(filename = filename, filepath = filepath)

    return redirect(url_for('files'))

@app.route('/reset/filename',methods=['POST'])
def reset_filename():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        filename = request.form['filename']
        filepath = request.form['filepath']
        privilege = request.form['privilege']
        newfilename = request.form['new_filename']
        owner = request.form['owner']
        while filepath[-1] == '/':
            filepath = filepath[:-1]
        path = filepath + '/' + filename
        endswith = os.path.splitext(path)[-1]
        newfilename = newfilename + endswith
        newpath = filepath + '/' + newfilename
        if owner == id:
            os.rename(path,newpath)
            file_operator.revise_filename(filename,filepath,newfilename)
        elif user_operator.get_privilege_text(id) == 'FishCouncilor' or user_operator.get_privilege_text(id) == 'Administrator':
            os.rename(path,newpath)
            file_operator.revise_filename(filename, filepath, newfilename)
    return redirect(url_for('files'))

@app.route('/add/file',methods=['POST'])
def add_files():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if is_session_path():
        (filepath,filename) = get_session_path()
        while filepath[-1] == '/':
            filepath = filepath[:-1]
        if os.path.isdir(filepath + '/' + filename):
            file_dir = filepath + '/' + filename

            if file_dir == './static' or file_dir == './static/upload':
                pass
            else:
                if get_privilege(file_dir,id) == '私有':
                    filename = add_random_path(file_dir)
                    file_operator.add(filename,file_dir,get_privilege(file_dir,id),id)
                elif user_operator.get_privilege_text(id) == 'FishCouncilor' or user_operator.get_privilege_text(id) == 'Administrator':
                    filename = add_random_path(file_dir)
                    file_operator.add(filename, file_dir, get_privilege(file_dir, id), id)
    return redirect(url_for('files'))

@app.route('/unzip/file',methods=['POST'])
def unzip_files():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        filename = request.form['filename']
        filepath = request.form['filepath']
        privilege = request.form['privilege']
        owner = request.form['owner']
        if filename == '/' or filename == '//':
            return redirect(url_for('files'))
        while filepath[-1] == '/':
            filepath = filepath[:-1]
        dirpath = filepath + '/' + filename

        if os.path.isfile(dirpath) and os.path.splitext(dirpath)[-1] == '.zip':
            if get_privilege(dirpath,id) == '私有':
                dir = unzip(dirpath)
                print(dir)
                file_operator.addpath(dir,'私有',id)
            elif user_operator.get_privilege_text(id) == 'FishCouncilor' or user_operator.get_privilege_text(id) == 'Administrator':
                dir = unzip(dirpath)
                print(dir)
                file_operator.addpath(dir, '共享', id)
    return redirect(url_for('files'))

@app.route('/set/myweb',methods=['POST'])
def set_myweb():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        filename = request.form['filename']
        filepath = request.form['filepath']
        privilege = request.form['privilege']
        owner = request.form['owner']
        if filename == '/' or filename == '//':
            return redirect(url_for('files'))
        while filepath[-1] == '/':
            filepath = filepath[:-1]
        dirpath = filepath + '/' + filename

        if os.path.isfile(dirpath) and os.path.splitext(dirpath)[-1] == '.html':
            user_operator.set_link(id,dirpath)
            print(user_operator.is_link(id))

    return redirect(url_for('files'))

@app.route('/PersonalHomePage/<username>')
def PersonalHomePage(username):
    html_path = user_operator.is_link(username)

    filename = os.path.basename(html_path)
    filepath = os.path.dirname(html_path)
    relatie_path = filepath.replace('./static/', '')
    env = Environment(loader=PackageLoader('static',relatie_path))
    template = env.get_template(filename)
    supplement_path = '.' + filepath
    content = template.render(supplement_path = supplement_path )

    return content

@app.route('/files',methods=['GET','POST'])
def files():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    add_user_dir(id)
    file_operator.add(filename=id,filepath='./static/upload',privilege='私有',owner=id)
    if request.method == "POST":
        filename = request.form['filename']
        filepath = request.form['filepath']
        if os.path.isdir(filepath + '/' + filename):
            set_session_path(filepath,filename)

    return render_template('files.html', post={
        'islogin': True,
        'id': id
    })

@app.route('/down/file',methods=['POST'])
def downfile():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        filename = request.form['filename']
        filepath = request.form['filepath']
        privilege = request.form['privilege']
        owner = request.form['owner']

        while filepath[-1] == '/':
            filepath = filepath[:-1]

        dirpath = filepath + '/' + filename

        if filename == '/' or filename == '//':
            return redirect(url_for('files'))
        if privilege != '共享' and owner != id:
            return redirect(url_for('files'))
        if os.path.isfile(dirpath):
            print('下载文件:',dirpath)
            return send_from_directory(filepath + '/',filename,as_attachment=True)
        else:
            zipDir(dirpath ,'./static/tmp/',filename + '.zip')
            return send_from_directory('./static/tmp/',filename + '.zip',as_attachment=True)
    return redirect(url_for('files'))


@app.route('/upload/file',methods=['POST'])
def uploadfiles():
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if request.method == "POST":
        file = request.files.get('file')
        if is_session_path():
            (filepath,filename) = get_session_path()
            while filepath[-1] == '/':
                filepath = filepath[:-1]
            filepath = filepath + '/' + filename
            while filepath[-1] == '/':
                filepath = filepath[:-1]

            if os.path.isdir(filepath):
                if filepath == './static' or filepath == './static/upload':
                    return {'flag': False}

                filename = file.filename
                file.save(filepath + '/' + filename)
                file_operator.add(filename=filename,filepath=filepath,privilege=get_privilege(filepath,id),owner=id)
                return {'flag': True}
    return {'flag': False}




@app.route('/revise/<int:text_id>')
def revise(text_id):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    text = text_operator.get_text(text_id=text_id)
    if text.user_id != id:
        return redirect(url_for('login'))

    return render_template('blog_revise.html', post={
        'islogin': True,
        'id': id,
        'text':text,
        'lineStyle':True
    })

@app.route('/delete/<int:text_id>')
def delete(text_id):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    text = text_operator.get_text(text_id=text_id)
    if text.user_id != id:
        return redirect(url_for('login'))
    text_operator.delete(text_id=text_id)
    return redirect(url_for('blog_list'))

@app.route('/chat/<friend_id>', methods=['GET', 'POST'])
def chat(friend_id):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))

    if not user_operator.isid(friend_id):
        return render_template('404.html')

    if request.method == 'POST':
        text = request.form['massage']
        chat_operator.add(send_id=id, receive_id=friend_id, message=text)

    chat_operator.set_history(receive_id=id, send_id=friend_id)

    # 侧边栏信息 用户名以及最近一条消息
    chat_list = []
    username_list = user_operator.get_id_list()
    for username in username_list:
        recent = chat_operator.get_recently_message(id, username)
        if recent is None:
            time = ''
            count = 0
            recent = ''
        else:
            time = datetime.strptime(str(recent.date), '%Y-%m-%d %H:%M:%S')
            time = str(time.hour) + ':' + str(time.minute)
            count = chat_operator.get_unread_count(id, username)
            recent = recent.message

        if username == friend_id:
            state = 'active'
        else:
            state = ' '

        chat_list.append({'username': username,
                          'recent': recent,
                          'unread_count': count,
                          'date': time,
                          'state': state
                          })
    N = 100
    # 聊天窗口消息
    messages = []
    message_list = chat_operator.get_message_list(id, friend_id, N)
    for message in reversed(message_list):
        time = datetime.strptime(str(message.date), '%Y-%m-%d %H:%M:%S')
        time = str(time.hour) + ':' + str(time.minute)
        if message.send_id == id:
            messages.append({'message': message.message, 'date': time, 'is_right_or_left': True})
        else:
            messages.append({'message': message.message, 'date': time, 'is_right_or_left': False})

    return render_template('chat.html', post={
        'id': id,
        'friend_id': friend_id,
        'chat_list': chat_list,
        'messages': messages,
        'login_state': '在线'
    })
@app.route('/send_message/<friend_id>',methods=['POST'])
def send_message(friend_id):
    (id, pwd) = get_session()
    if not user_operator.login(id, pwd):
        return redirect(url_for('login'))
    message = request.form.get('message')
    chat_operator.add(id,friend_id,message)
    return {'flag':True}


@app.route('/get_chat_message/<friend_id>')
def get_chat_message(friend_id):
    (id, pwd) = get_session()
    N = 30
    # 聊天窗口消息
    messages = []
    message_list = chat_operator.get_message_list(id, friend_id, N)
    for message in reversed(message_list):
        time = datetime.strptime(str(message.date), '%Y-%m-%d %H:%M:%S')
        time = str(time.hour) + ':' + str(time.minute)
        if message.send_id == id:
            messages.append({'message': message.message, 'date': time, 'is_right_or_left': True})
        else:
            messages.append({'message': message.message, 'date': time, 'is_right_or_left': False})

    chat_list = '<div>'
    my_message = '<div class="message my_message"><p>'
    frnd_message = '<div class="message my_message"><p>'
    br_span = '<br><span>'
    span_p = '</span> </p></div>'

    '''
<button id='voice_button' onclick="switch_voice_state()"><img id='voice_img' src="../static/image/chatimage/语音.png" style="width:50px;height:50px;"></button>
    '''

    left_voice = '<button> <img src="../static/image/chatimage/左语音消息.png" style="width:50px;height:50px;"></button>'
    right_voice = '<button> <img src="../static/image/chatimage/右语音消息.png" style="width:50px;height:50px;"></button>'

    for msg in messages:
        if msg['is_right_or_left']:
            if msg['is_voice']:
                chat_list = chat_list + my_message + right_voice + br_span + msg['date'] + span_p
            else:
                chat_list = chat_list + my_message + msg['message'] + br_span + msg['date'] + span_p
        else:
            if msg['is_voice']:
                chat_list = chat_list + frnd_message + left_voice + br_span + msg['date'] + span_p
            else:
                chat_list = chat_list + frnd_message + msg['message'] + br_span + msg['date'] + span_p

    chat_list = chat_list + '</div>'
    return {'chat_list':chat_list}


@app.route('/recorder')
def recorder():
    return render_template('recorder.html')


@app.route('/upload/recorder', methods=['POST'])
def upload_recorder():
    if request.method == "POST":
        file = request.files.get('upfile')
        random_string = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8))
        file.save('./static/upload/' + random_string + '.bin')

    return {'flag': True}

@app.template_filter('get_avatar_path')
def get_avatar_path(user_id):
    (avatar,background) = get_user_path(user_id)
    return avatar

@app.template_filter('get_background_path')
def get_background_path(user_id):
    (avatar,background) = get_user_path(user_id)
    return background


if __name__ == '__main__':
    scheduler.start()
    #server = pywsgi.WSGIServer(('0.0.0.0', 8080), app)
    #server.serve_forever
    app.run(port=5639)




