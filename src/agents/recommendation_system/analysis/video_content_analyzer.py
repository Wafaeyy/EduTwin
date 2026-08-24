"""
Resource Content Understanding (Section 24) - Piece 1: Video ID extraction.
Piece 2: Transcript fetching, with an honest access-status message.

Before we can fetch a video's transcript, we need just its 11-character
video ID, not the whole URL. This handles the common URL formats YouTube
uses.

Not every video has a transcript available (no captions, private video,
etc.). Rather than just returning None on failure, we return a clear status
message too, so nothing downstream has to guess why it failed.
"""

import os
import re
import json

from google import genai
from youtube_transcript_api import YouTubeTranscriptApi

GEMINI_MODEL = "gemini-2.5-flash"


def extract_youtube_video_id(url):
    """
    Pulls the video ID out of a YouTube URL, in whichever common format it
    was written.

    Args:
        url (str): a YouTube video URL.

    Returns:
        str or None: the video ID, or None if it couldn't be found.
    """
    patterns = [
        r"(?:v=|/)([0-9A-Za-z_-]{11})(?:&|$|\?|/)",
        r"youtu\.be/([0-9A-Za-z_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def get_video_transcript(video_id):
    """
    Fetches the real transcript (spoken words + timestamps) for a YouTube video.

    Args:
        video_id (str): the YouTube video ID.

    Returns:
        tuple: (entries, access_status)
            entries: a list of {"text": ..., "start_seconds": ...} dicts,
                     or None if unavailable.
            access_status: "ok" if it worked, or a short human-readable
                     reason why it didn't.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)

        entries = []

        for snippet in transcript:
            entries.append({
                "text": snippet.text,
                "start_seconds": snippet.start,
            })

        return entries, "ok"
    except Exception as error:
        return None, f"Transcript not accessible: {error}"


def format_timestamp(total_seconds):
    """
    Converts raw seconds into a readable mm:ss timestamp.

    Args:
        total_seconds (float): seconds from the start of the video.

    Returns:
        str: e.g. "12:34"
    """
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)

    return f"{minutes}:{seconds:02d}"


def build_transcript_text(transcript_entries):
    """
    Combines transcript entries into one readable block of text, with a
    timestamp before each line, so an LLM can reference real time ranges.

    Args:
        transcript_entries (list): output of get_video_transcript().

    Returns:
        str: formatted transcript text.
    """
    lines = []

    for entry in transcript_entries:
        timestamp = format_timestamp(entry["start_seconds"])
        lines.append(f"[{timestamp}] {entry['text']}")

    return "\n".join(lines)


def build_segmentation_prompt(transcript_text):
    """
    Builds the instruction that will be sent to an LLM, explicitly
    requesting JSON-only output so our code can reliably parse it.

    Args:
        transcript_text (str): output of build_transcript_text().

    Returns:
        str: the full prompt.
    """
    return f"""You are analyzing a video transcript with timestamps to identify distinct topic chapters.

Read the transcript below and split it into chapters, where each chapter covers one coherent topic.

Respond with ONLY a JSON array, no other text, no markdown code fences. Each item must have this exact shape:
{{"start_time": "mm:ss", "end_time": "mm:ss", "topic": "short topic name", "summary": "one sentence describing what is covered"}}

Transcript:
{transcript_text}
"""


def parse_gemini_json_response(response_text):
    """
    Safely parses Gemini's response as JSON, stripping markdown code fences
    if the model added them despite being told not to (a common real-world
    quirk of LLM output).

    Args:
        response_text (str): raw text from the Gemini response.

    Returns:
        list or None: parsed chapters, or None if parsing failed.
    """
    cleaned = response_text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        print(f"[video content] Could not parse Gemini's response as JSON ({error}).")
        return None


def analyze_video_content(video_url):
    """
    The full pipeline: YouTube URL -> transcript -> Gemini segmentation -> chapters.

    This is the ONLY function other parts of the engine need to call --
    everything else in this file is an internal step it uses.

    Args:
        video_url (str): a YouTube video URL.

    Returns:
        dict: {
            "access_status": "ok" or a clear reason it failed,
            "chapters": [...] or None,
        }
    """
    video_id = extract_youtube_video_id(video_url)

    if video_id is None:
        return {"access_status": "Could not extract a video ID from that URL.", "chapters": None}

    entries, transcript_status = get_video_transcript(video_id)

    if entries is None:
        return {"access_status": transcript_status, "chapters": None}

    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key is None:
        return {"access_status": "GEMINI_API_KEY environment variable is not set.", "chapters": None}

    transcript_text = build_transcript_text(entries)
    prompt = build_segmentation_prompt(transcript_text)

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model = "gemini-3.6-flash",
            contents=prompt,
        )
    except Exception as error:
        return {"access_status": f"Gemini API call failed: {error}", "chapters": None}

    chapters = parse_gemini_json_response(response.text)

    if chapters is None:
        return {"access_status": "Gemini responded, but its answer could not be parsed.", "chapters": None}

    return {"access_status": "ok", "chapters": chapters}


if __name__ == "__main__":
    print("=== Full pipeline test ===")
    test_url = "https://www.youtube.com/watch?v=aircAruvnKk"
    result = analyze_video_content(test_url)

    print(f"Access status: {result['access_status']}")

    if result["chapters"] is not None:
        for chapter in result["chapters"]:
            print(f"{chapter['start_time']}-{chapter['end_time']}: {chapter['topic']}")
            print(f"  {chapter['summary']}")