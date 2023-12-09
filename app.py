from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip
import requests
import shutil
import os

app = FastAPI()

# CORS設定（必要に応じて設定してください）
origins = [
    "http://localhost",
    "http://localhost:8000",
    # 他の許可するオリジンをここに追加
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConvertRequest(BaseModel):
    drive_id: str
    file_name: str

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}

def download_mp3(mp3_url: str, mp3_filename: str):
    response = requests.get(mp3_url)
    with open(mp3_filename, 'wb') as file:
        file.write(response.content)

@app.post("/convert")
async def convert_mp3_to_mp4(request_data: ConvertRequest):
    try:
        base_url = "https://drive.google.com/uc?id="
        drive_id = request_data.drive_id
        file_name = request_data.file_name

        mp3_url = f"{base_url}{drive_id}"
        mp3_file_name = f"{file_name}.mp3"
        mp4_file_name = f"{file_name}.mp4"
        image_file_name = "input_image.jpeg"

        # ダウンロード先のディレクトリにあるすべての.mp3および.mp4ファイルを削除
        for file_name in os.listdir('.'):
            if file_name.endswith('.mp3') or file_name.endswith('.mp4'):
                os.remove(file_name)

        download_mp3(mp3_url, mp3_file_name)

        audio_clip = AudioFileClip(mp3_file_name)
        image_clip = ImageClip(image_file_name, duration=audio_clip.duration)
        video_clip = CompositeVideoClip([image_clip.set_duration(audio_clip.duration).set_audio(audio_clip)])

        video_clip.write_videofile(mp4_file_name, codec='libx264', audio_codec='aac', fps=24)
        os.remove(mp3_file_name)

        return FileResponse(mp4_file_name, media_type='video/mpeg', filename=mp4_file_name)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# 静的ファイル（画像ファイル）の配信を設定
app.mount("/static", StaticFiles(directory="static"), name="static")
