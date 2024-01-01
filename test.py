import requests
import os
import shutil
# saving the trigger words as .txt file

path = r"C:\Users\bimar\Desktop\video"

payload = {
    "pretrained_model": "D:\\code\\lora\\lora-scripts-main\\sd-models\\majicmixRealistic_v7.safetensors",
    "train_data_dir": "./train/sanu",
    "output_name": "muso" ,
    "max_train_epochs": 20,
    "network_dim": 128,
    "network_alpha": 128,
}
# headers = {
#     'Content-Type': 'application/json'
# }
# response = requests.post("http://127.0.0.1:8100/lora", json=payload,headers='headers')
response = requests.post("http://127.0.0.1:8100/lora", json=payload)
r = response.json()
print(r)
result = r['lora']

print(result)

def save_trigger(path):
    save_path = path
    filename = "trigger_word"
    full_name = os.path.join(path,filename +".txt")
    file1= open(full_name,"w")
    file1.write(result)
    file1.close()
    print("Successfully added the trigger_word.txt")


# save_trigger(path)
