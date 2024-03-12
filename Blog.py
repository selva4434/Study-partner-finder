import pymongo
from Config import Configurations
import requests
import random
import string
from datetime import datetime
from UserAPI import DataAPI

class Blog(DataAPI):
    def __init__(self):
        self.config=Configurations()
        self.storage=self.config.Setup_Storage()
        self.mongo_conn=self.config.create_mong_conn()
        self.current_datetime = datetime.now()
        
    def get_top_three_blogs(self):
        db=self.mongo_conn['Blogs']
        collection=db['allBlogPost']
        
        pipeline = [
    {
        '$addFields': {
            'parsedDate': {
                '$toDate': {
                    '$dateToString': {
                        'date': {
                            '$dateFromString': {
                                'dateString': '$date'
                            }
                        },
                        'format': '%Y-%m-%d'  # Adjust the format based on your date string
                    }
                }
            }
        }
    },
    {
        '$sort': {
            'parsedDate': -1
        }
    },
    {
        '$limit': 3
    }
]
        result = list(collection.aggregate(pipeline))
        
        for i in result:
            del i['parsedDate']
            
        return result
        
    
    def generate_post_id(self,length=6):
   
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for _ in range(length))
        return random_string
        
    def create_new_post(self,data):
        post_id=self.generate_post_id(6)
        blog_pic_url=None
        
        db=self.mongo_conn['Blogs']
        collection=db['allBlogPost']
        
        user_blog=db[data['email']]
        if(data['bimgs']):
            self.save_profile(data['bimgs'],post_id)
            blog_pic_url=self.get_profile_pic(post_id)
        else:
            pass
        
        data={
            'post_id':post_id,
            'email':data['email'],
            'username':data['username'],
            'title':data['title'],
            'description':data['description'],
            'blog_pic':blog_pic_url,
            'content':data['content'],
            'profile_pic':self.get_profile_pic(data['username']),
            'date':datetime.now().strftime("%b %d, %Y")
            
            
        }
        try:
            collection.insert_one(data)
            user_blog.insert_one(data)
            return True
        except:
            return False
        
    def get_all_blog_posts(self):
        db=self.mongo_conn['Blogs']
        collection=db['allBlogPost']
        
        cursor=collection.find({})
        
        blogs={}
        
        blogs['_id']=list()
        
        for doc in cursor:
            for key,value in doc.items():
                if key not in blogs:
                    blogs[key]=list()
                blogs[key].append(value)
                
        return blogs
    
    def get_user_blogs(self,email):
        collection=self.mongo_conn['Blogs'][email]
        
        user_blog={}
        
        cursor=collection.find({})
        user_blog['_id']=list()
        for doc in cursor:
            for key,value in doc.items():
                if key not in user_blog:
                    user_blog[key]=list()
                user_blog[key].append(value)
                
        return user_blog
    def get_specific_blog(self,blog_id):
        collection=self.mongo_conn['Blogs']['allBlogPost']
        
        cursor=collection.find({"post_id":blog_id})
        
        specific_blog={}
        
        
        for doc in cursor:
            for key,value in doc.items():
                specific_blog[key]=value
        return specific_blog
    
    def post_comment(self,post_id,username,message):
        collection=self.mongo_conn['Comments'][post_id]
        
        
        try:
            collection.insert_one({
                'post_id':post_id,
                'username':username,
                'Date':self.current_datetime.strftime("%B %d, %Y at %I:%M %p"),
                'message':message
                
            })
            return True
        except:
            return False
        
    def get_all_comments(self,post_id):
        collection=self.mongo_conn['Comments'][post_id]
        
        cursor=collection.find({})
        
        all_comments={}
        
        all_comments['_id']=list()
        
        for doc in cursor:
            for key,value in doc.items():
                if key not in all_comments:
                   all_comments[key]=list()
                all_comments[key].append(value)
        return all_comments
    
    def delete_blog_by_id(self,blog_id):
        db=self.mongo_conn['Blogs']
        collection=db['allBlogPost']
        
        criteria = {"post_id": blog_id}
        
        cursor=collection.find_one(criteria)    
        
        email=cursor['email']
        collection_email=db[email]
        try:
            collection.delete_one(criteria)
            collection_email.delete_one(criteria)
            
        except:
            return False
        
        
                 
        
        
                
                
        
        
        