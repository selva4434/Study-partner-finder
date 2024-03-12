import pymongo
from Config import Configurations
from UserAPI import DataAPI




class Admin:
    def __init__(self):
        self.config=Configurations()
        self.mongo_conn=self.config.create_mong_conn()
        self.user_api=DataAPI()
        
    
    def get_all_user_data(self):
        collection=self.mongo_conn['User-Data']['user_details']
        
        user_data={}
        user_data['_id']=list()
        user_data['profile_pic']=list()
        cursor=collection.find({})
        
        for doc in cursor:
            for key,value in doc.items():
                if key not in user_data:
                    user_data[key]=list()
                if(key=="email"):
                    user_data['profile_pic'].append(self.user_api.get_profile_pic(value))
                user_data[key].append(value)
        
        return user_data
    
    def delete_user_by_email(self,email):
        collection=self.mongo_conn['User-Data']['user_details']
        
        criteria = {"email": email}
        
        try:
            result = collection.delete_one(criteria)
            return True
        except:
            return False
        
        