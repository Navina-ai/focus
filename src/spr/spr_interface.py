from pyannote.audio.core.model import Model
class SPRInterface:
    """
    Interface for speaker recognition (SPR) systems.
    """

    def classify_speaker(self, client_id, audio_data):
        """
        classify the speaker in the given audio data.
        Assuming a single speaker in the audio data.

        Args:
            client (str): The client id to classify on
            audio_data (nparray): The data to classify

        Returns:
            int: SPR result,  a unique identifier for the speaker
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    @property
    def model(self) -> Model:
        """
        The model used for speaker recognition.

        Returns:
            Any: The model used for speaker recognition
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
