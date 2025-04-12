import edge_tts
import asyncio
import json
# import random
from aiohttp import WSServerHandshakeError
import subprocess
import shutil
import re
import os
import edge_tts
import win10toast

from modules.text_splicer import split_text_by_period
from modules.cleanup import textCleanUp


async def generate_voice_using_config(text: str, output_file: str) -> None:
    """Generate voice using config file with retry logic."""
    with open("config.json", "r") as f:
        config = json.load(f)

    retries = 3  # Number of retries
    for attempt in range(retries):
        try:
            # Create a new Communicate object for each call
            communicate = edge_tts.Communicate(
                text,
                voice=config['voice_short_name'],
                rate=config['rate'],
                volume=config['volume'],
                pitch=config['pitch']
            )
            await communicate.save(output_file)
            break  # Exit the loop if successful
        except WSServerHandshakeError as e:
            if attempt < retries - 1:
                print(f"Attempt {attempt + 1} failed. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retrying
            else:
                print("All retry attempts failed.")
                raise e
        except RuntimeError as e:
            print(f"RuntimeError: {e}. Retrying with a new Communicate object...")
            if attempt < retries - 1:
                await asyncio.sleep(5)  # Wait before retrying
            else:
                raise e


with open("config.json", "r") as f:
    config = json.load(f)

async def generate_voice_with_limit(semaphore, text, output_file:str) -> None:
    async with semaphore:
        await generate_voice_using_config(text, output_file)

async def generate_voice_from_folders(story_dir:str, story_file:str, chunk_length:int) -> None:
    if not os.path.exists(os.path.join("audioOutput", story_dir, story_file)):
        os.makedirs(os.path.join("audioOutput", story_dir,story_file))
    print(f"Processing {story_dir} - '{story_file}'...")

    # with open(os.path.join("inputFiles", story_dir, story_file), "r", encoding="utf-8") as f:
    #     TEXT = f.read()
    texts = split_text_by_period(os.path.join("inputFiles", story_dir, story_file), chunk_length)
    semaphore = asyncio.Semaphore(3)  # Limit to n concurrent tasks
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
        cmd = fr'''cd "{subdir_path}" && ffmpeg -y -f concat -safe 0 -i filelist.txt -c copy "..\{story_file.replace(".txt", "").replace(".md", "")}.mp3" && cd ..\..'''
        subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        shutil.rmtree(os.path.join(subdir_path))

async def process_directory(semaphore, story_dir, chunk_length):
    """Process a single directory."""
    async with semaphore:
        print(f"Processing directory: {story_dir}")
        if not os.path.exists(os.path.join("audioOutput", story_dir)):
            os.makedirs(os.path.join("audioOutput", story_dir))
        story_files = [
            f for f in os.listdir(os.path.join("inputFiles", story_dir)) if f.endswith(".txt") or f.endswith(".md")
        ]
        if not story_files:
            print(f"No text files found in the '{story_dir}' directory.")
            return
        for story_file in story_files:
            await generate_voice_from_folders(story_dir, story_file, chunk_length)


def chunk_list(lst, chunk_size):
    """Divide a list into chunks of a specified size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


async def amain() -> None:
    """Main function"""

    chunk_length = config['chunk_length']

    # Get all story directories
    story_dirs = [f for f in os.listdir("inputFiles") if os.path.isdir(os.path.join("inputFiles", f))]
    if not story_dirs:
        print("No stories found in the 'inputFiles' directory.")
        return

    folder_chunk_size = config['concurrent_folders']

    # Divide story directories into user-defined chunks
    chunks = list(chunk_list(story_dirs, folder_chunk_size))

    while True:
        # Display chunks to the user
        print("\nAvailable chunks:")
        for idx, chunk in enumerate(chunks):
            print(f"{idx + 1}: {chunk}")

        # Ask the user to select a chunk
        while True:
            try:
                selected_chunk = int(input(f"Select a chunk to process (1-{len(chunks)}): "))
                if 1 <= selected_chunk <= len(chunks):
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        # Get the selected chunk
        selected_dirs = chunks[selected_chunk - 1]

        # Process the selected chunk with the user-defined concurrency
        semaphore = asyncio.Semaphore(folder_chunk_size)  # Limit to user-defined concurrent folder processing tasks
        await asyncio.gather(
            *(process_directory(semaphore, story_dir, chunk_length) for story_dir in selected_dirs)
        )

        # Ask the user if they want to process another chunk
        win10toast.ToastNotifier().show_toast(
            "Processing Complete",
            f"Processed chunk: {selected_dirs}",
            duration=10,
            threaded=True
        )
        process_another = input("Do you want to process another chunk? (yes/no): ").strip().lower()
        if process_another != "yes":
            print("Exiting program.")
            break


if __name__ == "__main__":
    asyncio.run(amain())


