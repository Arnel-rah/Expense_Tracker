import os
import sys
import subprocess
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from pytube import YouTube

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

def normalize_youtube_url(url: str) -> str:
    url = url.strip()
    url = url.replace("m.youtube.com", "www.youtube.com")
    # youtu.be/<id> → watch?v=<id>
    if "youtu.be/" in url:
        vid = url.split("youtu.be/")[1].split("?")[0].strip("/")
        return f"https://www.youtube.com/watch?v={vid}"
    # /shorts/<id> → watch?v=<id>
    if "/shorts/" in url:
        vid = url.split("/shorts/")[1].split("?")[0].strip("/")
        return f"https://www.youtube.com/watch?v={vid}"
    # Nettoie certains params parasites (?si=…)
    parsed = urlparse(url)
    if parsed.netloc.endswith("youtube.com") and parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        # On ne garde que v + (playlist éventuellement)
        keep = []
        if "v" in qs:
            keep.append(f"v={qs['v'][0]}")
        if "list" in qs:
            keep.append(f"list={qs['list'][0]}")
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if keep:
            return f"{base}?{'&'.join(keep)}"
        return base
    return url

def has_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def to_mp3(filepath: Path) -> Path:
    """Convertit en .mp3 via ffmpeg si dispo. Supprime l’original si succès."""
    if not has_ffmpeg():
        print("ℹ️ ffmpeg non détecté : le fichier audio reste dans son format d’origine.")
        return filepath
    mp3_path = filepath.with_suffix(".mp3")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(filepath), str(mp3_path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        filepath.unlink(missing_ok=True)
        return mp3_path
    except Exception as e:
        print(f"⚠️ Conversion mp3 échouée: {e}")
        return filepath

def download_with_pytube(url: str, audio_only: bool) -> Path:
    yt = YouTube(url)
    print(f"🎯 Titre: {yt.title}")

    if audio_only:
        stream = (yt.streams
                    .filter(only_audio=True)
                    .order_by("abr")
                    .desc()
                    .first())
        if not stream:
            raise RuntimeError("Aucun flux audio trouvé.")
        out = Path(stream.download(output_path=DOWNLOAD_DIR))
        # Convertir en mp3 si possible
        return to_mp3(out)
    else:
        # progressive=True → mp4 avec audio inclus
        stream = (yt.streams
                    .filter(progressive=True, file_extension="mp4")
                    .order_by("resolution")
                    .desc()
                    .first())
        if not stream:
            raise RuntimeError("Aucun flux vidéo progressif trouvé.")
        out = Path(stream.download(output_path=DOWNLOAD_DIR))
        return out

def have_ytdlp() -> bool:
    try:
        import yt_dlp  # noqa: F401
        return True
    except Exception:
        return False

def download_with_ytdlp(url: str, audio_only: bool) -> Path:
    # Requires: pip install yt_dlp  (+ ffmpeg pour mp3)
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        raise RuntimeError("yt-dlp n’est pas installé.")

    outtmpl = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
    if audio_only:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ] if has_ffmpeg() else []
        }
    else:
        ydl_opts = {
            "format": "mp4[height<=1080]/bestvideo[ext=mp4]+bestaudio/best",
            "outtmpl": outtmpl,
            "merge_output_format": "mp4",
        }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Quand postprocessors sont utilisés, l’extension peut changer (mp3).
        if audio_only and has_ffmpeg():
            filename = os.path.splitext(filename)[0] + ".mp3"
        return Path(filename)

def main():
    url = input("🎥 Enter YouTube URL: ").strip()
    url = normalize_youtube_url(url)

    print("\n--- Select download type ---")
    print("1. Video (mp4)")
    print("2. Audio only (mp3 si ffmpeg)")
    choice = input("👉 Your choice (1/2): ").strip()

    audio_only = (choice == "2")

    try:
        print("⬇️ Tentative avec pytube…")
        out = download_with_pytube(url, audio_only=audio_only)
        print(f"✅ Terminé : {out}")
        return
    except Exception as e:
        print(f"⚠️ Échec pytube: {e}")

    # Fallback vers yt-dlp si dispo
    if have_ytdlp():
        try:
            print("🔁 Fallback avec yt-dlp…")
            out = download_with_ytdlp(url, audio_only=audio_only)
            print(f"✅ Terminé : {out}")
            return
        except Exception as e:
            print(f"❌ Échec yt-dlp: {e}")
    else:
        print("ℹ️ yt-dlp n’est pas installé. Pour l’installer :")
        print("    py -3.13 -m pip install yt_dlp")
        print("Pour la conversion mp3, installe ffmpeg (et ajoute-le au PATH).")

if __name__ == "__main__":
    main()
