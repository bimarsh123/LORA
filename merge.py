import os
from fastapi import FastAPI, BackgroundTasks
import json
import subprocess
from fastapi import FastAPI, UploadFile , BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
import torch
import string
import random
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from fastapi import FastAPI

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", torch_dtype=torch.float16).to("cuda")

app = FastAPI()

class Data(BaseModel):
    pretrained_model: str
    train_data_dir: str
    output_name: str 
    max_train_epochs: int
    network_dim: int
    network_alpha: int

app.add_middleware (
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def random_key():
    res = ''.join(random.choices(string.ascii_lowercase, k=3))
    return res

key = ""
l = ""
prompt = ""
prompt_return = ""
"Saving the trigger words"
def save_trigger(path,output):
    global key
    if not key:
        key = random_key()
    save_path = path
    filename = "trigger_word"
    full_name = os.path.join(path,filename+".txt")
    file1= open(full_name,"w")
    file1.write(key +" <lora:"+ output +":1>")
    file1.close()
    print("Successfully added the trigger_word.txt")

# Creating a json file
def write_json(new_data, filename='data.json'):
    if os.path.isfile(filename) and os.path.getsize(filename) > 0:
        with open(filename, 'r') as file:
            try:
                file_data = json.load(file)
            except json.JSONDecodeError:
                file_data = {}
    else:
        file_data = {}
        
    file_data.update(new_data)

    with open(filename, 'w') as file:
        json.dump(file_data, file, indent=4)

def contains_chinese(s):
    """检查字符串是否包含中文字符"""
    return any('\u4e00' <= char <= '\u9fff' for char in s)

def random_string(length):
    """生成只包含英文字母和数字的随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(length))

def caption_image(trigger_keyword, image_path):
    global prompt
    raw_image = Image.open(image_path).convert('RGB')
    inputs = processor(raw_image, return_tensors="pt").to("cuda", torch.float16)
    out = model.generate(**inputs)
    if not prompt:
        prompt = processor.decode(out[0], skip_special_tokens=True)
    return (trigger_keyword + ', ' + processor.decode(out[0], skip_special_tokens=True))

def save_caption_to_txt(destination_folder, image_name, caption):
    txt_path = os.path.join(destination_folder, os.path.splitext(image_name)[0] + '.txt')
    with open(txt_path, 'w') as f:
        f.write(caption)

def preprocess(trigger_keyword, directory_path):
    base_name = os.path.basename(directory_path)
    relative_directory_path = os.path.join('.', 'train', base_name)
    new_folder_name = "6_" + base_name
    new_folder_path = os.path.join(relative_directory_path, new_folder_name)
    
    # 创建新文件夹，如果它不存在
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)

    for filename in os.listdir(directory_path):
        full_path = os.path.join(directory_path, filename)
        
        # 如果文件名包含中文字符，重命名文件
        if contains_chinese(filename):
            new_name = random_string(10) + os.path.splitext(filename)[1]
            new_full_path = os.path.join(directory_path, new_name)
            os.rename(full_path, new_full_path)
            full_path = new_full_path
            filename = new_name

        # 检查在新文件夹中是否存在同名的txt文件
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_path = os.path.join(new_folder_path, txt_filename)
        
        # 如果txt文件存在，跳过这张图片的标注过程
        if os.path.exists(txt_path):
            continue
        else:
            caption = caption_image(trigger_keyword, full_path)
            # 保存标注到新文件夹
            save_caption_to_txt(new_folder_path, filename, caption)

        # 检查在新文件夹中是否存在同名的图片
        img_path = os.path.join(new_folder_path, filename)
        if not os.path.exists(img_path):
            # 如果图片不存在，将其复制到新文件夹
            shutil.copy(full_path, new_folder_path)

def add_json_data(json_data):
    if os.path.exists("trainedModel.json"):
        with open("trainedModel.json", 'r') as f:
            existing_data = json.load(f)
        # Append the new data to the existing data
        existing_data.extend(json_data)
    else:
        existing_data = json_data

    # Write the updated data back to the file
    with open("trainedModel.json", 'w') as f:
        json.dump(existing_data, f,indent=4)



async def run_ps1_with_temp_params(ps1_path, params):
    args = ' '.join([f"-{key} {value}" if isinstance(value, int) else f"-{key} '{value}'" for key, value in params.items()])        
    process = subprocess.run(["powershell", ps1_path, args])
    print(process.stdout)
    # print("we get here!!!!!!!!!!!!!!!!!!!!!!!")
    # return 'training done'



@app.get("/refresh")
async def refresh_model_name():
    with open("trainedModel.json",'r') as file:
        model = json.load(file)

    return model



app.mount("/outputs",StaticFiles(directory="outputs"),name="outputs")
@app.post("/video")
async def video_to_images(file: UploadFile, background_tasks : BackgroundTasks):
    
    global l,key,prompt
    key = ""
    prompt = ""
    # removal of old image data
    path = f"C:\\Users\\bimar\\Desktop\\lora\\outputs\\{l}"
    if os.path.exists(path):
        shutil.rmtree(path)
    
    # Save the video file
    # file_path input video directory
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),os.path.basename(file.filename))
    with open(file_path, "wb") as f:
        f.write(await file.read())
    l =os.path.splitext(os.path.basename(file.filename))[0]
    # Create the output directory for image frames
    # output_dir is output video directory
    output_dir = os.path.join(os.path.dirname(file_path), "outputs", 
                                os.path.splitext(os.path.basename(file_path))[0])
    os.makedirs(output_dir, exist_ok=True)

#     directory_path = f"C:\\Users\\bimar\\Desktop\\lora\\outputs\\{l}"
#     preprocess(key, directory_path)
    save_trigger(r"C:\Users\bimar\Desktop\lora",l)
    json_data ={
        f"{l} video": l
    }
 
    with open("data.json") as file:
        model = json.load(file)

    def check_values(new_Data):
        for name, value in new_Data.items():
            if isinstance(value, dict):
                # check_values(value)
                print("Data already exists")
            else:
                with open("data.json") as data_file:
                    model = json.load(data_file)
                # Check if value exists in model
                if value not in model.values():
                    print("Data doesnot exist the model trainig will start soon")
                    # Extract the image from the video and save as PNG
                    subprocess.run(["ffmpeg", "-i", file_path, "-r", "0.3", f"{output_dir}/image_%06d.png"])
                    directory_path = f"C:\\Users\\bimar\\Desktop\\lora\\outputs\\{l}"
                    rm_path = f"C:\\Users\\bimar\\Desktop\\lora\\train\\{l}"
                    if os.path.exists(rm_path):
                        shutil.rmtree(rm_path)
                    preprocess(key, directory_path)
                    get_data = [
                                    {
                                        "name": f"{l}",
                                        "prompt":f"{key},"+ f"{prompt}" + f"<lora:{l}:1>"
                                    }
                            ]
                    add_json_data(get_data)
                    global prompt_return
                    prompt_return = f"{key},"+ f"{prompt}" + f"<lora:{l}:1>"
                    print(prompt_return)
                    # Runs the background task run_lora
                    background_tasks.add_task(run_lora)

                write_json(new_Data)
    check_values(json_data)
    # Return the list of generated image frames
    # frames = []
    # for filename in os.listdir(output_dir):
    #     frames.append(os.path.join(output_dir,filename))

     # reading trigger words from existing directory
    with open("trigger_word.txt",'r') as f:
        lines = f.read()
    
    # data = {"trigger_words": lines}
    global prompt_return
    # print(prompt_return)
    data = {"trigger_words": prompt_return}
    # data = {"result":frames, "trigger_words": lines}

    return data

# def edit_json_data(prompt):
#     if os.path.exists("trainedModel.json"):
#         with open("trainedModel.json", 'r') as f:
#             existing_data = json.load(f)
#         # i'm gonna find the last object's 'prompt', manipulate it and place it back
#         old_prompt = existing_data[-1]['prompt']   
#         print('\n\n'+old_prompt+'\n\n')     
#         existing_data[-1]['prompt'] = old_prompt[0:4] + ',' + prompt + old_prompt[3:-1]
#     else:
#         print('ERR: trainedModel JSON FILE NOT EXIST')

#     # Write the updated data back to the file
#     with open("trainedModel.json", 'w') as f:
#         json.dump(existing_data, f,indent=4)


#@app.get("/abc")
async def run_lora():
    global key
    # trigger_keyword = key
    # directory_path = f"C:\\Users\\bimar\\Desktop\\lora\\outputs\\{l}"
    # preprocess(trigger_keyword, directory_path)
    parameters = {
        "pretrained_model": "C:\\Users\\bimar\\Desktop\\lora\\sd-models\\v1-5-pruned-emaonly.safetensors",
        "train_data_dir": f"./train/{l}",
        "output_name": f"{l}",
        "max_train_epoches": 0,
        "network_dim": 128,
        "network_alpha": 128, 
    }
    training_data = parameters["train_data_dir"]
    if os.path.exists(training_data):
        await run_ps1_with_temp_params("./train_lora.ps1", parameters)
    else:
        print("The training data doesn't exists")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)