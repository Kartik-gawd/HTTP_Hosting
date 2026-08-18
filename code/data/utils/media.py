import os
import time

try:
    import ffmpeg as ffmpeg_python
    FFMPEG_PROBE_AVAILABLE = True
except ImportError:
    ffmpeg_python = None
    FFMPEG_PROBE_AVAILABLE = False
    print("[FFmpeg] ffmpeg-python not installed. Run: pip install ffmpeg-python")

def _is_valid_vtt(path: str) -> bool:
    #Return True if path exists, is non-empty, and looks like valid WebVTT
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
        return "WEBVTT" in head
    except OSError:
        return False

def probe_video(filepath: str) -> dict:
    #Return dict {audio_tracks, subtitle_tracks} using ffmpeg.probe
    if not FFMPEG_PROBE_AVAILABLE:
        return {"audio_tracks": [], "subtitle_tracks": []}
    try:
        probe   = ffmpeg_python.probe(filepath)
        streams = probe.get("streams", [])
        sub_tracks = []
        for s in streams:
            idx   = s.get("index", 0)
            ctype = s.get("codec_type", "")
            tags  = s.get("tags", {})
            lang  = tags.get("language", tags.get("LANGUAGE", "und"))
            title = tags.get("title",    tags.get("TITLE", ""))
            if ctype == "subtitle":
                sub_tracks.append({"index": idx, "lang": lang, "title": title or lang})
        return {"audio_tracks": [], "subtitle_tracks": sub_tracks}
    except Exception as e:
        print(f"[FFmpeg probe] {e}")
        return {"audio_tracks": [], "subtitle_tracks": []}

def extract_subtitles(filepath: str, base: str, extract_dir: str,
                       cancel_event=None, on_ready=None, register_process=None) -> list[str]:
    
    if not FFMPEG_PROBE_AVAILABLE:
        return []
    extracted = []
    try:
        video_stem = os.path.splitext(os.path.basename(filepath))[0]
        sub_dir    = os.path.join(extract_dir, video_stem)
        os.makedirs(sub_dir, exist_ok=True)

        probe   = ffmpeg_python.probe(filepath)
        streams = probe.get("streams", [])
        for s in streams:
            if cancel_event is not None and cancel_event.is_set():
                break
            if s.get("codec_type") != "subtitle":
                continue
            idx  = s.get("index", 0)
            tags = s.get("tags", {})
            lang = tags.get("language", tags.get("LANGUAGE", "und"))
            out_name = f"{video_stem}.{lang}.{idx}.vtt"
            out_path = os.path.join(sub_dir, out_name)
            tmp_path = out_path + ".part"
            rel = os.path.relpath(out_path, extract_dir).replace("\\", "/")
            url = "/__subtitles_extracted__/" + rel

            if os.path.exists(out_path) and not _is_valid_vtt(out_path):
                # Invalid/incomplete cached file: remove and re-extract.
                try:
                    os.remove(out_path)
                except OSError:
                    pass

            if _is_valid_vtt(out_path):
                # Cache hit: never invoke FFmpeg for an already-cached stream.
                extracted.append(url)
                if on_ready:
                    on_ready(url)
                continue

            # Clean up any stale temp file from a previous interrupted run.
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

            try:
                process = (
                    ffmpeg_python
                    .input(filepath)
                    .output(tmp_path, map=f"0:{idx}", f="webvtt")
                    .overwrite_output()
                    
                    .run_async(pipe_stdout=False, pipe_stderr=False)
                )
                if register_process:
                    register_process(process)

                cancelled = False
                while process.poll() is None:
                    if cancel_event is not None and cancel_event.is_set():
                        cancelled = True
                        try:
                            process.terminate()
                            process.wait(timeout=5)
                        except Exception:
                            try:
                                process.kill()
                            except Exception:
                                pass
                        break
                    time.sleep(0.1)

                if cancelled:
                    # Cancellation cleanup: remove any incomplete output.
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except OSError:
                        pass
                    try:
                        if os.path.exists(out_path):
                            os.remove(out_path)
                    except OSError:
                        pass
                    break

                if process.returncode != 0 or not _is_valid_vtt(tmp_path):
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except OSError:
                        pass
                    continue

                try:
                    os.replace(tmp_path, out_path)
                except OSError:
                    continue
            except Exception as ex:
                print(f"[FFmpeg sub extract] stream {idx}: {ex}")
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except OSError:
                    pass
                continue

            extracted.append(url)
            if on_ready:
                on_ready(url)
    except Exception as e:
        print(f"[FFmpeg sub extract] probe error: {e}")
    return extracted