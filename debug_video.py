from youtube_transcript_api import YouTubeTranscriptApi

# Test with a known TED video that definitely has captions
# TED: "Do schools kill creativity? | Sir Ken Robinson"
video_id = "iG9CE55wbtY" 

print(f"Testing Video ID: {video_id}")

try:
   print("Testing: api = YouTubeTranscriptApi(); api.list_transcripts(video_id) ... wait, dir said 'list', not 'list_transcripts'")
   
   api = YouTubeTranscriptApi() 
   print("Instance created (no args).")
   
   # Try 'list_transcripts' first if it exists? No, dir said 'list'
   # But wait, looking closer at Step 434 dir output:
   # ['__class__', ..., 'fetch', 'list']
   # The attribute name IS 'list'.
   
   print("Calling api.list(video_id)...")
   # Check signature of list first
   import inspect
   print(f"list method signature: {inspect.signature(api.list)}")
   
   transcript_list = api.list(video_id)
   transcript = next(iter(transcript_list))
   
   # Fetch the actual content
   print("Fetching data...")
   data = transcript.fetch()
   print(f"Data type: {type(data)}")
   
   if isinstance(data, list) and len(data) > 0:
       item = data[0]
       print(f"First item type: {type(item)}")
       print(f"First item dir: {dir(item)}")
       print(f"First item repr: {repr(item)}")
   else:
       print(f"Data repr: {repr(data)}")

except Exception as e:
    print(f"Instance pattern failed: {e}") 
