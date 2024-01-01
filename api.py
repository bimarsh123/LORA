import os
import base64
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Data(BaseModel):
    pretrained_model: str
    train_data_dir: str
    output_name: str 
    max_train_epochs: int
    network_dim: int
    network_alpha: int

lora = ''

@app.post("/lora")
async def lora(data: Data):
    # params = {
    #     "pretrained_model": "./sd-models/beautifulRealistic_v60.safetensors",
    #     "train_data_dir": "./train/as",
    #     "output_name": "as",
    #     "max_train_epoches": 20,
    #     "network_dim": 128,
    #     "network_alpha": 128,
    # }
    params = {
        "pretrained_model": data.pretrained_model,
        "train_data_dir": data.train_data_dir,
        "output_name": data.output_name,
        "max_train_epochs": data.max_train_epochs,
        "network_dim": data.network_alpha,
        "network_alpha": data.network_alpha,
    }
    args = ' '.join([f"-{key} {value}" if isinstance(value, int) else f"-{key} '{value}'" for key, value in params.items()])
    subprocess.run(["powershell", "./train_lora1.ps1", args])
    
    lora = "abc<lora:" + data.output_name + ":1>"
    return {"lora": lora}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
