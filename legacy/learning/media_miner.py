
import os
import whisper
import tempfile

class MediaMiner:
    """
    Extracts knowledge from Audio/Video sources using OpenAI Whisper.
    """
    def __init__(self, model_size="base"):
        # sizes: tiny, base, small, medium, large
        self.model_size = model_size
        self.model = None

    def _load_model(self):
        if self.model is None:
            print(f"Loading Whisper Model ({self.model_size})...")
            self.model = whisper.load_model(self.model_size)

    def transcribe(self, file_path):
        """
        Transcribes the audio file at file_path.
        Returns the full text string.
        """
        if not os.path.exists(file_path):
            return ""
            
        try:
            self._load_model()
            # transcribe
            result = self.model.transcribe(file_path, fp16=False)
            return result.get("text", "")
        except Exception as e:
            print(f"Transcription Error: {e}")
            return f"[Error: {str(e)}]"
