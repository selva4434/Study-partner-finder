import pyrebase
import pymongo
import ssl

class Configurations:
    def __init__(self):
        self.firebaseConfig={
            
                'apiKey': "AIzaSyAiwvGBmyscjjekiRF2mcMlRYEW6Yu3tCU",
                'authDomain': "course-link-2cdaf.firebaseapp.com",
                'projectId': "course-link-2cdaf",
                'storageBucket': "course-link-2cdaf.appspot.com",
                'messagingSenderId': "58053067019",
                'appId': "1:58053067019:web:9eec85b90de1aeb90c220e",
                'measurementId': "G-BGPMWXMG8G",
                "databaseURL":"https://course-link-2cdaf-default-rtdb.firebaseio.com/"

        }
        self.client = pymongo.MongoClient("mongodb+srv://raviajay9344:x41B2mJP2PEDBAcg@courselinkfreelancer.k5wwxhh.mongodb.net/")
        #x41B2mJP2PEDBAcg
        self.firebase=pyrebase.initialize_app(self.firebaseConfig)
         
    def Setup_auth(self):
        return self.firebase.auth()

    def Setup_DataBase(self):
        return self.firebase.database()
    
    def create_mong_conn(self):
        return self.client
    
    def Setup_Storage(self):
        return self.firebase.storage()