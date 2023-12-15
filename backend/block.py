# In block.py
class Block:
    def __init__(self, parent_file):
        self.parent_file = parent_file
        self.lines = []

    def add_line(self, line):
        self.lines.append(line)