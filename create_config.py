import json
import asyncio
import edge_tts

CONFIG_FILE = "config.json"

def choose_from_list(title, options):
    print(f"\n{title}")
    for idx, option in enumerate(options):
        print(f"{idx + 1}. {option}")
    while True:
        try:
            choice = int(input("Enter choice number: ")) - 1
            if 0 <= choice < len(options):
                return options[choice]
        except ValueError:
            pass
        print("Invalid input. Try again.")

def format_percent(value: str) -> str:
    """Ensure the value is in +n% or -n% format."""
    try:
        num = int(value)
        return f"{'+' if num >= 0 else ''}{num}%"
    except ValueError:
        return value if value.endswith('%') else value + '%'

def format_hz(value: str) -> str:
    """Ensure the value is in +nHz or -nHz format."""
    try:
        num = int(value)
        return f"{'+' if num >= 0 else ''}{num}Hz"
    except ValueError:
        return value if value.endswith('Hz') else value + 'Hz'

def get_input_with_default(prompt, default, formatter):
    user_input = input(f"{prompt} (default {default}): ").strip()
    return formatter(user_input) if user_input else default

async def main():
    print("Fetching available English voices...\n")
    voices = await edge_tts.list_voices()

    english_voices = [v for v in voices if v.get("Locale", "").startswith("en")]
    genders = sorted(set(v["Gender"] for v in english_voices))
    gender = choose_from_list("Select Gender", genders)

    filtered_voices = [v for v in english_voices if v["Gender"] == gender]
    short_names = [v["ShortName"] for v in filtered_voices]
    short_name = choose_from_list("Select Voice (ShortName)", short_names)

    selected_voice = next(v for v in filtered_voices if v["ShortName"] == short_name)
    full_name = selected_voice.get("Name", short_name)

    chunk_length_input = input("\nEnter chunk length (characters per segment): ").strip()
    try:
        chunk_length = int(chunk_length_input)
    except ValueError:
        print("Invalid number. Using default of 500.")
        chunk_length = 500

    rate = get_input_with_default("Enter speaking rate (e.g., +0%, -10%, 15)", "+0%", format_percent)
    volume = get_input_with_default("Enter volume (e.g., +0%, -5%, 10)", "+0%", format_percent)
    pitch = get_input_with_default("Enter pitch (e.g., +0Hz, -10Hz, 15)", "+0Hz", format_hz)

    config = {
        "gender": gender,
        "voice_short_name": short_name,
        "voice_name": full_name,
        "chunk_length": chunk_length,
        "rate": rate,
        "volume": volume,
        "pitch": pitch
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Configuration saved to {CONFIG_FILE}")
    print(f"Voice: {short_name}  |  Name: {full_name}")
    print(f"Rate: {rate}  |  Volume: {volume}  |  Pitch: {pitch}")

if __name__ == "__main__":
    asyncio.run(main())
