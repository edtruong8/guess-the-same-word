from game import Game

DEFAULT_CATEGORIES = ['Movies', 'Ice Cream Flavors', 'Animals', 'Celebrities']

# returns yes no or add in string form
def get_category_setting():
    print("Do you want to use predefined categories only (Yes), custom categories only (No), " \
    "or both and add onto the predefined cateogries (Add)")
    setting = ""
    while setting not in ["Yes", "No", "Add"]:
        print("Please input either: Yes / No / Add")
        setting = input("Input (Yes/No/Add)")
    return setting


def get_custom_category():
    return input("Input a custom category you would like. When done, enter FINISHED")

def get_num_tries():
    while True:
        tries = input("Input how many tries you want.") 
        if tries.isdigit():
            return int(tries)
        print("Please input a valid integer")

def get_num_players():
    while True:
        numPlayers = input("Input number of players.")
        if numPlayers.isdigit():
            return int(numPlayers)
        print("Please input a valid integer")

def get_guess(player_id):
    return input(f"Player {player_id + 1} please input your guess.")

def main():

    categories = DEFAULT_CATEGORIES.copy()
    setting = get_category_setting()

    if setting == "No":
        categories.clear()

    else:
        while True:
            category = get_custom_category()
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

    tries = get_num_tries()
    numPlayers = get_num_players()

    game = Game(categories=categories, tries=tries, numPlayers=numPlayers)
    print("Category :", game.category)

    # game runs here
    while True:
        for i in range(game.numPlayers):
            guess = get_guess(i)
            res = game.submit_guess(guess)
            if res["status"] == "error":
                # either no guess or guess has been used already
                print(res["message"])
                while res["status"] == "error":
                    guess = get_guess(i)
                    res = game.submit_guess(guess)
            # okay confirmation
            print(res["message"])
        
        # all guesses are stored
        res = game.check_answers()
        print(f'{res["message"]} Round: {res["round"]}, Total Tries: {res["tries"]}')
        if res["status"] in ["success", "L"]:
            break
    

if __name__ == "__main__":
    main()
