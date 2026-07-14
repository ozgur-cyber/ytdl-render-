from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid
import time
import httpx

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

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>1080p Video Downloader</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-950 text-white flex flex-col items-center justify-center min-h-screen p-4">
        <div class="max-w-md w-full bg-gray-900 p-8 rounded-2xl border border-gray-800 shadow-2xl text-center">
            <h1 class="text-3xl font-extrabold mb-2 bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                1080p Downloader
            </h1>
            <p class="text-gray-400 text-sm mb-6">YouTube Video İndirme Sitesi (Süper Hibrit Sürüm)</p>
            
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
                    target="_blank"
                    class="inline-block w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-xl transition text-center"
                >
                    Tarayıcıda Aç ve İndir (.MP4)
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
                btn.innerText = 'Video Hazırlanıyor (30-60 Saniye Sürebilir)...';
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
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(cleanup_old_files)
    video_url = request.url
    file_id = str(uuid.uuid4())
    output_filename = f"static/{file_id}.mp4"
    output_template = f"static/{file_id}.%(ext)s"

    # YÖNTEM 1: Safari/iOS Taklidi ile Doğrudan yt-dlp Kullanımı (Engelleri Aşar)
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web_safari'] # Sihirli taklit parametreleri
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if os.path.exists(output_filename):
            return {"download_url": f"/static/{file_id}.mp4"}
    except Exception as direct_err:
        print(f"Dogrudan indirme basarisiz oldu: {direct_err}. Yedek Cobalt sunuculari deneniyor...")

    # YÖNTEM 2: Üstteki yöntem başarısız olursa yedekli Cobalt havuzunu dene
    COBALT_API_POOL = [
        "https://api.cobalt.meowing.de/",
        "https://api.cobalt.canine.tools/"
    ]
    
    payload = {
        "url": video_url,
        "videoQuality": "1080",
        "downloadMode": "auto"
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        for api_url in COBALT_API_POOL:
            try:
                response = await client.post(api_url, json=payload, headers=headers, timeout=12.0)
                if response.status_code == 200:
                    result = response.json()
                    if "url" in result:
                        return {"download_url": result["url"]}
            except Exception as cobalt_err:
                print(f"Cobalt sunucusu hata verdi ({api_url}): {cobalt_err}")
                continue

    raise HTTPException(
        status_code=500, 
        detail="Şu an tüm indirme yöntemleri YouTube engeline takıldı. Lütfen birkaç dakika sonra tekrar deneyin."
    )
