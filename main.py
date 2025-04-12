import edge_tts
import asyncio
import json
# import random
import subprocess
import shutil
import re
import os
import edge_tts

from modules.text_splicer import split_text_by_period
from modules.cleanup import textCleanUp

 

async def generate_voice_using_config(text:str, output_file:str) -> None:
    """Generate voice using config file"""
    with open("config.json", "r") as f:
        config = json.load(f)

    communicate = edge_tts.Communicate(
        text, 
        voice=config['voice_name'], 
        rate=config['rate'], 
        volume=config['volume'], 
        pitch=config['pitch']
    )
    await communicate.save(output_file)


with open("config.json", "r") as f:
    config = json.load(f)

async def generate_voice_with_limit(semaphore, text, output_file:str) -> None:
    async with semaphore:
        await generate_voice_using_config(text, output_file)

async def generate_voice_from_folders(story_dir:str, story_file:str, chunk_length:int) -> None:
    if not os.path.exists(os.path.join("audioOutput", story_dir, story_file)):
        os.makedirs(os.path.join("audioOutput", story_dir,story_file))
    print(f"Processing {story_file}...")

    # with open(os.path.join("inputFiles", story_dir, story_file), "r", encoding="utf-8") as f:
    #     TEXT = f.read()
    texts = split_text_by_period(os.path.join("inputFiles", story_dir, story_file), chunk_length)
    semaphore = asyncio.Semaphore(10)  # Limit to n concurrent tasks
    await asyncio.gather(*(generate_voice_with_limit(semaphore, textCleanUp(text), output_file=(os.path.join("audioOutput", story_dir, story_file,f'{i}.mp3'))) for i,text in enumerate(texts)))
    subdir_path = os.path.join("audioOutput", story_dir, story_file)
    if os.path.isdir(subdir_path):  # Check if it's a directory
        mp3_files = [f for f in os.listdir(subdir_path) if f.endswith('.mp3')]
        if not mp3_files:
            raise ValueError("No .mp3 files found in the folder.")

        # Sort files numerically based on the first number in the filename
        def extract_first_number(filename):
            match = re.search(r'(\d+)', filename)
            return int(match.group(1)) if match else float('inf')

        mp3_files.sort(key=extract_first_number)
        # print(f"Sorted mp3 files: {mp3_files}")
        with open(os.path.join(subdir_path, "filelist.txt"), 'w') as f:
            for mp3_file in mp3_files:
                f.write(f"file '{mp3_file}'\n")
        cmd = fr'''cd "{subdir_path}" && ffmpeg -y -f concat -safe 0 -i filelist.txt -c copy "..\{story_file.replace(".txt", "")}.mp3" && cd ..\..'''
        subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        shutil.rmtree(os.path.join(subdir_path))

async def amain() -> None:
    """Main function"""

    chunk_length = config['chunk_length']

    story_dirs = [f for f in os.listdir("inputFiles") if os.path.isdir(os.path.join("inputFiles", f))]
    if not story_dirs:
        print("No stories found in the 'stories' directory.")
        return
    for story_dir in story_dirs:
        print(f"Processing directory: {story_dir}")
        #Make a directory audio if it doesn't exist
        if not os.path.exists(os.path.join("audioOutput", story_dir)):
            os.makedirs(os.path.join("audioOutput", story_dir))
        story_files = [f for f in os.listdir(os.path.join("inputFiles", story_dir)) if f.endswith(".txt")]
        if not story_files:
            print(f"No text files found in the '{story_dir}' directory.")
            continue
        for story_file in story_files:
            await generate_voice_from_folders(story_dir, story_file, chunk_length)



if __name__ == "__main__":
    asyncio.run(amain())

