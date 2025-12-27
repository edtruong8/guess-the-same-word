"""
Two-player game (will extend to multiplayer) where a category is selected and players have to come up 
with the same word. 5 tries (will be able to select how many) to get the same word.
"""

from random import choice

# TODO: let users submit their own categories in addition to this
categories = ['Movies', 'Ice Cream Flavors', 'Animals', 'Celebrities']

class Game:

    # Functions will be returning dictionaries, will make it easier to see state
    # status - 'error', 'continue', 'success', 'L'

    def __init__(self, tries=5, numPlayers=2):
        self.category = choice(categories)
        self.guesses = []
        self.usedWords = set()
        self.tries = tries
        self.round = 0
        self.numPlayers = numPlayers
    
    def submit_guess(self, guessWord):
        guess = guessWord.strip().lower()
        if not guess:
            return {"status" : "error", "message" : "Please input a guess."}
        if guess in self.usedWords:
            return {"status" : "error", "message" : "Word has been used by a player already, input another guess."}
        self.guesses.append(guess)
        return {"status" : "continue", "message" : "Thank you for inputting your guess."}

    # def is_over(self):
    #     return self.round >= self.tries

    # will return dictionary with game state, when game is initalized it will know when to stop
    def check_answers(self):
        if len(self.guesses) != self.numPlayers:
            return {"status" : "error", "message" : "All players need to input a guess."}
        
        if len(set(self.guesses)) == 1:
            return {"status" : "success", "message" : "Congrats! Everybody got the same word.",
                    "round" : self.round, "tries" : self.tries}

        if self.round >= self.tries:
            return {"status" : "L", "message" : "Players were not able to guess the same word."}
        
        self.round += 1

        for word in self.guesses:
            self.usedWords.add(word)

        self.guesses = []

        return {"status" : "continue", "message" : "Not all guesses were the same. Onto the next round!",
                "round" : self.round, "tries" : self.tries}
