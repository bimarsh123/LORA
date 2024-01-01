import os
import subprocess
import shutil
import torch
import random
import string
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", torch_dtype=torch.float16).to("cuda")

def contains_chinese(s):
    """检查字符串是否包含中文字符"""
    return any('\u4e00' <= char <= '\u9fff' for char in s)

def random_string(length):
    """生成只包含英文字母和数字的随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for i in range(length))
# def random_key():
#     res = ''.join(random.choices(string.ascii_lowercase, k=3))
#     return (str(res))
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

if __name__ == "__main__":
    trigger_keyword = 'asd'
    directory_path = r"C:\Users\bimar\Desktop\video\outputs\new"
    parameters = {
        "pretrained_model": "D:\\code\\lora\\lora-scripts-main\\sd-models\\realisticVisionV51_v51VAE.safetensors",
        "train_data_dir": "./train/object",
        "output_name": "object",
        "max_train_epoches": 20,
        "network_dim": 128,
        "network_alpha": 128,
    }
    # print(trigger_keyword)
    preprocess(trigger_keyword, directory_path)
    run_ps1_with_temp_params("./train_lora.ps1", parameters)
