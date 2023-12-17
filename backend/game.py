""" 
This script defines the Game class that contains almost all the gama integration top-level functions. 
All child classes should have these functions declared in this class as abstract methods.
"""

from abc import ABC, abstractmethod


class Game(ABC):
    """Parent class for all games."""

    def __init__(self, name):
        self.name = name

        # encodings for encoding fix and text integration
        self.original_encoding = None
        self.target_encoding = None

    @abstractmethod
    def prepare_raw_text(self):
        """
        This generalized function should provide a combination of operations that take the raw text from the game, save it to GameResources/RawText and prepare it for further processing.
        """
        pass

    @abstractmethod
    def integrate_from_text(self, text):
        """
        This generalized function should provide a combination of operations that take the text from the GameResources/Text folder and integrate it into the game.
        """
        pass
