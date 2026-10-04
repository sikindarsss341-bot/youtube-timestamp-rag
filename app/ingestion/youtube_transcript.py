from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url):
    parsed_url = urlparse(url)

    # Short YouTube URL: youtu.be/VIDEO_ID
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path.strip("/")

    # Normal YouTube URL: youtube.com/watch?v=VIDEO_ID
    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    return None


def get_transcript(video_id):
    api = YouTubeTranscriptApi()
    try:
        return api.fetch(video_id)
    except Exception:
        # Fallback to any available transcript or translated track
        transcript_list = api.list(video_id)
        for t in transcript_list:
            if t.is_translatable:
                try:
                    return t.translate("en").fetch()
                except Exception:
                    pass
            return t.fetch()
        raise


if __name__ == "__main__":
    youtube_url = input("Enter YouTube URL: ")

    video_id = extract_video_id(youtube_url)

    if not video_id:
        print("❌ Invalid YouTube URL.")
        exit()

    print(f"\nVideo ID: {video_id}")

    transcript = get_transcript(video_id)

    print("\n--- Transcript ---\n")

    for item in transcript:
        print(f"[{item.start:.2f}s] {item.text}")