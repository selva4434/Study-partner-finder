from functools import wraps
from flask import Flask,render_template,request,jsonify,session,url_for,redirect,send_from_directory,send_file
import json
import os
import random
from Config import Configurations
from mail import send_email
from pyfcm import FCMNotification
from datetime import datetime
from flask_caching import Cache
from UserAPI import DataAPI
from chat import Chat
from flask_socketio import SocketIO, emit,join_room,leave_room,send
from flask_cors import CORS
import threading
from Blog import Blog
from Admin import Admin
import firebase_admin
from firebase_admin import credentials, auth
import threading
import time


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app,cors_allowed_origins="*")
config=Configurations()
firebase_db=config.Setup_auth()
cred = credentials.Certificate("course_link.json")
firebase_admin.initialize_app(cred)
app.secret_key = 'Course-Link'
mail=send_email()
mongo_client=config.create_mong_conn()
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
user_dataAPI=DataAPI()
user_chat=Chat()
user_blog=Blog()
admin=Admin()
push_service = FCMNotification(api_key="AAAADYQ7gQs:APA91bGi9fLum9wMFZeGxx7JZJfOsfdnnfIPtEpolYSDaCGpe2pwiqQqa7GKNe_xmvmtT8e-cWbdMY5OojxUpTXvx_QUUb43a7n4pvWgat2dxlkfKO6aMJbEJkZ1cNQwxpKWYkXv-brT")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


#helping functions
def generate_otp():
    sequence_length = 5
    min_value = 10 ** (sequence_length - 1)  # Smallest 5-digit number (10000)
    max_value = (10 ** sequence_length) - 1  # Largest 5-digit number (99999)
    random_number = random.randint(min_value, max_value)
    return random_number

def check_email_exists(email):
    try:
        users = auth.get_user_by_email(email)
        return True
    except Exception as e:
        return False
    
#end of helping functions

