import os
import json
import gspread
from google.oauth2.service_account import Credentials
import urllib.request
import urllib.parse
from moviepy.editor import ImageClip, AudioFileClip

try:
    # 1. Google Sheets & Drive Authentication (Safe JSON parsing)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    raw_creds = os.environ['GOOGLE_CREDENTIALS'].strip()
    
    # Agar galti se extra quotes aa gaye ho toh unhe saaf karna
    if raw_creds.startswith("'") and raw_creds.endswith("'"):
        raw_creds = raw_creds[1:-1]
    elif raw_creds.startswith('"') and raw_creds.endswith('"'):
        raw_creds = raw_creds[1:-1]
        
    creds_json = json.loads(raw_creds)
    creds = Credentials.from_service_account_info(creds_json, scopes=scope)
    gc = gspread.authorize(creds)

    # Sheet open karna
    sheet = gc.open('YOUTUBEAPI').sheet1
    records = sheet.get_all_records()

    print("Google Sheets connection successful!")

    # 2. Check rows for 'Ready for Voiceover'
    for i, row in enumerate(records, start=2):
        if row.get('Status') == 'Ready for Voiceover':
            topic_name = str(row.get('Topic')).replace(" ", "_")[:20]
            script_text = row.get('Script')
            
            print(f"Processing topic: {topic_name}")
            
            # Audio & File paths
            audio_path = f"{topic_name}.mp3"
            image_path = f"{topic_name}_bg.jpg"
            video_path = f"{topic_name}.mp4"
            
            # A. Edge TTS se Audio banana
            with open("temp_script.txt", "w", encoding="utf-8") as f:
                f.write(script_text)
            os.system(f'edge-tts --voice hi-IN-MadhurNeural -f temp_script.txt --write-media "{audio_path}"')
            
            # B. Pollinations AI se Background Image banana
            image_prompt = f"Minimalist premium 2D animation style, dark deep blue charcoal background with neon accents, depicting {topic_name}, highly detailed, 9:16 aspect ratio"
            encoded_prompt = urllib.parse.quote(image_prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
            urllib.request.urlretrieve(image_url, image_path)
            
            # C. MoviePy se Video Render karna
            try:
                audio_clip = AudioFileClip(audio_path)
                video_clip = (ImageClip(image_path)
                              .set_duration(audio_clip.duration)
                              .resize(lambda t: 1 + 0.03 * (t / audio_clip.duration)) 
                              .set_position(('center', 'center')))
                
                video_clip = video_clip.set_audio(audio_clip)
                video_clip.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
                
                print(f"Video successfully generated: {video_path}")
                
                # Sheet mein status update karna
                sheet.update_cell(i, 4, 'Video Ready')
                
            except Exception as e:
                print(f"Error generating video: {e}")

except Exception as e:
    print(f"Authentication or Connection Error: {e}")
