import edge_tts
import asyncio
import json
import random

import edge_tts

TEXT = """Deep beneath the streets of London, past the gleaming Atrium of the Ministry of Magic, beyond circular hallways of shifting doors, lies a chamber shrouded in more mystery than perhaps any other place in the wizarding world. The air here feels different – heavier, older somehow, as though the very atmosphere has been undisturbed for centuries. The whispers that echo through this room speak of secrets that even the most learned magical scholars do not fully comprehend.

Tonight, as shadows gather in the corners of our room, let us descend together into the Department of Mysteries and explore the enigmatic Death Chamber – a place where the boundary between the living world and whatever lies beyond becomes thin enough to sense, if not to cross.

The Department of Mysteries itself is perhaps the most secretive division of the Ministry of Magic, a place where the fundamental forces and mysteries of existence are studied by wizards known as Unspeakables. These researchers are bound by magical oaths that prevent them from discussing their work with outsiders, adding layers of secrecy to the already mysterious nature of their studies.

Imagine yourself passing through the plain black door that marks the entrance to the Department. You find yourself in a circular room with identical doors set at regular intervals around the wall. When the door closes behind you, the walls begin to rotate, deliberately disorienting visitors – a security measure that ensures only those who know precisely where they're going can find their way through this labyrinthine department.
"""
OUTPUT_FILE = "test.mp3"

with open("config.json", "r") as f:
    config = json.load(f)

async def amain() -> None:
    """Main function"""        
    communicate = edge_tts.Communicate(
        TEXT, 
        voice=config['voice_name'], 
        rate=config['rate'], 
        volume=config['volume'], 
        pitch=config['pitch']
    )
    await communicate.save(OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(amain())

