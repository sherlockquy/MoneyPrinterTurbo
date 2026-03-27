import requests

url = "http://localhost:8080/api/v1/videos"
headers = {"Content-Type": "application/json"}
payload = {
    "video_subject": "Viking meditation Nordic landscapes",
    "video_terms": "viking ship fog, nordic mountain snow, ancient fire ritual, dark cinematic landscape, warrior silhouette sunset",
    "custom_audio_file": "D:/Projects/MoneyPrinterTurbo/storage/music/ValhallaGold.mp3",
    "video_aspect": "9:16",
    "video_clip_duration": 15,
    "subtitle_enabled": False
}

print("Đang gửi yêu cầu tạo video...")
response = requests.post(url, json=payload, headers=headers)

print("Status Code:", response.status_code)
print("Response:", response.json())