def login_required(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        
        
        if session.get('user_id'):
            return view_function(*args, **kwargs)
        else:
            return redirect(url_for('signup_login'))
    return decorated_function

@app.route('/')
def Home():
    session_bool=False
    
    if('user_id' in session):
        if(session['user_id']=="admin12345656"):
            return redirect(url_for('Admin_Home'))
        user_data=user_dataAPI.get_data_of_specific_user(session['email'])
        if(user_data['Intial_set']=='False'):
            return redirect(url_for('profile'))
        session_bool=True
    
    top_three=user_blog.get_top_three_blogs()
    
    return render_template('index.html',session_bool=session_bool,top_three_blog=top_three,count=len(top_three))

@app.route('/signup_login')
def signup_login():
    if('email' in session and session['email']!=''):
        return redirect(url_for('Home'))
    return render_template('signup_login.html')



@app.route('/success')
def success():
    data=request.args.get('data')
    return render_template('success.html',data=data)



@app.route('/login',methods=['POST','GET'])
def login():
    if(request.method=='POST'):
        email=request.form['loginemail']
        password=request.form['loginPassword']
    
    try:
        userauth=firebase_db.sign_in_with_email_and_password(email,password)
        session['email']=email
        session['username']=user_dataAPI.get_data_of_specific_user(email)['username']
  
    except Exception as e:
        error_url = url_for('error', data="Invalid login", reason="Check your credentials and try again or contact us")
        return redirect(error_url)
    
    cookie=userauth['idToken']
    session['user_id'] = cookie
    return redirect(url_for('Home'))

@app.route('/signup',methods=['GET','POST'])
def signup():

    database=config.Setup_DataBase()


    data={
        'username':session.get('username'),
        'email':session.get('email'),
        'password':session.get('password'),
        
        
        }

    db=mongo_client['User-Data']
    collection=db['user_details']
    current_date = datetime.now()
    
    # existing_document = collection.find({'email': data['email']})
    
    # if existing_document is not None:
    #         response_data = {'message': 'Signup successful'}

    #         return jsonify(response_data), 200 
    firebase_db.create_user_with_email_and_password(data['email'],data['password'])
    collection.insert_one({
            'username':data['username'],
            'email':data['email'],
            'password':data['password'],
            'Age':"Not Set",
            'Course':"Not Set",
            'About':"Not Set",
            'first_name':"Not Set",
            'last_name':"Not Set",
            'City':"Not Set",
            'Country':"Not Set",
            'Degree':"Not Set",
            'Experince_Level':"Not Set",
            'language':"Not Set",
            'postal_code':"Not Set",
            'Joined_date':current_date.strftime("%Y-%m-%d"),
            'Intial_set':'False'
            })
    
    
    


    session['username']=''
    session['email']=''
    session['password']=''


    response_data = {'message': 'Signup successful'}

    return jsonify(response_data), 200 

# @app.route('/profile')
# def profile():
#     return render_template('Profile.html')

@app.route('/send_otp',methods=['GET','POST'])
def send_otp():
    response_data = {'message': 'Signup successful','email_exists':False}


    data=request.get_json()
    flag=check_email_exists(data['email'])

    if(flag==True):
        response_data['email_exists']=True
        return jsonify(response_data),404

    session['username']=data['username'].strip()
    session['email']=data['email'].strip()
    

    if(data['password']==data['confirm_password']):

        session['password']=data['password']
        get_otp=generate_otp()
        response_data['otp']=str(get_otp)

        mail.send_otp(session['username'],session['email'],get_otp)

        return jsonify(response_data), 200

    response_data['message']='FAIL'

    return jsonify(response_data),404


@app.route('/error')
def error():
    data = request.args.get('data')
    reason = request.args.get('reason')
    return render_template('error.html',data={"data":data,"reason":reason})

@app.route('/email_exists')
def email_exists():
    return render_template('error.html',data={"reason":"Email Already Exists","data":"Try to login using valid credentials"})

    
@app.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    user_specific_data=None
    user_specific_data=cache.get('profile_data')
    
    # user_specific_event=None
    # user_specific_event=cache.get('event_data')
    
    # friend_data=None
    # friend_data=cache.get('user_friend_data')
    
    # if(friend_data is None):
        
    #     friend_data=friend.get_friends_specific_user(session['email'])
    #     cache.set("user_friend_data",friend_data,timeout=180*60)
    
    
    # if(user_specific_event is None):
    #     user_specific_event=event.get_event_for_user(session['email'])
    #     cache.set('event_data',user_specific_event,timeout=180*60)
    
    if(user_specific_data is None):
        user_specific_data=user_dataAPI.get_data_of_specific_user(session['email'])
        cache.set('profile_data',user_specific_data,timeout=30*60)

        
    else:
        print("Cache Hit")
    
    if(user_specific_data['Intial_set']=='False'):
        return render_template('first_user.html')


    # return render_template("profile.html",user_specific_data=user_specific_data,event_count=len(user_specific_event['_id']),friend_count=len(friend_data['_id']))
    return render_template('Profile.html',user_specific_data=user_specific_data)
@app.route('/first_user',methods=['POST'])
@login_required
def first_user():

    data=request.get_json()
    data['Intial_set']='True'
    db=mongo_client['User-Data']
    collection=db['user_details']
    filters = {"email": session['email']}
    update_operation = {"$set": data}

    
    try:
        result = collection.update_one(filters, update_operation)
        cache.delete("profile_data")
        return jsonify({"status":200}),200
    except: 
        return jsonify({"status":404}),404
        
    
@app.route('/save_profile_pic',methods=['POST'])
@login_required
def save_profile_pic():
    
    if 'file' not in request.files:
        pass
    file = request.files['file']

    return_code=user_dataAPI.save_profile(file,cache.get('profile_data')['email'] or session['email'])
    
    if(return_code==True):
        result = {'message': 'Image uploaded successfully'}
        cache.delete('profile_data')
        return jsonify(result)
    else:
        result = {'error': 'Unexpected error occured'}
        return jsonify(result)
    
@app.route('/create_chat',methods=['POST','GET'])
@login_required
def create_chat():
    
    data=request.get_json()
    
    return_code=user_chat.start_chat(session['email'],data['email'])    
    
    if(return_code==True):
        cache.delete('users_chats')
        return jsonify({'message':"Sucess",'status':200}),200
    
    return jsonify({'message':"Error",'status':404}),404

@app.route('/save_token',methods=['POST'])
def save_token():
    token=request.get_json()
    return_code=user_dataAPI.save_notify_token(session['email'],token['token'])
    
    
    if(return_code==True):
        return jsonify({'message':"Sucess",'status':200}),200
    return jsonify({'message':"Error",'status':404}),404   
@app.route('/chat_page/<chat_id>')
@login_required
def chat_page(chat_id):
    
    user_specific_chats=None
    user_specific_chats=cache.get('users_chats')
    history_chat={}
    len_chat=0
    
    user_specific_data=[]
    
    if(user_specific_chats is None):
        user_specific_chats=user_chat.get_users_chat(session['email'])
        cache.set('users_chat',user_specific_chats,timeout=30*60)
    else:
        print("Cache Hit")  
    if(len(user_specific_chats['_id'])!=0):
    
        for email in user_specific_chats['chat_reciever_email']:
            try:
                data=user_dataAPI.get_data_of_specific_user(email)
                user_specific_data.append(data)
            except:
                continue
    
    selected_chat={}
    
    if(chat_id!='None'):
        index=user_specific_chats['chat_id'].index(chat_id)
        selected_chat=user_specific_data[index]
        selected_chat['chat_id']=user_specific_chats['chat_id'][index]
        
        history_chat=user_chat.get_specific_chat(chat_id,session['email'])
        len_chat=len(history_chat['_id'])
        
    return render_template('chat.html',user_specific_data=user_specific_data,user_specific_chats=user_specific_chats,count=len(user_specific_data),chat_id=chat_id,selected_chat=selected_chat,email=session['email'],history_chat=history_chat,len_chat=len_chat,username=session['username'],firebase_config=config.firebaseConfig)

@app.route('/firebase-messaging-sw.js', methods=['GET'])
def serve_sw():
    print("hello")
    return send_from_directory(os.path.join(app.root_path, 'static/js'), 'firebase-messaging-sw.js')

@app.route('/firebase-app.js', methods=['GET'])
def firebase_app_js():
    print("hello")
    return send_from_directory(os.path.join(app.root_path, 'static/js'), 'firebase-app.js')


@app.route('/change_chat/<chat_id>')
@login_required
def change_chat(chat_id):
    # specific_chat=user_chat.get_specific_chat(chat_id,session['email'])
    return "hi"
@app.route('/delete_user/<email>')
def delete_user(email):
    return_code=admin.delete_user_by_email(email)
    
    
    if(return_code==True):
        try:
            user=auth.get_user_by_email(email)
            user_id=user.uid
            auth.delete_user(user_id)
            cache.clear()
            return redirect(url_for('Admin_Home'))
        except:
            return "UNEXPECTED ERROR"
    else:
        return "UNEXPECTED ERROR"
    
@app.route('/Admin_Blogs/<int:page_no>')
@login_required
def Admin_Blogs(page_no):
    all_blogs=None
    blog_posts=None
    
    cache.get('blogs_data')
    
    if( all_blogs is None):
        
        blog_posts=user_blog.get_all_blog_posts()
        cache.set("blogs_data",blog_posts,timeout=30*60)
    else:
        print("Cache Hit")
        
    
    
    start=(page_no-1)*10
    
    end=(page_no)*10
    
    if(start>len(blog_posts['_id'])):
        start=(page_no-1)*10
    
    if(end>len(blog_posts['_id'])):
        end=len(blog_posts['_id'])

    return render_template('Admin_Blogs.html',blog_posts=blog_posts,end=end,start=start,page_no_len=int(len(blog_posts['_id'])/10)+1,page_no=page_no,Admin=True)

@app.route('/delete_blog/<post_id>')
@login_required
def delete_blog(post_id):
    user_blog.delete_blog_by_id(post_id)
    
    if(session['user_id']=="admin12345656"):
        return redirect(url_for('Admin_Home'))
    return redirect(url_for('Home'))
    
@app.route('/Admin_Home')
@login_required
def Admin_Home():
    user_data=None
    user_data=cache.get('All_User')
    if('email' in session and  session['email']!="studypartnerfinder@gmail.com" and session['username']!="Admin"):
        return redirect(url_for('Admin'))
    
    if(user_data is None):
        user_data=admin.get_all_user_data()
        cache.set('All_User',user_data,timeout=30*30)
    
    
    return render_template('Admin_Home.html',user_data=user_data,count=len(user_data['_id']))
    


@app.route("/Admin",methods=['GET','POST'])
def Admin():
    if('email' in session and session['email']=="studypartnerfinder@gmail.com"):
        return redirect(url_for('Admin_Home'))    
    if(request.method=='POST'):
        admin_email=request.form['emailAdress']
        admin_password=request.form['password']
        if(admin_email=="studypartnerfinder@gmail.com" and admin_password=="AayushH008"):
            session['user_id']="admin12345656"
            session['username']="Admin"
            session['email']="studypartnerfinder@gmail.com"
            return redirect(url_for('Admin_Home'))
    return render_template('Admin_login.html')
    
    
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    session['chat_id'] = room
    
@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    
    session.pop('chat_id', None)




@socketio.on('message')
def handle_message(message):
    # Run the background thread
    
    
    return_code = user_chat.push_data_specific_chat(message['sender_email'], message['receiver_email'], str(session['username']+':'+message['message']), message['room'])
    notify_token=user_dataAPI.get_notify_token(message['receiver_email'])
    
    
    
    if(notify_token):
        try:
            registration_id = notify_token['token']
            message_title = session['username']
            message_body = message['message']
            message_icon = "https://studypartnerfinder.com/static/images/Logo.png"

            result = push_service.notify_multiple_devices(registration_ids=registration_id, message_title=message_title, message_body=message_body,message_icon=message_icon)
            print(result)

        except Exception as e:
            print(e)
            pass
        

    
    if return_code:

        # Emitting from within a socket event handler
        emit('response', {
            'data': str(session['username']+':'+message['message']),
            'sender_email': message['sender_email'],
            'receiver_email': message['receiver_email'],
            'email':session['email'],
            'time': message['time']
        }, broadcast=True, room=message['room'])

@app.route('/terms')
def terms():
    return "hello"

@app.route('/create_blog')
@login_required
def create_blog():
    user_specific_data=None
    user_specific_data=cache.get('profile_data')
    
    if(user_specific_data is None):
        user_specific_data=user_dataAPI.get_data_of_specific_user(session['email'])
        cache.set('profile_data',user_specific_data,timeout=180*60)
        
    return render_template('create_blog.html',username=session['username'],profile_pic=user_specific_data['profile_pic'],date=datetime.now().strftime("%b %d"))

@app.route('/user_blogs/<int:page_no>')
def user_blogs(page_no):
    
    blog_posts=user_blog.get_user_blogs(session['email'])
    
    
    start=(page_no-1)*10
    
    end=(page_no)*10
    
    if(start>len(blog_posts['_id'])):
        start=(page_no-1)*10
    
    if(end>len(blog_posts['_id'])):
        end=len(blog_posts['_id'])

    return render_template('Admin_Blogs.html',blog_posts=blog_posts,end=end,start=start,page_no_len=int(len(blog_posts['_id'])/10)+1,page_no=page_no,user=True)



@app.route('/blog/<int:page_no>')
@login_required
def blog(page_no):
    all_blogs=None
    blog_posts=None
    
    cache.get('blogs_data')
    
    if( all_blogs is None):
        
        blog_posts=user_blog.get_all_blog_posts()
        cache.set("blogs_data",blog_posts,timeout=30*60)
    else:
        print("Cache Hit")
    
    
    start=(page_no-1)*10
    
    end=(page_no)*10
    
    if(start>len(blog_posts['_id'])):
        start=(page_no-1)*10
    
    if(end>len(blog_posts['_id'])):
        end=len(blog_posts['_id'])

    return render_template('blog.html',blog_posts=blog_posts,end=end,start=start,page_no_len=int(len(blog_posts['_id'])/10)+1,page_no=page_no)

@app.route('/view_blog/<blog_id>')
def view_blog(blog_id):
    Admin=False
    
    if(session['email']=="studypartnerfinder@gmail.com"):
        Admin=True
    user_specific_blog=user_blog.get_specific_blog(blog_id)
    all_blog=user_blog.get_all_blog_posts()
    get_all_comments=user_blog.get_all_comments(blog_id)
    
    count=0
    if(len(all_blog['_id'])<=4):
        count=len(all_blog['_id'])
    else:
        count=4   
    return render_template('blog-single.html',user_specific_blog=user_specific_blog,all_blog=all_blog,count=count,get_all_comments=get_all_comments,comment_count=len(get_all_comments['_id']),Admin=Admin)

@app.route('/post_comment/<post_id>',methods=['GET','POST'])
def post_comment(post_id):
    
    if(request.method=='POST'):
        username=session['username']
        
        message=request.form['message']
    return_code=user_blog.post_comment(post_id,username,message)
    
    if(return_code==True):
        blog_id=post_id
        return redirect(url_for('view_blog',blog_id=blog_id))
    else:
        return "Can't post comment"

@app.route('/post_blog',methods=['POST','GET'])
@login_required
def post_blog():
    bimgs=None
    if(request.method=='POST'):
        title=request.form['title']
        description=request.form['dscription']
        if 'bimgs'  in request.files:
            bimgs=request.files['bimgs']
        content=request.form['content']
        
        return_code=user_blog.create_new_post(
            {'title':title,
             'description':description,
             'bimgs':bimgs,
             'content':content,
             'email':session['email'],
             'username':session['username']
             }
        )
        if(return_code==True):
            cache.delete('blogs_data')
            return redirect(url_for('success',data="Successfully Posted"))
        else:
            return redirect(url_for('error',data="Couldn't Upload",reason="Check with admin"))
        
    
@app.route('/find_friends')
@login_required
def find_friends():
    all_user_data=None
    Course=[]
    degree=[]
    all_user_data = cache.get('cached_all_user_data')
    
    
    if(all_user_data is None):
        
        all_user_data=user_dataAPI.get_all_user_data(session['email'])
        
        cache.set('cached_all_user_data', all_user_data, timeout=60 * 60)
    else:
        print("Cache Hit")
        pass
    langauge=[]
    
    if(len(all_user_data)>1):
        for i in all_user_data['language']:
            temp=",".join(i)
            langauge.append(temp)
            
        all_user_data['language']=langauge

    
            
        for i,j in zip(all_user_data['Course'],all_user_data['Degree']):
            if(i not in Course and i!="Not Set"):
                Course.append(i)
            if( j not in degree and j!="Not Set"):
                degree.append(j)
    
    if len(all_user_data)<=1:
        count=0
    else:
        count=len(all_user_data['username'])
    return render_template('find_friends.html',all_user_data=all_user_data,count=count,Course=Course,degree=degree)

# @app.route('/send_friend_request')
# def send_friend_request():
#     return "hi"

    
@app.route('/update_profile_data',methods=['POST'])
@login_required
def update_profile_data():
    
    updated_data={}
    updated_data['language'] = request.form.getlist('mySelect[]')
    
    updated_data['first_name']=request.form['f_name']
    updated_data['last_name']=request.form['l_name']
    updated_data['Age']=request.form['age']
    updated_data['Address']=request.form['address']
    updated_data['City']=request.form['city']
    updated_data['Country']=request.form['country']
    updated_data['Postal_Code']=request.form['postal']
    updated_data['About']=request.form['about']
    updated_data['Course']=request.form['Course']
    updated_data['Degree']=request.form['Degree']
    updated_data['Experince_Level']=request.form['Experince_Level']

    # return_code=True
    return_code=user_dataAPI.update_profile(updated_data,session['email'])
    
    if(return_code==True):
        
        cache.clear()
        return redirect(url_for('profile'))
    
    else:
        return redirect(url_for('error',data="Couldn't Update",reason="Try to update again you should have strong internet"))

@app.route('/logout')
def logout():
    # Clear the user ID from the session
    session.pop('user_id', None)
    session.clear()
    cache.clear()
    return redirect(url_for('Home'))

@app.route('/contact')
def contact():
    session_bool=False
    if('user_id' in session):
        session_bool=True
    return render_template('contact.html',session_bool=session_bool)

@app.route('/contact_form',methods=['POST','GET'])
def contact_form():
    data={}
    if(request.method=='POST'):
        data['name']=request.form['name']
        data['email']=request.form['email']
        data['subject']=request.form['subject']
        data['message']=request.form['message']
        
        return_code=mail.contact_email(data)
        if(return_code==True):
            return redirect(url_for('success',data='Thanks For Feedback'))
        else:
            return redirect(url_for('error',data="Couldn't post feedback",reason='Kindly Try Again'))
        
@app.route('/sitemap', methods=['GET'])
def sitemap():
    xml_file_path = 'sitemap.xml'
    return send_file(xml_file_path, mimetype='application/xml')


@app.route('/about')
def about():
    session_bool=False
    if('user_id' in session):
        session_bool=True
    return render_template('about.html',session_bool=session_bool)

def run_inf():
    while True:
        print("running server....")
        time.sleep(600)


if __name__ == '__main__':
    thread = threading.Thread(target=run_inf)
    thread.start()
    socketio.run(app,host='0.0.0.0',port='443',debug=True)