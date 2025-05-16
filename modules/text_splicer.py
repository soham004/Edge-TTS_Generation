import time
from modules.cleanup import textCleanUp
import re

def split_text_by_period(filename: str, limit: int) -> list:
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read().strip()
        text = textCleanUp(text)
    
    chunks = []
    start = 0
    
    # Minimum chunk length to be considered valid (adjust as needed)
    MIN_CHUNK_LENGTH = 10

    while start < len(text):
        end = start + limit

        if end >= len(text):  # End of text reached
            chunk = text[start:].strip()
            if chunk and len(chunk) >= MIN_CHUNK_LENGTH:  # Ensure chunk is substantial
                chunks.append(chunk)
            elif chunk and chunks:  # If it's too small but not empty, append to the last chunk
                chunks[-1] = chunks[-1] + " " + chunk
            break

        # Look for the nearest period (.) or question mark (?) after the limit
        stop_pos = text.find('.', int(end))
        qmark_pos = text.find('?', int(end))
        excl_pos = text.find('!', int(end))  # Also consider exclamation marks

        # Find the nearest valid stopping position
        if stop_pos == -1:
            stop_pos = float('inf')
        if qmark_pos == -1:
            qmark_pos = float('inf')
        if excl_pos == -1:
            excl_pos = float('inf')

        best_pos = min(stop_pos, qmark_pos, excl_pos)

        # If a stopping point is found within a reasonable range, extend the chunk
        if best_pos != float('inf') and best_pos - start < limit * 1.5:
            end = best_pos + 1  # Include the period, question mark, or exclamation mark

        chunk = text[start:end].strip()
        
        # Check if the chunk is meaningful
        if chunk and len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)
        elif chunk and chunks:  # If it's too small but not empty, append to the previous chunk
            chunks[-1] = chunks[-1] + " " + chunk
        
        start = end  # Move to the next part

    # Additional validation - ensure no chunks with just punctuation
    filtered_chunks = []
    for chunk in chunks:
        # Check if chunk contains meaningful text (not just punctuation/spaces)
        if re.search(r'[a-zA-Z0-9]', chunk):
            filtered_chunks.append(chunk)
    
    return filtered_chunks


if __name__ == "__main__":
    while True:
        file = input("Please input the file to splice.\n>>>")
        if not file.endswith(".txt"):
            print(f"Invalid file: {file}\nTry again.")
            continue
        try:
            charLen = int(input("Please input the character limit per chunk.\n>>>"))
        except ValueError:
            print("Invalid input. Please input an integer.")
            continue
        try:
            chunks = split_text_by_period(file, charLen)
            it = 1
            for chunk in chunks:
                output = f"output/chunk{it}.txt"
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(chunk)
                print(f"Chunk {it} saved to {output}")

                it += 1

            print(f"\nSuccess. You can close by pressing the exit button or CTRL + C twice.")
            time.sleep(5)
        except Exception as e:
            print(f"An error occured: {e}. Restarting...")
            time.sleep(3)
