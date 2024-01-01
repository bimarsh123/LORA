import requests

name = input("Enter the name of the video model:")
file_path = f"C:\\Users\\bimar\\Desktop\\lora\\{name}.mp4"

# Open the video file
with open(file_path, "rb") as f:
    file_data = f.read()

# Prepare the POST request
    payload = {"file": file_data}
    url = "http://127.0.0.1:8000/video"


# Send the request
    response = requests.post(url, files=payload)
# Check the response
if response.status_code == 200:
    try:
        data = response.json()
        frames = data["result"]
        trigger_words = data["trigger_words"]
        for frame in frames:
            print(frame)
        print(trigger_words)
    except KeyError:
        print("Error: 'result' key not found in response JSON")
else:
    print("Error:", response.status_code)



