""" define the Block class """


class Block:
    """ A block is a unit of text in a script file that controls the text that is shown at one time """

    # for translation
    is_translated = False
    content_translated = ""
    translation_date = ""

    # info variables
    is_narration = False
    def __init__(self, block_name, block_content):
        self.block_name = block_name
        self.block_content = block_content

    @classmethod
    def from_csv_line(cls, csv_line):
        """create a block instance from a csv line"""
        # check if csv_line is a list
        if not isinstance(csv_line, list):
            # if not, split it
            csv_line = csv_line.split(",")
        # check csv line length
        if len(csv_line) < 3:
            raise ValueError("CSV line length not correct")
        block_name = csv_line[0]
        block_content = csv_line[1]
        block = cls(block_name, block_content)

        block.content_translated = csv_line[2]
        block.is_translated = csv_line[3]
        block.is_narration = csv_line[4]
        block.translation_date = csv_line[5]
        return block


    def __str__(self):
        return f"Block {self.block_name} with {len(self.block_content)} lines"
