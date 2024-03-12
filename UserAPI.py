import pymongo
from Config import Configurations
import requests



class DataAPI:
    def __init__(self):
        self.config=Configurations()
        self.mongo_conn=self.config.create_mong_conn()
        self.storage=self.config.Setup_Storage()
    
    def is_url_exists(self,url):
        response=requests.get(url)

        if(response.status_code==200):
            return True
        else:
            return False
        
    def get_profile_pic(self,username):		
        url=self.storage.child(username).get_url(None) or None

        if (not self.is_url_exists(url)):
            url=""
        if(url==""):
            url=self.storage.child("default_profile.jpg").get_url(None) or None
        
        return url
        
    def get_all_user_data(self,email):
        db = self.mongo_conn["User-Data"]
        collection=db['user_details']
        
        
        query = {
    "$and": [
        {"email": {"$ne": email}},
        
    ]
}
        
        cursor = collection.find(query)
        
        user_all_data={}
        
        
        #have to check whether the user is already a friend or not
        user_all_data['profile_url']=list()
        
        for doc in cursor:
            for key,value in doc.items():
                
                if key not in user_all_data:
                    user_all_data[key]=list()
                user_all_data[key].append(value)
                
                if(key=="email"):
                    user_all_data['profile_url'].append(self.get_profile_pic(value))
                    
                    
        try:        
            del user_all_data['_id']
        except:
            pass
        
        return user_all_data
    
    def get_data_of_specific_user(self,email):
        if(email=="studypartnerfinder@gmail.com"):
            email='logo.png'
        db = self.mongo_conn["User-Data"]
        collection=db['user_details']
        
        cursor = collection.find({"email":email})
        data={}
        for doc in cursor:
            data=doc
            break
        data['profile_pic']=self.get_profile_pic(email)
        
        return data
    
    def update_profile(self,updated_data,email):

        db = self.mongo_conn["User-Data"]
        collection=db['user_details']
        
        filter={"email":email}
        update={"$set":updated_data}
        
        try:
            collection.update_one(filter, update)
            return True
        except Exception as e:
            return False
    
    def save_profile(self,file,username):
        try:
            self.storage.child(username).put(file)
            
            return True
        except Exception as e:
       
            return  False
        
    def save_notify_token(self,email,token):
        db=self.mongo_conn['Notification']
        collection=db['notify_clients']
        try:
            collection.insert_one({
                'email':email,
                'token':token
            })
            return True
        except:
            return False
        
    def get_notify_token(self,email):
        db=self.mongo_conn['Notification']
        collection=db['notify_clients']
        
        cursor=collection.find({'email':email})
        
        data={}
        
        for doc in cursor:
            for key,val in doc.items():
                if key not in data:
                    data[key]=list()
                data[key].append(val)
        
        return data or None
        
        
        
        