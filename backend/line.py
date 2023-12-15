""" This script defines the Line class. """

from datetime import datetime

def default_parser(raw_content):
    """ 
    Default parser for the line class. 
    Return a tuple of (
        content,
        speaker,
        line_number_in_block,
        speaker_line_number_in_block,
        start_end_position_in_raw_line,
        speaker_start_end_position_in_raw_line,
    )
    All other parsers defined in the Integrators should have the same return format.
    """
    return (raw_content, None, None, None)


class Line:
    """ 
    Line class stores the content and the information of a line of text in game. 
    In a game it should normaly displayed without break.
    A line class contains following attributes:
        - content: the content of the line
        - translated_content: the translated content of the line

        - speaker: the untranslated speaker of the line 
        - translated_speaker: the translated speaker of the line

        - line_number_in_file: the line number of the line in the file
        - file_name: the name of the file

        - line_number_in_block: the line number of the line in the block
        - speaker_line_number_in_block: the line number of the speaker in the block
        - block_name: the name of the block

        - start_end_position_in_raw_line: the start and end position of the line in the raw line
            This should be a tuple of two integers, this will be used to repalce the translated files 
        - speaker_start_end_position_in_raw_line: the start and end position of the speaker in the raw line

        - is_translated: Ture if the line is translated, False if not, 
            this bool could be used if the user is not satisfied with the translation 
            and want to mark it as not translated even if a translated_content is present

    """

    def __init__(
        self, 
    ):
        self.is_translated = False


    @classmethod
    def from_raw(cls, raw_content, parser=default_parser):
        """ Create a line object from raw content. """
        (cls.content, cls.speaker, cls.line_number_in_file, cls.line_number_in_block,) = parser(raw_content=raw_content)

        return cls

    @classmethod
    def from_csv_row(cls, csv_row):
        """ Create a line object from csv row. """
        pass


    def get_content(self):
        """ Return the content of the line. """
        return self.content

    def get_speaker(self):
        """ Return the speaker of the line. """
        return self.speaker

    def translate(self, translator=None):
        """ translating a single line without context is an unrecommended behavior """
        if translator != None:
            self.translated_content = translator.translate(self.content)
        else:
            self.translated_content = ""
        pass

    def get_translated_content(self):
        """ Return the translated content of the line. """
        return self.translated_content if 
