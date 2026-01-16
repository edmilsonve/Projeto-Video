import os
import json
import tempfile
from services.openai_service import OpenAIService
from services.groq import GroqService
from services.image_gen import ImageGenerationService, VoiceService
from storage.local import LocalStorageService
from utils.text import slugify

class VideoOrchestrator:
    def __init__(self):
        self.state_file = "state.json"
        
        # Initialize Services
        self.script_service = OpenAIService()
        self.transcription_service = GroqService()
        self.image_service = ImageGenerationService()
        self.voice_service = VoiceService()
        self.storage_service = LocalStorageService(output_root="final_videos")
        
        self.current_video = {}
        self.load_state()

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                self.current_video = json.load(f)

    def save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(self.current_video, f, indent=2)

    def start_pipeline(self, topic: str):
        print(f"--- Starting Pipeline for: {topic} ---")
        self.current_video = {"topic": topic, "status": "started", "scenes": []}
        self.save_state()
        
        # 1. Script (JSON)
        print("Step 1: Generating Script (Structured)...")
        script_data = self.script_service.generate_script(topic)
        if not script_data or "scenes" not in script_data:
            print("Failed to generate script JSON.")
            return
        
        self.current_video["script_data"] = script_data
        self.save_state()
        
        scenes = script_data["scenes"]
        temp_videos = []
        slug = slugify(topic)[:30]
        
        # 2. Process Scenes
        print(f"Step 2: Processing {len(scenes)} Scenes...")
        
        for i, scene in enumerate(scenes):
            print(f"  > Processing Scene {i+1}...")
            scene_text = scene.get("text")
            scene_visual = scene.get("visual")
            
            # A. Audio
            audio_filename = f"tmp_{slug}_s{i}.mp3"
            audio_path = self.voice_service.generate_voice(scene_text, audio_filename)
            if not audio_path:
                print(f"    Failed Audio for Scene {i+1}")
                continue
                
            # B. Image
            img_filename = f"tmp_{slug}_s{i}.png"
            # Truncate visual prompt just in case
            img_path = self.image_service.generate_image(scene_visual[:1000], img_filename)
            if not img_path:
                 print(f"    Failed Image for Scene {i+1}")
                 continue

            # C. Assembly Scene (Image + Audio)
            scene_video_name = f"tmp_{slug}_s{i}.mp4"
            scene_video_path = self._assemble_video(img_path, audio_path, scene_video_name)
            
            if scene_video_path:
                temp_videos.append(scene_video_path)
                self.current_video["scenes"].append({
                    "id": i,
                    "text": scene_text,
                    "video_path": scene_video_path
                })
                self.save_state()
        
        if not temp_videos:
            print("No scenes were successfully generated.")
            return

        # 5. Concatenation
        print("Step 5: Concatenating Scenes...")
        try:
            output_filename = f"{slug}.mp4"
            final_path = self._concatenate_videos(temp_videos, output_filename)
            
            if final_path:
                print(f"Video assembled successfully: {final_path}")
                self.current_video["final_path"] = final_path
                self.current_video["status"] = "completed"
                
                # Save to final storage
                saved_location = self.storage_service.save_file(final_path)
                print(f"Final video saved to: {saved_location}")
            else:
                print("Failed to assemble video.")
                
        except Exception as e:
            print(f"Assembly Error: {e}")
            
        self.save_state()

    def _assemble_video(self, image_path, audio_path, output_filename):
        # Determine FFMPEG Path
        ffmpeg_exe = os.path.join(os.getcwd(), "ffmpeg_bin", "bin", "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = "ffmpeg"

        temp_out = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Scene Assembly command
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            temp_out
        ]
        
        import subprocess
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return temp_out
        except subprocess.CalledProcessError as e:
            print(f"FFMPEG Scene Assembly Failed: {e.stderr.decode()}")
            return None

    def _concatenate_videos(self, video_paths, output_filename):
        # Create input list file
        list_file_path = os.path.join(tempfile.gettempdir(), "concat_list.txt")
        with open(list_file_path, "w") as f:
            for path in video_paths:
                # ffmpeg requires paths with forward slashes and 'file ' prefix
                formatted_path = path.replace("\\", "/")
                f.write(f"file '{formatted_path}'\n")
        
        ffmpeg_exe = os.path.join(os.getcwd(), "ffmpeg_bin", "bin", "ffmpeg.exe")
        if not os.path.exists(ffmpeg_exe):
            ffmpeg_exe = "ffmpeg"
            
        temp_out = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Concat command
        cmd = [
            ffmpeg_exe, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file_path,
            "-c", "copy",
            temp_out
        ]
        
        import subprocess
        print(f"Running FFMPEG Concat...")
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return temp_out
        except subprocess.CalledProcessError as e:
            print(f"FFMPEG Concat Failed: {e.stderr.decode()}")
            return None
