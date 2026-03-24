from pydantic import BaseModel,field_validator,computed_field,Field,EmailStr,ConfigDict,constr
from typing import List,Annotated,Text,Optional
from sql_models import Team,Match,Map,MatchPerformance,Map_FreeFireMax
from pydantic_settings import BaseSettings,SettingsConfigDict
from datetime import date,datetime
from fastapi import HTTPException



class Admin_Response(BaseModel):
    name:Annotated[str, Field(...,description="Enter Your Full Name",examples=["Raushan Kumar"],min_length=3,max_length=25)]
    email:EmailStr
    username: str= Field(max_length=20,examples=["raushan99_x"])

class Login_Admin(BaseModel):
    
    email:EmailStr=Field(..., description="enter your valid email",examples=["admin@espire.in"])
    password:Annotated[Text, Field(description="Password must contain atleast 8 character",examples=["Enter your password."])]

class Register_Team(BaseModel):
    
    team_name: Annotated[str,Field(...,description="maximum_limit is 29 characters.",max_length=29,examples=["maximum length is 29 char."])]
    email:EmailStr=Field(..., description="email should be unique",examples=["team_abc@espire.in"])
    password:Annotated[Text, Field(description="Password must contain atleast 8 character")]

class Registration_Response(BaseModel):
    team_id:str
    team_name: Annotated[str,Field(...,description="maximum_limit is 29 characters.",max_length=29)]
    email:EmailStr=Field(..., description="team_abc@espire.in")
    model_config=ConfigDict(from_attributes=True)


class Login_Model(BaseModel):
    
    email:EmailStr=Field(..., description="enter your valid email",examples=["team_abc@espire.in"])
    password:Annotated[Text, Field(description="Password must contain atleast 8 character",examples=["Enter your password."])]

class Important_Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file="important.env",extra="ignore")
    DataBase_URL:str
    SECRET_KEY:str
    ALGORITHM:str
    Expire_Time:int

class Match_Create(BaseModel):
    match_date: datetime
    suffix:str

    

class Match_Response(BaseModel):
    id:str
    match_date:datetime
   

    model_config=ConfigDict(from_attributes=True)

class Match_Performance_Create(BaseModel):
    match_id:str
    map_name:Map_FreeFireMax
    team_id:str
    kills:int
    result:str
    
    

    @field_validator("result")
    @classmethod
    def result_validation(cls,value):
        avialble_option=["Booyah","2nd","3rd","4th","5th","6th","7th","8th","9th","10th","11th","12th"]
        if value not in avialble_option:
            raise HTTPException(status_code=400,detail="Enter valid input")
        else:
            return value
    
    @computed_field(return_type=float)
    @property
    def score(self):
        if self.result == "Booyah":
            points = (12 + int(self.kills))
            return points
        if self.result=="2nd":
            points=(9+int(self.kills))
            return points
        if self.result=="3rd":
            points=(8+int(self.kills))
            return points
        if self.result=="4th":
            points=(7+int(self.kills))
            return points
        if self.result=="5th":
            points=(6+int(self.kills))
            return points
        if self.result=="6th":
            points=(5+int(self.kills))
            return points
        if self.result=="7th":
            points=(4+int(self.kills))
            return points
        if self.result=="8th":
            points=(3+int(self.kills))
            return points
        if self.result=="9th":
            points=(2+int(self.kills))
            return points
        if self.result=="10th":
            points=(1+int(self.kills))
            return points
        if self.result=="11th":
            points=(0+int(self.kills))
            return points
        if self.result=="12th":
            points=(0+int(self.kills))
            return points
    
class Match_Performance_Response(BaseModel):
    match_id:str
    map_name:Map_FreeFireMax
    team_id:str
    team_name:str
    score:float
    kills:int
    result:str
    rating:float

    model_config=ConfigDict(from_attributes=True)

class CommunityPost_Response(BaseModel):
    id:int
    match_id:str
    table_data:list
    created_by:int
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)

class Comment_Create(BaseModel):
    content: str

class Comment_Response(BaseModel):
    id:int
    post_id:int
    team_id:Optional[str]=None
    admin_id:Optional[int]=None
    content:str
    created_at:datetime

    model_config=ConfigDict(from_attributes=True)



    

 


        



    




