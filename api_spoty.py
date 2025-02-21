from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import random
import string
from typing import List
from fastapi.responses import RedirectResponse
import webbrowser



json_users="users.json"
token_data="token.json"


class Song(BaseModel):
    song_name: str

class Usuario(BaseModel):
    user: str
    songs: List[str]=[]
    



def random_string(length: int) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))



    

app=FastAPI()

CLIENT_ID = "82c38d08d2f548da9a5388093b863b9d"
CLIENT_SECRET= "b2c5b2947e784c799ec2f28345680910"
REDIRECT_URI = "http://localhost:8000/callback"
scope = 'user-top-read'

TopArtistsURL="https://api.spotify.com/v1/me/top/artists"
TopTracksURL='https://api.spotify.com/v1/me/top/tracks'
ArtistURL= "https://api.spotify.com/v1/search?q=remaster%2520track%3ADoxy%2520artist%3AMiles%2520Davis&type=artist"


def token_request(code:str):

    url="https://accounts.spotify.com/api/token"

    data= {
        #"grant_type": "client_credentials",
        "grant_type": "authorization_code",
        "code":code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        
    }

    response = requests.post(url, data=data)

    if response.status_code ==200:
        
       return response.json()
        
    else:
        print(f"Error:{response.status_code}, {response.text}")
        return(None)

@app.get("/login")

def login():

    state=random_string(16)
    auth_url = "https://accounts.spotify.com/authorize"
    #'user-read-private user-read-email'
    query= f"response_type=code&client_id={CLIENT_ID}&scope={scope}&redirect_uri={REDIRECT_URI}&state={state}"
    auth_url=f'https://accounts.spotify.com/authorize?{query}'
    print(auth_url)
    return webbrowser.open(url=auth_url)

@app.get("/callback")
def callback(code:str):
        
    access_token = token_request(code)
    if access_token:
        with open(token_data,"w") as file:
            json.dump(access_token, file, indent=4)
    
        return {"message": "Authorization successful", "access_token": access_token}
    else:
        raise HTTPException(status_code=400, detail="Failed to get access token")

def get_refresh_token():
    
    try:
        with open(token_data, "r") as file:
            token_info = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    refresh_token = token_info.get("refresh_token")
    if not refresh_token:
        return None 

    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers)

    if response.status_code == 200:
        new_token_info = response.json()

        
        new_token_info["refresh_token"] = refresh_token  
        with open(token_data, "w") as file:
            json.dump(new_token_info, file, indent=4)

        return new_token_info["access_token"]

    return None


    
@app.get("/api/top_artist/")
def get_artist():
    try:
        with open(token_data,"r") as file:
            token_info = json.load(file)
            print(token_info)
    except (FileNotFoundError, json.JSONDecodeError) as e:
     
        raise HTTPException(status_code=400, detail=f"Error al leer el token: {str(e)}")
    
    if not token_info:
      
        raise HTTPException(status_code=400, detail="Access token no disponible")
    
    access_token=get_refresh_token() or token_info["access_token"]

    headers = {
    "Authorization": f"Bearer {access_token}"
    }

    params=  {'time_range': 'medium_term', 'limit': 10}

    response = requests.get(TopArtistsURL,headers=headers,params=params)

    if response.status_code == 200:
        data = response.json()
        artist_names = [track['name'] for track in data['items']]
        return {"favourite_artists": artist_names}
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error al obtener las canciones: {response.status_code} - {response.text}")



    # token = token_request()
    
    # headers = {
    # "Authorization": f"Bearer {token}"}

    # #params = {'q': f'remaster%20track:Doxy%20artist:{name}','type':'artist',}

    # response = requests.get(TopArtistsURL,headers=headers)

    # if response.status_code == 200:
    #     return response.json()

    # else:
    #     raise HTTPException(status_code=response.status_code, detail=response.json())


@app.get("/api/songs/")
def get_songs():
    try:
        with open(token_data,"r") as file:
            token_info = json.load(file)
            print(token_info)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        
        raise HTTPException(status_code=400, detail=f"Error al leer el token: {str(e)}")
    
    if not token_info:
        
        raise HTTPException(status_code=400, detail="Access token no disponible")
    
    access_token=get_refresh_token() or token_info["access_token"]

    headers = {
    "Authorization": f"Bearer {access_token}"
    }

    params=  {'time_range': 'medium_term', 'limit': 10}

    response = requests.get(TopTracksURL,headers=headers,params=params)

    if response.status_code == 200:
        data = response.json()
        song_names = [track['name'] for track in data['items']]
        return {"favourite_songs": song_names}
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error al obtener las canciones: {response.status_code} - {response.text}")
    


@app.post("/api/create_user")
def create_user(user: Usuario):
    
    
    try:
        with open(json_users,"r") as file:
            saved_users=json.load(file)
    except FileNotFoundError:
        saved_users=[]
    if any (u["user"]==user.user for u in saved_users):
        raise HTTPException(status_code=400, detail="This user already exists")
    
    new_user= user.dict()
    saved_users.append(new_user)

    with open(json_users,"w") as file:
        json.dump(saved_users, file, indent=4)
    return{"message": "User created", "user": new_user}



@app.get("/api/users")
def see_users():
    try:
        with open(json_users,"r") as file:
            saved_users=json.load(file)

            return {"users":saved_users}
        
    except:
        return("users not found")
    

@app.get("/api/users/{user}")

def see_users(user:str):
    try:
        with open(json_users,"r") as file:
            saved_users=json.load(file)
            user_data = next((u for u in saved_users if u["user"] == user), None)
            
            return {"user":user_data}
        
    except:
        return("user not found")



@app.put("/api/{user}")
def modify_preferences(user:str,newPreferences:List[Song]):
    try:
        with open(json_users, "r")as file:
            saved_users=json.load(file)
            user_data=next((u for u in saved_users if u["user"]==user), None)

            if user_data is None:
                raise HTTPException(status_code=400, detail="User not found")
            
            #user_data["songs"]= newPreferences
            user_data["songs"].extend([song.song_name for song in newPreferences])
        
        with open(json_users,"w") as file:
            json.dump(saved_users,file,indent=4)
        return{"mesage": "User Modified", "user": user}
    
    except:
        return("Error")
    
@app.delete("/api/{user}")
def delete_user(user:str):
    try:
        with open(json_users,"r") as file:
            saved_users = json.load(file)
            userToRemove=next((u for u in saved_users if u["user"]==user),None)

        if userToRemove is None:
            raise HTTPException(status_code=400, detail="User not found")
            
        saved_users= [u for u in saved_users if u["user"]!=user]

        with open(json_users,"w") as file:
            json.dump(saved_users,file,indent=4)
        return{"message": f"User '{user}' deleted"}
    
    except:
        return("Error")










