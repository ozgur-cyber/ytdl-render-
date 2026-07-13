from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

class DownloadRequest(BaseModel):
    url: str

def cleanup_old_files():
    now = time.time()
    for filename in os.listdir("static"):
        filepath = os.path.join("static", filename)
        if os.stat(filepath).st_mtime < now - 600: # 10 dakika
            try:
                os.remove(filepath)
            except:
                pass

# Web sitemizin şık arayüzü doğrudan bu adreste açılacak
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>1080p Video Downloader - Lokal Test</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white flex flex-col items-center justify-center min-h-screen p-4">
        <div class="max-w-md w-full bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-2xl text-center">
            <h1 class="text-3xl font-extrabold mb-2 bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                1080p Downloader
            </h1>
            <p class="text-gray-400 text-sm mb-6">YouTube Video İndirme Sitesi (Lokal Test)</p>
            
            <input
                type="text"
                id="videoUrl"
                placeholder="YouTube Video Linki Yapıştırın..."
                class="w-full p-4 rounded-xl bg-gray-800 border border-gray-700 mb-4 focus:outline-none focus:border-red-500 text-white transition"
            />

            <button
                id="downloadBtn"
                onclick="startDownload()"
                class="w-full bg-red-600 hover:bg-red-700 p-4 rounded-xl font-bold transition disabled:bg-gray-800 disabled:text-gray-500"
            >
                İndirme Bağlantısı Oluştur
            </button>

            <p id="errorText" class="text-red-500 mt-4 text-sm hidden"></p>

            <div id="successBox" class="mt-6 p-4 bg-gray-850 rounded-xl border border-green-900/30 hidden">
                <p class="text-green-400 text-sm mb-3">Videonuz Başarıyla Hazırlandı!</p>
                <a
                    id="downloadLink"
                    href="#"
                    download="video.mp4"
                    class="inline-block w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-xl transition text-center"
                >
                    Cihaza Kaydet (.MP4)
                </a>
            </div>
        </div>

        <script>
            async function startDownload() {
                const urlInput = document.getElementById('videoUrl');
                const btn = document.getElementById('downloadBtn');
                const errorText = document.getElementById('errorText');
                const successBox = document.getElementById('successBox');
                const downloadLink = document.getElementById('downloadLink');

                const url = urlInput.value.trim();
                if(!url) return;

                btn.disabled = true;
                btn.innerText = 'Video İşleniyor (FFmpeg)...';
                errorText.classList.add('hidden');
                successBox.classList.add('hidden');

                try {
                    const response = await fetch('/download', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url: url })
                    });

                    const data = await response.json();
                    if(!response.ok) throw new Error(data.detail || 'Bir hata oldu.');

                    downloadLink.href = data.download_url;
                    successBox.classList.remove('hidden');
                } catch (err) {
                    errorText.innerText = err.message;
                    errorText.classList.remove('hidden');
                } finally {
                    btn.disabled = false;
                    btn.innerText = 'İndirme Bağlantısı Oluştur';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/download")
def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(cleanup_old_files)
    
    video_url = request.url
    file_id = str(uuid.uuid4())
    output_filename = f"static/{file_id}.mp4"
    output_template = f"static/{file_id}.%(ext)s"

    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if not os.path.exists(output_filename):
            raise HTTPException(status_code=500, detail="Video işlenirken bir hata oluştu.")

        return {"download_url": f"/static/{file_id}.mp4"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
