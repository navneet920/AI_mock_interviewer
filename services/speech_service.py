import asyncio
import edge_tts
import pygame
import os


class TextToSpeech:

    def __init__(
        self,
        voice="en-US-JennyNeural"
    ):
        self.voice = voice
        pygame.mixer.init()

    async def _generate_audio(
        self,
        text: str,
        output_file: str = "temp_voice.mp3"
    ):
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice
        )

        await communicate.save(output_file)

        return output_file

    def speak(self, text: str):

        output_file = "temp_voice.mp3"

        asyncio.run(
            self._generate_audio(
                text=text,
                output_file=output_file
            )
        )

        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()

        if os.path.exists(output_file):
            os.remove(output_file)

# if __name__=="__main__":
#     tts = TextToSpeech()
#
#     tts.speak(
#         "Hello Navneet. Welcome to your AI Mock Interview."
#     )