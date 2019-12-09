class Keyboard(object):
    def __init__(self, keyboard):
        self.keyboard = list(keyboard)
        self.indexed = {note: idx for idx, note in enumerate(self.keyboard)}

    def get_index(self, note) -> int:
        """Returns the index of the note in the keyboard array"""
        return self.indexed[note]

    def calculate_transposition(self, noteset) -> int:
        """
        Calculates the transposition needed for the notes to fit on the keyboard
        Throws an exception if it can not fit the notes
        """
        notes = sorted(noteset)

        minimum = min(self.keyboard) - notes[0]
        maximum = max(self.keyboard) - notes[-1]

        transposition = 0
        while -transposition >= minimum or transposition <= maximum:
            for signedTransposition in [transposition, -transposition]:
                if self.__fits(notes, signedTransposition):
                    return signedTransposition
            transposition += 1
        raise RuntimeError(f"Cannot fit notes {notes} on keyboard {self.keyboard}")

    def __fits(self, notes, transposition):
        for note in notes:
            if not (note + transposition) in self.indexed:
                return False
        return True
