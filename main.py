from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

app = FastAPI()

# CORS engellerini tamamen kaldırıyoruz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
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
            <p class="text-gray-400 text-sm mb-6">YouTube Video İndirme Sitesi (Köprü Sunucu Sürümü)</p>
            
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
                <p class="text-green-400 text-sm mb-3 font-semibold">Videonuz Başarıyla Hazırlandı!</p>
                <a
                    id="downloadLink"
                    href="#"
                    target="_blank"
                    class="inline-block w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-xl transition text-center shadow-lg"
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
                btn.innerText = 'Bağlantı Çözülüyor (Köprü Kuruluyor)...';
                errorText.classList.add('hidden');
                successBox.classList.add('hidden');

                try {
                    // Kendi backend API'mize (Render sunucumuza) güvenli istek atıyoruz (CORS engeli yok!)
                    const response = await fetch('/api/download', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ url: url })
                    });

                    const data = await response.json();

                    if (response.ok && data.url) {
                        downloadLink.href = data.url;
                        successBox.classList.remove('hidden');
                    } else {
                        errorText.innerText = data.detail || "Video indirme linki oluşturulamadı. Lütfen başka bir video deneyin.";
                        errorText.classList.remove('hidden');
                    }
                } catch (err) {
                    errorText.innerText = "Sunucu bağlantısı başarısız oldu. Lütfen internetinizi kontrol edin.";
                    errorText.classList.remove('hidden');
                }

                btn.disabled = false;
                btn.innerText = 'İndirme Bağlantısı Oluştur';
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/download")
async def proxy_download(request: DownloadRequest):
    # Arka planda CORS engeline takılmadan sorgulayacağımız en kararlı API havuzu
    api_pool = [
        "https://api.cobalt.meowing.de",
        "https://cobalt.canine.tools",
    ]
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": request.url,
        "videoQuality": "1080",
        "downloadMode": "auto"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        for api_url in api_pool:
            try {
                response = await client.post(api_url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("url"):
                        return {"url": data["url"]}
            except Exception as e:
                continue
                
    raise HTTPException(status_code=500, detail="Tüm yedek sunucular şu an yoğun veya bu video kısıtlanmış. Lütfen az sonra tekrar deneyin.")
