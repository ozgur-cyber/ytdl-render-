from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            <p class="text-gray-400 text-sm mb-6">YouTube Video İndirme Sitesi (Merkeziyetsiz Hızlı Sürüm)</p>
            
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
                btn.innerText = 'Bağlantı Çözülüyor (Tarayıcı Üzerinden)...';
                errorText.classList.add('hidden');
                successBox.classList.add('hidden');

                // Tarayıcının doğrudan sorgulayacağı en stabil topluluk sunucuları ve endpointleri
                const apiPool = [
                    "https://api.cobalt.meowing.de",
                    "https://cobalt.canine.tools",
                    "https://api.cobalt.meowing.de/api/json",
                    "https://cobalt.canine.tools/api/json"
                ];

                let success = false;

                for (const apiUrl of apiPool) {
                    try {
                        const response = await fetch(apiUrl, {
                            method: 'POST',
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                url: url,
                                videoQuality: "1080",
                                downloadMode: "auto"
                            })
                        });

                        if (response.ok) {
                            const data = await response.json();
                            if (data && data.url) {
                                downloadLink.href = data.url;
                                successBox.classList.remove('hidden');
                                success = true;
                                break; 
                            }
                        }
                    } catch (err) {
                        console.log(apiUrl + " denemesi başarısız oldu, sıradakine geçiliyor.");
                    }
                }

                if (!success) {
                    errorText.innerText = "Tüm yedek sunucular şu an yoğun veya bu video kısıtlanmış. Lütfen biraz sonra tekrar deneyin.";
                    errorText.classList.remove('hidden');
                }

                btn.disabled = false;
                btn.innerText = 'İndirme Bağlantısı Oluştur';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)
