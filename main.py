#import data to dialogflow

import pymongo
import json
from google.oauth2 import service_account
from google.cloud import dialogflow_v2 as dialogflow
import os
import datetime
from google.cloud import dialogflow_v2
client = pymongo.MongoClient('mongodb://xxx:xxxx@localhost:27017/')
db = client['phukethealth_chatbot_service']  
collection = db['chatbot']  
intent_data = collection.find()
intent_data_check = collection.find()
ground_data = {}
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'configpath/keychatbotv3.json'
credentials = service_account.Credentials.from_service_account_file('configpath/keychatbotv3.json')
project_id = 'chatbot-290308'
parent = f"projects/{project_id}/agent"
language = "th"
folder_path = "filejson"


# Get the current time
current_time = datetime.datetime.now()
current_unix_time = int(current_time.timestamp())

one_day_ago = current_time - datetime.timedelta(days=1)
one_day_ago_unix_time = int(one_day_ago.timestamp())


one_day_later = current_time + datetime.timedelta(days=1)
one_day_later_unix_time = int(one_day_later.timestamp())

intent_check_last = collection.find().sort('created_at', -1).limit(1)
time_last_in_mongo = int(intent_check_last[0]['created_at'])

def createformjsontoDialogflow():
    count=0
    for intent_usersays_data in intent_data:
        intent_check_last = intent_usersays_data.get('created_at')
        if (intent_check_last <= one_day_later_unix_time) and (intent_check_last>=one_day_ago_unix_time):
            count+=1  
            responsesspeech = []
            user_says = []               
            for checkarray_response_v2 in range(len(intent_usersays_data['response'])):                       
                responsesspeech.append(intent_usersays_data['response'][checkarray_response_v2])
            
            for checkarray_message_v2 in range(len(intent_usersays_data['message'])):               
                message = {
                    "data": [
                        {
                            "text": intent_usersays_data['message'][checkarray_message_v2]
                        }
                    ]
                }  
                user_says.append(message)
            
            
            data = {
                "name": str(count)+"_"+str(intent_check_last)+"_"+str(intent_usersays_data['topic']),
                "responses":[
                    {  "messages":[
                        {
                            "type": "message",
                                "speech": responsesspeech
                        }
                    ]
                }
                ],
                "userSays": user_says
            }

            json_data = json.dumps(data,indent=2)
            file_path = "{}{}{}{}{}.json".format(str(count),"_",intent_check_last,"_",intent_usersays_data['topic'])  # Specify the file pßßath
            # print(file_path,end="\n")
                
            with open('filejson/'+file_path, 'w') as json_file:
                json_file.write(json_data)
           

def importAutoToIntents():
    client = dialogflow.IntentsClient(credentials=credentials)
    dialogflow.ListIntentsRequest(parent=parent,language_code=language)
    countinput=0
    countchrckv2 = 0
    
    files = os.listdir(folder_path)
    json_files = [file for file in files if file.endswith(".json")]
    json_files.sort(key=lambda x: int(x.split("_")[0]))

    for file_name in json_files:
        json_file_path = os.path.join(folder_path, file_name)            
        with open(json_file_path, 'r') as file:            
            intent_data = json.load(file)
    
        display_name = intent_data['name']
        existing_intent = find_existing_intent(client, parent, display_name)
        namecheck = existing_intent
        
        if namecheck == None:
            countinput+=1                       
            intent = create_intent(intent_data)
            response = client.create_intent(parent=parent, intent=intent)
            print('%s - %s - Intent created successfully. Intent ID: %s'%(countinput,display_name,response.name))
        else:
            print("have "+ namecheck.display_name)
        

def find_existing_intent(client, parent, display_name):
    intents = client.list_intents(parent=parent)
    for intent in intents:
        if intent.display_name == display_name:
            return intent
    return None




def create_intent(intent_data):
    # intent_data = str(intent_data)
    training_phrases = [
        dialogflow.Intent.TrainingPhrase(
            parts=[
                dialogflow.Intent.TrainingPhrase.Part(text=phrase['data'][0]['text'])
            ]
        )
        for phrase in intent_data['userSays']
    ]

    messages = []
    for response in intent_data['responses']:
        text = response['messages'][0]['speech']
        if len(text) <= 300:
            message = dialogflow.Intent.Message(
                text=dialogflow.Intent.Message.Text(text=text)
            )
            messages.append(message)
        else:
            # Split the text into multiple responses
            num_responses = len(text) // 300 + 1
            for i in range(num_responses):
                start = i * 300
                end = (i + 1) * 300
                response_text = text[start:end]
                message = dialogflow.Intent.Message(
                    text=dialogflow.Intent.Message.Text(text=response_text)
                )
                messages.append(message)

    intent = dialogflow.Intent(
        display_name=intent_data['name'],
        training_phrases=training_phrases,
        messages=messages,    
    )

    return intent

def trainagrnt(project_id):
    client = dialogflow.AgentsClient.from_service_account_file("configpath/keychatbotv3.json")
    client.train_agent(parent=f"projects/{project_id}")
    
def delete_files_in_folder():
    file_list = os.listdir(folder_path)
    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_name}")

createformjsontoDialogflow()

# def runfunction():      
#     createformjsontoDialogflow()
#     importAutoToIntents()        
#     trainagrnt(project_id)
#     delete_files_in_folder()

    
# if (time_last_in_mongo <= one_day_later_unix_time) and (time_last_in_mongo>=one_day_ago_unix_time):
#     runfunction()
# else:
#     print("not data now")


