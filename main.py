from game import Game

def main():
    game = Game()
    print("Category :", game.category)

    # game runs here
    while True:

        for i in range(game.numPlayers):
            guess = input(f"Player {i + 1} please input your guess: ")
            res = game.submit_guess(guess)
            if res["status"] == "error":
                print(res["message"])
                while res["status"] == "error":
                    guess = input(f"Player {i + 1} please input your guess: ")
                    res = game.submit_guess(guess)
            else:
                print(res["message"])
        
        # all guesses are stored
        res = game.check_answers()
        print(f"{res["message"]} Round: {res["round"]}, Total Tries: {res["tries"]}")
        if res["status"] in ["success", "L"]:
            break
    

if __name__ == "__main__":
    main()
