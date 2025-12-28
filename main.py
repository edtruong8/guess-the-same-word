from game import Game

DEFAULT_CATEGORIES = ['Movies', 'Ice Cream Flavors', 'Animals', 'Celebrities']

def main():
    categories = DEFAULT_CATEGORIES.copy()
    # player inputting categories
    # while True:
    print("Do you want to use predefined categories only (Yes), custom categories only (No), " \
    "or both and add onto the predefined cateogries (Add)")
    temp = input("Input (Yes/No/Add)")
    while temp not in ["Yes", "No", "Add"]:
        temp = input("Please input either: Yes / No / Add")
    if temp == "No":
        # don't use categories.clear, because if we run another game, we lost the global
        categories = []

    if temp != "Yes":
        while True:
            category = input("Input a custom category you would like. When done, enter FINISHED")
            if category == "FINISHED":
                if len(categories) == 0:
                    print("Input at least one category.")
                    continue
                break
            if category in categories:
                print("Category already added.")
                continue
            categories.append(category)
            print(f"Current categories: {categories}")

    while True:
        try:
            tries = input("Input how many tries you want.")
            break
        except ValueError:
            print("Please input a valid integer")
    
    while True:
        try:
            numPlayers = input("Input number of players")
            break
        except ValueError:
            print("Please input a valid integer")

    game = Game(categories=categories, tries=tries, numPlayers=numPlayers)
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
            print(res["message"])
        
        # all guesses are stored
        res = game.check_answers()
        print(f'{res["message"]} Round: {res["round"]}, Total Tries: {res["tries"]}')
        if res["status"] in ["success", "L"]:
            break
    

if __name__ == "__main__":
    main()
