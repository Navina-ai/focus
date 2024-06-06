from .pyannote_embedding_spr import PyannoteEmbeddingSPR

class SPRFactory:
    """
    Factory for creating instances of VAD systems.
    """

    @staticmethod
    def create_spr_pipeline(type, **kwargs):
        """
        Creates a SPR pipeline based on the specified type.

        Args:
            type (str): The type of SPR pipeline to create (e.g., 'pyannote').
            kwargs: Additional arguments for the SPR pipeline creation.

        Returns:
            SPRInterface: An instance of a class that implements SPRInterface.
        """
        if type == "pyannote":
            return PyannoteEmbeddingSPR(**kwargs)
        else:
            raise ValueError(f"Unknown VAD pipeline type: {type}")
