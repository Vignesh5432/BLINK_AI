import pyttsx3
import threading
import queue

class TTSEngine:
    def __init__(self):
        self.queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        """
        Worker thread that initializes the engine once and processes the queue.
        """
        try:
            # Initialize engine inside the thread
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            
            while self.running:
                try:
                    text = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                if text is None: # Sentinel to stop
                    break
                
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"TTS Error during playback: {e}")
                
                self.queue.task_done()
                
        except Exception as e:
            print(f"TTS Initialization Error: {e}")

    def speak(self, text):
        """Add text to the speech queue."""
        if not text:
            return
        self.queue.put(text)

    def stop(self):
        """Stop the background thread."""
        self.running = False
        self.queue.put(None)
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
