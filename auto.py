import os
import subprocess
import shutil
import torch
import random
import string
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware (
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/outputs",StaticFiles(directory="outputs"),name="outputs")

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", torch_dtype=torch.float16).to("cuda")

def contains_chinese(s):
    """检查字符串是否包含中文字符"""
    return any('\u4e00' <= char <= '\u9fff' for char in s)

def random_string(length):
    """生成只包含英文字母和数字的随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(length))

def random_key():
    random.seed(40)
    res = ''.join(random.choices(string.ascii_lowercase, k=3))
    return res

def save_trigger(path,output):
    save_path = path
    filename = "trigger_word"
    full_name = os.path.join(path,filename+".txt")
    file1= open(full_name,"w")
    file1.write(random_key()+"<lora:"+ output +":1>")
    file1.close()
    print("Successfully added the trigger_word.txt")

def caption_image(trigger_keyword, image_path):
    raw_image = Image.open(image_path).convert('RGB')
    inputs = processor(raw_image, return_tensors="pt").to("cuda", torch.float16)
    out = model.generate(**inputs)
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

def run_ps1_with_temp_params(ps1_path, params):
    args = ' '.join([f"-{key} {value}" if isinstance(value, int) else f"-{key} '{value}'" for key, value in params.items()])        
    subprocess.run(["powershell", ps1_path, args])
   

@app.post("/video")
async def video_to_images(file: UploadFile):
    # removal of old image data
    path = r'C:\Users\bimar\Desktop\lora\outputs\new'
    if os.path.exists(path):
        shutil.rmtree(path)
    
    # Save the video file
    # file_path input video directory
    # new_name = input("Input name of the video model that you are training:")
    train_Data =input("Enter the name of the training model:")
    output_name = input("Set the name of output model:")
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),f"{train_Data}.mp4")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Create the output directory for image frames
    # output_dir is output video directory
    output_dir = os.path.join(os.path.dirname(file_path), "outputs", 
                                os.path.splitext(os.path.basename(file_path))[0])
    os.makedirs(output_dir, exist_ok=True)

    # Extract image frames from the video and save as PNG
    subprocess.run(["ffmpeg", "-i", file_path,"-r","0.4" ,f"{output_dir}/image_%06d.png"])

    # Return the list of generated image frames
    frames = []
    for filename in os.listdir(output_dir):
        frames.append(os.path.join(output_dir,filename))

    # reading trigger words from existing directory
    with open("trigger_word.txt",'r') as f:
        lines = f.read()
    # data = {
    #     "result" : frames,
    #     "trigger_words" :  lines,
    #     # "lora" : lora
    # }
    data= {"result":frames,"trigger_words": lines}
    
    if __name__ == "__main__":
        trigger_keyword = random_key()
        directory_path = f"C:\\Users\\bimar\\Desktop\\lora\\outputs\\{train_Data}"
        # f_path = os.path.join(directory_path,new_name)
        preprocess(trigger_keyword, directory_path)

        parameters = {
            "pretrained_model": "C:\\Users\\bimar\\Desktop\\lora\\sd-models\\realisticVisionV51_v51VAE.safetensors",
            "train_data_dir": f"./train/{train_Data}",
            "output_name": f"{output_name}",
            "max_train_epoches": 10,
            "network_dim": 128,
            "network_alpha": 128,
        }
    
    save_trigger(r"C:\Users\bimar\Desktop\lora",parameters["output_name"])
    training_data = parameters["train_data_dir"]
    if os.path.exists(training_data):
        run_ps1_with_temp_params("./train_lora.ps1", parameters)
    else:
        print("The training data doesn't exists")
    
    return data
    #return {"result" :frames}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)