from time import sleep
from dataclasses import asdict
from random import random

from duel_game.core.essential_types import GameState, Action

class OldPresenter:
    @staticmethod
    def intro():
        print('Welcome to Duel Game')


    @staticmethod
    def insert_margin(func):
        """
        insert one empty before and after a method operates and print something
        """
        def new_func(*args, **kwargs):
            print()
            result = func(*args, **kwargs)
            print()
            return result

        return new_func
    

    @staticmethod
    @insert_margin
    def main_menu() -> str:
        """
        displays the main menu to the user and let him choose an option
        then return the selected option as a numeric string
        """

        print(20 * "-")
        print('MAIN MENU')
        print()
        print('1. Play New Game')
        print('2. How to Play')
        print('3. Exit')
        print(20 * "-")

        print()

        while True:
            try:
                sleep(1)
                print()
                choice = int(input('what is your choice?\t').strip())
                if choice not in [1, 2, 3]:
                    raise ValueError
                return str(choice)

            except ValueError:
                print()
                print('Invalid Choice')
                continue

    @staticmethod
    @insert_margin
    def display_help():
        print("=" * 70)
        print("HOW TO PLAY — DUEL GAME")
        print("=" * 70)
        print()
        
        print("ABOUT THE GAME")
        print("-" * 70)
        print("This is a turn-based 1v1 duel between You and an AI opponent.")
        print("Your goal is simple: reduce the opponent's Health to 0 before yours reaches 0.")
        print("Every turn, both players secretly choose one action.")
        print("Then the actions resolve simultaneously.")
        print()

        print("CORE RESOURCES")
        print("-" * 70)
        print("• Health: Starts at 100. If it reaches 0, you lose.")
        print("• Stamina: Starts at 100. Used to perform actions.")
        print("• At the end of every turn, BOTH players regain +30 stamina.")
        print("• Maximum Health and Stamina are capped at 100.")
        print()

        print("AVAILABLE ACTIONS")
        print("-" * 70)

        print("1. ATTACK  (Cost: 50 Stamina)")
        print("   - Deals 20 damage if not defended or dodged.")
        print("   - High impact, but expensive.")
        print()

        print("2. DEFENSE (Cost: 0 Stamina)")
        print("   - Requires a Shield.")
        print("   - Shield becomes available every 5 turns.")
        print("   - Blocks incoming attack damage completely.")
        print("   - Cannot be used if Shield is on cooldown.")
        print()

        print("3. DODGE   (Cost: 10 Stamina)")
        print("   - 50% chance to completely avoid an incoming attack.")
        print("   - Cheap and risky.")
        print()

        print("4. HEAL    (Cost: 60 Stamina)")
        print("   - Restores 20 Health.")
        print("   - Cannot exceed 100 Health.")
        print("   - Very powerful but extremely costly.")
        print()

        print("5. DO NOTHING (Cost: 0 Stamina)")
        print("   - You skip your action.")
        print("   - Useful for saving stamina.")
        print("   - If both of you does not have enough stamina to attack,")
        print("     doing nothing is often the smartest move.")
        print()

        print("IMPORTANT STRATEGY NOTES")
        print("-" * 70)
        print("• You cannot spam Attack — stamina limits you.")
        print("• You cannot spam Heal — it is expensive.")
        print("• Defense depends on Shield timing.")
        print("• Managing stamina is often more important than raw aggression.")
        print("• Sometimes waiting is stronger than attacking.")
        print()

        print("WIN CONDITION")
        print("-" * 70)
        print("Reduce the opponent's Health to 0 to win.")
        print("If your Health reaches 0 first, you lose.")
        print()

        print("=" * 70)
        print("Tip: Watch stamina carefully. The duel is not about who attacks more —")
        print("it is about who chooses the right moment.")
        print("=" * 70)

        input("\nPress Enter to return to the main menu...")

        

    @staticmethod
    def on_game_starts():
        print('so Get Ready, DUEL is About to Begin...')
        sleep(2)


    @staticmethod
    @insert_margin
    def on_turn_start(game_state: GameState) -> Action:
        print(f'Turn {game_state.turn}')
        print()

        print(60 * '-')
        print((20 * ' ') + f'{"You":<17} {"AI":<20}')
        print()

        player_1 = game_state.player_1
        player_2 = game_state.player_2

        print(f'{'Health':<20} {str(player_1.health):<15} {str(player_2.health):<15}')
        print(f'{'Stamina':<20} {str(player_1.stamina):<15} {str(player_2.stamina):<15}')
        print(f'{'Has Shield':<20} {("Yes" if player_1.is_shield_available else "No"):<15} {("Yes" if player_2.is_shield_available else "No"):<15}')
        print(60 * '-')

        is_attack_feasible = player_1.stamina >= Action.ATTACK.stamina_cost()
        is_heal_feasible = player_1.stamina >= Action.HEAL.stamina_cost() and player_1.health < 100
        is_defense_feasible = player_1.is_shield_available
        action_feasibility = {
            1: {'feasibility': is_attack_feasible, 'reason': f'Stamina < {str(Action.ATTACK.stamina_cost())}'}, 
            2: {'feasibility': is_defense_feasible, 'reason': f'Shield not Available, {player_1.shield_cd} Turns Remained'},
            3: {'feasibility': True},
            4: {'feasibility': is_heal_feasible, 'reason': f'Stamina < {str(Action.HEAL.stamina_cost())}' if player_1.stamina < Action.HEAL.stamina_cost() else \
              "Health is full" if player_1.health == 100 else ""},
            5: {'feasibility': True}
        }

        print()
        print('Actions:')
        print('1. Attack ' + (f'(not Feasible because {action_feasibility[1]['reason']})' if not is_attack_feasible else ""))
        print('2. Defense ' + (f'(not Feasible because {action_feasibility[2]['reason']})' if not is_defense_feasible else ""))
        print('3. Dodge')
        print('4. Heal ' + (f"(not Feasible because {action_feasibility[4]['reason']})" if not is_heal_feasible else ""))
        print('5. Do Nothing!')

        while True:
            try:
                print()
                action = int(input('What is your Action?\t').strip())
                if action not in [1,2,3,4,5]:
                    raise ValueError
                if not action_feasibility[action]['feasibility']:
                    print(f'chosen Action is not Feasible because {action_feasibility[action]['reason']}')
                    continue
                return Action(action)

            except ValueError:
                print()
                print('Invalid Option!')
                continue

    @staticmethod
    @insert_margin
    def after_player_decision(player_action):
        if player_action == Action.ATTACK:
            print('You commit to an aggressive strike, preparing to deal direct damage.')
        elif player_action == Action.DEFENSE:
            print('You raise your guard, focusing on reducing incoming damage.')
        elif player_action == Action.HEAL:
            print('You concentrate briefly, attempting to recover lost health.')
        elif player_action == Action.DODGE:
            print("You shift your stance, ready to evade the opponent's next move.")
        else:
            print('wow, Nothing!\nEither you are very confident that your opponent will not attack or you are really hesitate about what Action to take.')

        print()
        print('wait for Opponent to Take his Action too...')
        sleep(2 + random())

    @staticmethod
    def after_decisions(player_action, ai_action, player_result_detail, ai_result_detail):
        print()

        static_detail = f"Your action: {player_action.name} | Opponent action: {ai_action.name if ai_action else 'None'}\n"

        # ---------------- ATTACK ----------------
        if player_action == Action.ATTACK and ai_action == Action.ATTACK:
            print(static_detail + "Steel meets steel! You both strike at the same time — both take 20 damage.")

        elif player_action == Action.ATTACK and ai_action == Action.DEFENSE:
            print(static_detail + "You swing boldly, but the opponent stands firm. Your strike finds no opening.")

        elif player_action == Action.ATTACK and ai_action == Action.HEAL:
            print(static_detail + "You attack while the opponent tries to recover. A risky move… and you make them pay.")

        elif player_action == Action.ATTACK and ai_action == Action.DODGE:
            if ai_result_detail['is_dodge_works']:
                print(static_detail + "You strike fast — but the opponent slips away just in time. Clean escape.")
            else:
                print(static_detail + "The opponent tries to dodge… not fast enough. Your blade lands true.")

        elif player_action == Action.ATTACK and ai_action == Action.NONE:
            print(static_detail + "You attack. No answer from the other side. That must hurt.")

        # ---------------- DEFENSE ----------------
        elif player_action == Action.DEFENSE and ai_action == Action.ATTACK:
            print(static_detail + "You brace yourself. The opponent attacks — but you are ready for it.")

        elif player_action == Action.DEFENSE and ai_action == Action.DEFENSE:
            print(static_detail + "Both of you hold your ground. A quiet moment… but tension grows.")

        elif player_action == Action.DEFENSE and ai_action == Action.HEAL:
            print(static_detail + "You defend calmly while the opponent gathers strength. A careful turn.")

        elif player_action == Action.DEFENSE and ai_action == Action.DODGE:
            print(static_detail + "You stay guarded. The opponent moves lightly, watching for a chance.")

        elif player_action == Action.DEFENSE and ai_action == Action.NONE:
            print(static_detail + "You defend. Silence from the other side… interesting.")

        # ---------------- HEAL ----------------
        elif player_action == Action.HEAL and ai_action == Action.ATTACK:
            print(static_detail + "You try to recover — but the opponent attacks! Healing under pressure… bold choice.")

        elif player_action == Action.HEAL and ai_action == Action.DEFENSE:
            print(static_detail + "You regain strength while the opponent stands guarded. A steady recovery.")

        elif player_action == Action.HEAL and ai_action == Action.HEAL:
            print(static_detail + "Both of you step back and recover. A short pause before the storm.")

        elif player_action == Action.HEAL and ai_action == Action.DODGE:
            print(static_detail + "You heal. The opponent keeps moving, cautious and light on their feet.")

        elif player_action == Action.HEAL and ai_action == Action.NONE:
            print(static_detail + "You take the moment to heal. No one stops you.")

        # ---------------- DODGE ----------------
        elif player_action == Action.DODGE and ai_action == Action.ATTACK:
            if player_result_detail['is_dodge_works']:
                print(static_detail + "The opponent attacks — but you vanish from harm. Nicely done.")
            else:
                print(static_detail + "You try to dodge… but the strike catches you. That one stings.")

        elif player_action == Action.DODGE and ai_action == Action.DEFENSE:
            print(static_detail + "You move swiftly while the opponent stands firm. Testing each other.")

        elif player_action == Action.DODGE and ai_action == Action.HEAL:
            print(static_detail + "You keep moving. The opponent uses the moment to recover.")

        elif player_action == Action.DODGE and ai_action == Action.DODGE:
            print(static_detail + "Both of you dance around the arena. No hits — just footwork.")

        elif player_action == Action.DODGE and ai_action == Action.NONE:
            print(static_detail + "You dodge lightly. No threat comes your way.")

        # ---------------- PLAYER NONE ----------------
        elif player_action == Action.NONE and ai_action == Action.ATTACK:
            print(static_detail + "The opponent attacks without hesitation. You stand still — not your best idea.")

        elif player_action == Action.NONE and ai_action == Action.DEFENSE:
            print(static_detail + "The opponent defends patiently. Waiting… perhaps for you to move.")

        elif player_action == Action.NONE and ai_action == Action.HEAL:
            print(static_detail + "The opponent restores their strength. You let them.")

        elif player_action == Action.NONE and ai_action == Action.DODGE:
            print(static_detail + "The opponent moves lightly, watching you closely.")
        elif player_action == Action.NONE and ai_action == Action.NONE:
            print(static_detail + "Both of you pause cautiously, neither willing to make the first move this turn.")


    @staticmethod
    def after_turn(sheild_count_down: int, whether_game_ends: bool, player_wins: bool):
        print()

        if whether_game_ends == True:
            if player_wins == True:
                print(80 * '-')
                print('You delivered the final blow — the opponent falls, and victory is yours.')
                print(80 * '-')
            elif player_wins == False: 
                print(80 * '-')
                print('The opponent overwhelms you with a decisive strike — you have been defeated.')
                print(80 * '-')
            else:
                raise ValueError('unexpected player_wins value provided ', str(player_wins))
            print('Was a Good Game, GG...')
        elif whether_game_ends == False:
            sleep(2)
            print('Next turn is about to begin. Both Players Stamina will Increase by 30')
            if sheild_count_down > 1:
                print(f'Shield will become available in {sheild_count_down} Turns')
            elif sheild_count_down == 1:
                print('Shield will be Available Now')
            print('Press Enter when you are ready.')
            input()
        else:
            raise ValueError('unexpected whether_game_ends value provided ', str(whether_game_ends))

        
class Presenter:
    def __init__(self, language='en'):
        self.lang = language

    def intro(self):
        if self.lang == 'fa':
            print('Be baazi duel khosh aamadid')
        else:
            print('Welcome to Duel Game')

    def insert_margin(func):
        """
        insert one empty before and after a method operates and print something
        """
        def new_func(*args, **kwargs):
            print()
            result = func(*args, **kwargs)
            print()
            return result

        return new_func
    
    
    @insert_margin
    def main_menu(self) -> str:
        """
        displays the main menu to the user and let him choose an option
        then return the selected option as a numeric string
        """

        print(20 * "-")
        if self.lang == 'fa':
            print('Menoo-ye asli')
        else:
            print('MAIN MENU')
        print()
        
        if self.lang == 'fa':
            print('1. Shoroo-e baazi jadid')
            print('2. Rahanamaye Bazi')
            print('3. Taghir zaboon')
            print('4. Khorooj')
        else:
            print('1. Play New Game')
            print('2. How to Play')
            print('3. Change Language')
            print('4. Exit')
        print(20 * "-")

        print()

        while True:
            try:
                sleep(1)
                print()
                if self.lang == 'fa':
                    choice = int(input('Entekhab-e shoma chist?\t').strip())
                else:
                    choice = int(input('what is your choice?\t').strip())
                if choice not in [1, 2, 3, 4]:
                    raise ValueError
                return str(choice)

            except ValueError:
                print()
                if self.lang == 'fa':
                    print('Entekhab-e naamotabar')
                else:
                    print('Invalid Choice')
                continue

    @insert_margin
    def change_language(self):
        """
        Display language selection menu and let the user choose between Farsi and English.
        Updates self.lang attribute and returns the selected language code.
        """
        print(20 * "-")
        if hasattr(self, 'lang') and self.lang == 'fa':
            print("Entekhab zaboon")
        else:
            print("LANGUAGE SELECTION")
        print(20 * "-")
        print()
        print("1. English")
        print("2. Finglish (Farsi with English Characters)")
        print(20 * "-")
        print()
        
        while True:
            try:
                sleep(1)
                print()
                if hasattr(self, 'lang') and self.lang == 'fa':
                    choice = input('Zaboon-e khod ra entekhab konid:\t').strip()
                else:
                    choice = input('Select your language:\t').strip()
                
                if choice == '1' or choice.lower() in ['1', 'en', 'english']:
                    self.lang = 'en'
                    print()
                    print("Language set to English")
                    return 'en'
                    
                elif choice == '2' or choice.lower() in ['2', 'fa', 'farsi', 'persian']:
                    self.lang = 'fa'
                    print()
                    print("Zaboon be Farsi tanzim shod")
                    return 'fa'
                    
                else:
                    raise ValueError
                    
            except ValueError:
                print()
                if hasattr(self, 'lang') and self.lang == 'fa':
                    print("Entekhab-e naamotabar")
                    print("Lotfan 1 baraye English ya 2 baraye Farsi ra vared konid")
                else:
                    print("Invalid choice")
                    print("Please enter 1 for English or 2 for Persian")
                continue

    @insert_margin
    def display_help(self):
        if self.lang == 'fa':
            print("=" * 70)
            print("Nahoeye baazi — Duel")
            print("=" * 70)
            print()
            
            print("Darbareye baazi")
            print("-" * 70)
            print("In yek duel-e nobati yek be yek bein-e shoma va harif-e hoosh-e masnooee ast.")
            print("Hadaf-e shoma sade ast: salaamat-e harif ra ghabl az inke salaamat-e shoma be sefr beresad, be sefr beresoonid.")
            print("Har nobat, har do baazikon makhfian yek amal ra entekhab mikonand.")
            print("Sepas a'amaal be toor-e hamzaman ejra mishavand.")
            print()

            print("Manabe-e asli")
            print("-" * 70)
            print("• Salaamat: Az 100 shoroo mishavad. Agar be sefr beresad, mibaazid.")
            print("• Esteghaamat: Az 100 shoroo mishavad. Baraye anjaam-e a'amaal estefade mishavad.")
            print("• Dar payan-e har nobat, har do baazikon 20 esteghaamat bazyabi mikonand.")
            print("• Haddaksar-e salaamat va esteghaamat 100 ast.")
            print()

            print("A'amaal-e mojood")
            print("-" * 70)

            print("1. Hamleh (Hazineh: 50 esteghaamat)")
            print("   - Agar defaa ya faraar nashavad, 20 aasib vared mikonad.")
            print("   - Ta'sir-e baala, amaa por-hazineh.")
            print()

            print("2. Defaa (Hazineh: 0 esteghaamat)")
            print("   - Niaaz be separ darad.")
            print("   - Separ har 5 nobat yekbaar dar dastres mishavad.")
            print("   - Aasib-e hamleh-ye voroodi ra kaamela masdood mikonad.")
            print("   - Agar separ dar haalat-e aamade-baash nabashad, ghabele estefade nist.")
            print()

            print("3. Faraar (Hazineh: 10 esteghaamat)")
            print("   - 50% shaans baraye jelogiri-ye kaamel az hamleh-ye voroodi.")
            print("   - Arzaan va reeski.")
            print()

            print("4. Darman (Hazineh: 60 esteghaamat)")
            print("   - 20 salaamat ra baazyabi mikonad.")
            print("   - Nemitavanad az 100 salaamat bishtar shavad.")
            print("   - Besyaar ghodratmand amaa besyaar por-hazineh.")
            print()

            print("5. Hich kari nakon (Hazineh: 0 esteghaamat)")
            print("   - Nobat-e khod ra migozarid.")
            print("   - Mofid baraye zakhireh-ye esteghaamat.")
            print("   - Agar har do esteghaamat-e kaafi baraye hamleh nadashteh baashand,")
            print("     anjaam nadadan-e kar aghlan hoomandaneh-tarin harekat ast.")
            print()

            print("Nokaat-e mohem-e esteratezhi")
            print("-" * 70)
            print("• Nemitavanid hamleh ra espam konid — esteghaamat shoma ra mahdud mikonad.")
            print("• Nemitavanid darman ra espam konid — por-hazineh ast.")
            print("• Defaa be zamoonbandi-ye separ bastegi darad.")
            print("• Modiriyyat-e esteghaamat aghlan mohemtar az por-khashgari-ye khaam ast.")
            print("• Gahi sabr kardan ghavitar az hamleh kardan ast.")
            print()

            print("Sharaayet-e piroozi")
            print("-" * 70)
            print("Salaamat-e harif ra be sefr beresoonid ta pirooz shavid.")
            print("Agar salaamat-e shoma zoodtar be sefr beresad, mibaazid.")
            print()

            print("=" * 70)
            print("Nokteh: Moraqeb-e esteghaamat baashid. Duel dar mored-e kasi nist ke bishtar hamleh mikonad —")
            print("dar mored-e kasi ast ke lahzeh-ye mounaseb ra entekhab mikonad.")
            print("=" * 70)
        else:
            print("=" * 70)
            print("HOW TO PLAY — DUEL GAME")
            print("=" * 70)
            print()
            
            print("ABOUT THE GAME")
            print("-" * 70)
            print("This is a turn-based 1v1 duel between You and an AI opponent.")
            print("Your goal is simple: reduce the opponent's Health to 0 before yours reaches 0.")
            print("Every turn, both players secretly choose one action.")
            print("Then the actions resolve simultaneously.")
            print()

            print("CORE RESOURCES")
            print("-" * 70)
            print("• Health: Starts at 100. If it reaches 0, you lose.")
            print("• Stamina: Starts at 100. Used to perform actions.")
            print("• At the end of every turn, BOTH players regain +30 stamina.")
            print("• Maximum Health and Stamina are capped at 100.")
            print()

            print("AVAILABLE ACTIONS")
            print("-" * 70)

            print("1. ATTACK  (Cost: 50 Stamina)")
            print("   - Deals 20 damage if not defended or dodged.")
            print("   - High impact, but expensive.")
            print()

            print("2. DEFENSE (Cost: 0 Stamina)")
            print("   - Requires a Shield.")
            print("   - Shield becomes available every 5 turns.")
            print("   - Blocks incoming attack damage completely.")
            print("   - Cannot be used if Shield is on cooldown.")
            print()

            print("3. DODGE   (Cost: 10 Stamina)")
            print("   - 50% chance to completely avoid an incoming attack.")
            print("   - Cheap and risky.")
            print()

            print("4. HEAL    (Cost: 60 Stamina)")
            print("   - Restores 20 Health.")
            print("   - Cannot exceed 100 Health.")
            print("   - Very powerful but extremely costly.")
            print()

            print("5. DO NOTHING (Cost: 0 Stamina)")
            print("   - You skip your action.")
            print("   - Useful for saving stamina.")
            print("   - If both of you does not have enough stamina to attack,")
            print("     doing nothing is often the smartest move.")
            print()

            print("IMPORTANT STRATEGY NOTES")
            print("-" * 70)
            print("• You cannot spam Attack — stamina limits you.")
            print("• You cannot spam Heal — it is expensive.")
            print("• Defense depends on Shield timing.")
            print("• Managing stamina is often more important than raw aggression.")
            print("• Sometimes waiting is stronger than attacking.")
            print()

            print("WIN CONDITION")
            print("-" * 70)
            print("Reduce the opponent's Health to 0 to win.")
            print("If your Health reaches 0 first, you lose.")
            print()

            print("=" * 70)
            print("Tip: Watch stamina carefully. The duel is not about who attacks more —")
            print("it is about who chooses the right moment.")
            print("=" * 70)

        if self.lang == 'fa':
            input("\nEnter ra bezanid ta be menoo-ye asli baazgardid...")
        else:
            input("\nPress Enter to return to the main menu...")

    def on_game_starts(self):
        if self.lang == 'fa':
            print('Aamadeh shavid, duel dar sharof-e shoroo ast...')
        else:
            print('so Get Ready, DUEL is About to Begin...')
        sleep(2)

    @insert_margin
    def on_turn_start(self, game_state: GameState) -> Action:
        if self.lang == 'fa':
            print(f'Nobat {game_state.turn}')
        else:
            print(f'Turn {game_state.turn}')
        print()

        print(60 * '-')
        if self.lang == 'fa':
            print((20 * ' ') + f'{"Shoma":<17} {"Hoosh-e masnooee":<20}')
        else:
            print((20 * ' ') + f'{"You":<17} {"AI":<20}')
        print()

        player_1 = game_state.player_1
        player_2 = game_state.player_2

        if self.lang == 'fa':
            print(f'{"Salaamat":<20} {str(player_1.health):<15} {str(player_2.health):<15}')
            print(f'{"Esteghaamat":<20} {str(player_1.stamina):<15} {str(player_2.stamina):<15}')
            print(f'{"Daaraye separ":<20} {("Bale" if player_1.is_shield_available else "Kheyr"):<15} {("Bale" if player_2.is_shield_available else "Kheyr"):<15}')
        else:
            print(f'{'Health':<20} {str(player_1.health):<15} {str(player_2.health):<15}')
            print(f'{'Stamina':<20} {str(player_1.stamina):<15} {str(player_2.stamina):<15}')
            print(f'{'Has Shield':<20} {("Yes" if player_1.is_shield_available else "No"):<15} {("Yes" if player_2.is_shield_available else "No"):<15}')
        print(60 * '-')

        is_attack_feasible = player_1.stamina >= Action.ATTACK.stamina_cost()
        is_heal_feasible = player_1.stamina >= Action.HEAL.stamina_cost() and player_1.health < 100
        is_defense_feasible = player_1.is_shield_available
        action_feasibility = {
            1: {'feasibility': is_attack_feasible, 'reason': f'Stamina < {str(Action.ATTACK.stamina_cost())}' if self.lang != 'fa' else f'Esteghaamat < {str(Action.ATTACK.stamina_cost())}'}, 
            2: {'feasibility': is_defense_feasible, 'reason': f'Shield not Available, {player_1.shield_cd} Turns Remained' if self.lang != 'fa' else f'Separ dar dastres nist, {player_1.shield_cd} nobat baagimaandeh'},
            3: {'feasibility': True},
            4: {'feasibility': is_heal_feasible, 'reason': f'Stamina < {str(Action.HEAL.stamina_cost())}' if player_1.stamina < Action.HEAL.stamina_cost() else \
              "Health is full" if player_1.health == 100 else "" if self.lang != 'fa' else \
              f'Esteghaamat < {str(Action.HEAL.stamina_cost())}' if player_1.stamina < Action.HEAL.stamina_cost() else \
              "Salaamat kaamel ast" if player_1.health == 100 else ""},
            5: {'feasibility': True}
        }

        print()
        if self.lang == 'fa':
            print('Aamaal:')
        else:
            print('Actions:')
        
        if self.lang == 'fa':
            print('1. Hamleh ' + (f'(emkan pazir nist choon {action_feasibility[1]["reason"]})' if not is_attack_feasible else ""))
            print('2. Defaa ' + (f'(emkan pazir nist choon {action_feasibility[2]["reason"]})' if not is_defense_feasible else ""))
            print('3. Faraar')
            print('4. Darman ' + (f"(emkan pazir nist choon {action_feasibility[4]['reason']})" if not is_heal_feasible else ""))
            print('5. Hich kari nakon!')
        else:
            print('1. Attack ' + (f'(not Feasible because {action_feasibility[1]["reason"]})' if not is_attack_feasible else ""))
            print('2. Defense ' + (f'(not Feasible because {action_feasibility[2]["reason"]})' if not is_defense_feasible else ""))
            print('3. Dodge')
            print('4. Heal ' + (f"(not Feasible because {action_feasibility[4]['reason']})" if not is_heal_feasible else ""))
            print('5. Do Nothing!')

        while True:
            try:
                print()
                if self.lang == 'fa':
                    action = int(input('Amal-e shoma chist?\t').strip())
                else:
                    action = int(input('What is your Action?\t').strip())
                if action not in [1,2,3,4,5]:
                    raise ValueError
                if not action_feasibility[action]['feasibility']:
                    if self.lang == 'fa':
                        print(f'Amal-e entekhab shodeh emkan pazir nist choon {action_feasibility[action]["reason"]}')
                    else:
                        print(f'chosen Action is not Feasible because {action_feasibility[action]["reason"]}')
                    continue
                return Action(action)

            except ValueError:
                print()
                if self.lang == 'fa':
                    print('Gozineh naamotabar!')
                else:
                    print('Invalid Option!')
                continue

    @insert_margin
    def after_player_decision(self, player_action):
        if player_action == Action.ATTACK:
            if self.lang == 'fa':
                print('Shoma baraye yek zarbeye tahajomi motahed mishavid, aamade vared kardan aasib-e mostaghim.')
            else:
                print('You commit to an aggressive strike, preparing to deal direct damage.')
        elif player_action == Action.DEFENSE:
            if self.lang == 'fa':
                print('Shoma negahbani-ye khod ra baala mibarid, tamarkoz bar kahesh-e aasib-e voroodi.')
            else:
                print('You raise your guard, focusing on reducing incoming damage.')
        elif player_action == Action.HEAL:
            if self.lang == 'fa':
                print('Shoma be toor-e mokhtasar tamarkoz mikonid, talash baraye baazyabi-e salaamat-e az dast rafteh.')
            else:
                print('You concentrate briefly, attempting to recover lost health.')
        elif player_action == Action.DODGE:
            if self.lang == 'fa':
                print('Shoma vaziyyat-e khod ra taghir midahid, aamade baraye faraar az harekat-e baadi-ye harif.')
            else:
                print("You shift your stance, ready to evade the opponent's next move.")
        else:
            if self.lang == 'fa':
                print('Vaay, hichi!\nYa kheili motmaeenid ke harif hamleh nemikonad ya vaghean dar mored-e inke che amali anjam dahid mardod hastid.')
            else:
                print('wow, Nothing!\nEither you are very confident that your opponent will not attack or you are really hesitate about what Action to take.')

        print()
        if self.lang == 'fa':
            print('Montazer bemoonid ta harif ham amal-e khod ra anjaam dahad...')
        else:
            print('wait for Opponent to Take his Action too...')
        sleep(2 + random())

    def after_decisions(self, player_action, ai_action, player_result_detail, ai_result_detail):
        print()

        if self.lang == 'fa':
            static_detail = f"Amal-e shoma: {player_action.name} | Amal-e harif: {ai_action.name if ai_action else 'Hich'}\n"
        else:
            static_detail = f"Your action: {player_action.name} | Opponent action: {ai_action.name if ai_action else 'None'}\n"

        # ---------------- ATTACK ----------------
        if player_action == Action.ATTACK and ai_action == Action.ATTACK:
            if self.lang == 'fa':
                print(static_detail + "Foolad be foolad! Har do hamzaman zarbe mizanid — har do 20 aasib mibinid.")
            else:
                print(static_detail + "Steel meets steel! You both strike at the same time — both take 20 damage.")

        elif player_action == Action.ATTACK and ai_action == Action.DEFENSE:
            if self.lang == 'fa':
                print(static_detail + "Shoma jasooreh zarbe mizanid, amma harif mohkam miistad. Zarbe shoma raahi peyda nemikonad.")
            else:
                print(static_detail + "You swing boldly, but the opponent stands firm. Your strike finds no opening.")

        elif player_action == Action.ATTACK and ai_action == Action.HEAL:
            if self.lang == 'fa':
                print(static_detail + "Shoma hamleh mikonid dar hali ke harif talash mikonad behbood yabad. Yek harekat-e por-reesk... va shoma oo ra vadar be pardakht-e hazineh mikonid.")
            else:
                print(static_detail + "You attack while the opponent tries to recover. A risky move… and you make them pay.")

        elif player_action == Action.ATTACK and ai_action == Action.DODGE:
            if ai_result_detail['is_dodge_works']:
                if self.lang == 'fa':
                    print(static_detail + "Shoma sari zarbe mizanid — amma harif be mooghe migrizad. Faraar-e tamiz.")
                else:
                    print(static_detail + "You strike fast — but the opponent slips away just in time. Clean escape.")
            else:
                if self.lang == 'fa':
                    print(static_detail + "Harif talash mikonad faraar konad... be andazeh kaafi sari nist. Tighe shoma be hadaf mikhord.")
                else:
                    print(static_detail + "The opponent tries to dodge… not fast enough. Your blade lands true.")

        elif player_action == Action.ATTACK and ai_action == Action.NONE:
            if self.lang == 'fa':
                print(static_detail + "Shoma hamleh mikonid. Pasokhi az taraf-e digar nist. Baayad dardnaak baashad.")
            else:
                print(static_detail + "You attack. No answer from the other side. That must hurt.")

        # ---------------- DEFENSE ----------------
        elif player_action == Action.DEFENSE and ai_action == Action.ATTACK:
            if self.lang == 'fa':
                print(static_detail + "Shoma khod ra aamade mikonid. Harif hamleh mikonad — amma shoma baraye aan aamade hastid.")
            else:
                print(static_detail + "You brace yourself. The opponent attacks — but you are ready for it.")

        elif player_action == Action.DEFENSE and ai_action == Action.DEFENSE:
            if self.lang == 'fa':
                print(static_detail + "Har doye shoma moze-e khod ra hefz mikonid. Yek lahzeh-ye aaram... amma tanaffoz afzaayesh miyabad.")
            else:
                print(static_detail + "Both of you hold your ground. A quiet moment… but tension grows.")

        elif player_action == Action.DEFENSE and ai_action == Action.HEAL:
            if self.lang == 'fa':
                print(static_detail + "Shoma aaram defaa mikonid dar hali ke harif ghodrat jam mikonad. Yek nobat-e mohtaataneh.")
            else:
                print(static_detail + "You defend calmly while the opponent gathers strength. A careful turn.")

        elif player_action == Action.DEFENSE and ai_action == Action.DODGE:
            if self.lang == 'fa':
                print(static_detail + "Shoma mohaafezekaar mimanid. Harif sabok harekat mikonad, montazer-e yek forsat.")
            else:
                print(static_detail + "You stay guarded. The opponent moves lightly, watching for a chance.")

        elif player_action == Action.DEFENSE and ai_action == Action.NONE:
            if self.lang == 'fa':
                print(static_detail + "Shoma defaa mikonid. Sokoot az taraf-e digar... jaaleb ast.")
            else:
                print(static_detail + "You defend. Silence from the other side… interesting.")

        # ---------------- HEAL ----------------
        elif player_action == Action.HEAL and ai_action == Action.ATTACK:
            if self.lang == 'fa':
                print(static_detail + "Shoma talash mikonid behbood yabid — amma harif hamleh mikonad! Darman taht-e feshaar... entekhab-e shojaaaneh.")
            else:
                print(static_detail + "You try to recover — but the opponent attacks! Healing under pressure… bold choice.")

        elif player_action == Action.HEAL and ai_action == Action.DEFENSE:
            if self.lang == 'fa':
                print(static_detail + "Shoma ghodrat ra baazyabi mikonid dar hali ke harif mohaafezekaar miistad. Yek baazyabi-e paayedar.")
            else:
                print(static_detail + "You regain strength while the opponent stands guarded. A steady recovery.")

        elif player_action == Action.HEAL and ai_action == Action.HEAL:
            if self.lang == 'fa':
                print(static_detail + "Har doye shoma aghab miravid va behbood miyabid. Yek maks-e kootah ghabl az toofan.")
            else:
                print(static_detail + "Both of you step back and recover. A short pause before the storm.")

        elif player_action == Action.HEAL and ai_action == Action.DODGE:
            if self.lang == 'fa':
                print(static_detail + "Shoma darman mikonid. Harif dar hale harekat ast, mohtaat va sabok bar rooye paahaay-e khod.")
            else:
                print(static_detail + "You heal. The opponent keeps moving, cautious and light on their feet.")

        elif player_action == Action.HEAL and ai_action == Action.NONE:
            if self.lang == 'fa':
                print(static_detail + "Shoma lahzeh ra baraye darman ghanimat mishomorid. Hichkas shoma ra motavaqef nemikonad.")
            else:
                print(static_detail + "You take the moment to heal. No one stops you.")

        # ---------------- DODGE ----------------
        elif player_action == Action.DODGE and ai_action == Action.ATTACK:
            if player_result_detail['is_dodge_works']:
                if self.lang == 'fa':
                    print(static_detail + "Harif hamleh mikonad — amma shoma az khatar naapeed mishavid. Aafarin.")
                else:
                    print(static_detail + "The opponent attacks — but you vanish from harm. Nicely done.")
            else:
                if self.lang == 'fa':
                    print(static_detail + "Shoma talash mikonid faraar konid... amma zarbe shoma ra migirad. In yeki misuzad.")
                else:
                    print(static_detail + "You try to dodge… but the strike catches you. That one stings.")

        elif player_action == Action.DODGE and ai_action == Action.DEFENSE:
            if self.lang == 'fa':
                print(static_detail + "Shoma sari harekat mikonid dar hali ke harif mohkam miistad. Aazmayesh-e yekdigar.")
            else:
                print(static_detail + "You move swiftly while the opponent stands firm. Testing each other.")

        elif player_action == Action.DODGE and ai_action == Action.HEAL:
            if self.lang == 'fa':
                print(static_detail + "Shoma be harekat edame midahid. Harif az lahzeh baraye behbood estefade mikonad.")
            else:
                print(static_detail + "You keep moving. The opponent uses the moment to recover.")

        elif player_action == Action.DODGE and ai_action == Action.DODGE:
            if self.lang == 'fa':
                print(static_detail + "Har doye shoma dar atraf-e meydan miraghsid. Bedoone zarbah — faaghat kaar ba pa.")
            else:
                print(static_detail + "Both of you dance around the arena. No hits — just footwork.")

        elif player_action == Action.DODGE and ai_action == Action.NONE:
            if self.lang == 'fa':
                print(static_detail + "Shoma sabok faraar mikonid. Hich tahdidi be sooy-e shoma nemiayad.")
            else:
                print(static_detail + "You dodge lightly. No threat comes your way.")

        # ---------------- PLAYER NONE ----------------
        elif player_action == Action.NONE and ai_action == Action.ATTACK:
            if self.lang == 'fa':
                print(static_detail + "Harif bedoone tardedid hamleh mikonad. Shoma biharekat miistid — behtarin ide-ye shoma nist.")
            else:
                print(static_detail + "The opponent attacks without hesitation. You stand still — not your best idea.")

        elif player_action == Action.NONE and ai_action == Action.DEFENSE:
            if self.lang == 'fa':
                print(static_detail + "Harif sabooraaneh defaa mikonad. Montazer... shayad baraye harekat-e shoma.")
            else:
                print(static_detail + "The opponent defends patiently. Waiting… perhaps for you to move.")

        elif player_action == Action.NONE and ai_action == Action.HEAL:
            if self.lang == 'fa':
                print(static_detail + "Harif ghodrat-e khod ra baazyabi mikonad. Shoma be oo ejaazeh midahid.")
            else:
                print(static_detail + "The opponent restores their strength. You let them.")

        elif player_action == Action.NONE and ai_action == Action.DODGE:
            if self.lang == 'fa':
                print(static_detail + "Harif sabok harekat mikonad, shoma ra az nazdik zire nazar darad.")
            else:
                print(static_detail + "The opponent moves lightly, watching you closely.")
        elif player_action == Action.NONE and ai_action == Action.NONE:
            if self.lang == 'fa':
                print(static_detail + "Har doye shoma mohtaataneh maks mikonid, hichkodam maayel be anjaam-e avvalin harekat dar in nobat nistid.")
            else:
                print(static_detail + "Both of you pause cautiously, neither willing to make the first move this turn.")

    def after_turn(self, sheild_count_down: int, whether_game_ends: bool, player_wins: bool|None):
        print()

        if whether_game_ends == True:
            if player_wins == True:
                print(80 * '-')
                if self.lang == 'fa':
                    print('Shoma zarbeye nahayi ra vaared kardid — harif soghoot mikonad va piroozi az aan-e shomast.')
                else:
                    print('You delivered the final blow — the opponent falls, and victory is yours.')
                print(80 * '-')
            elif player_wins == False: 
                print(80 * '-')
                if self.lang == 'fa':
                    print('Harif shoma ra ba yek zarbeye ghaate maghloob mikonad — shoma shekast khordeh-id.')
                else:
                    print('The opponent overwhelms you with a decisive strike — you have been defeated.')
                print(80 * '-')
            elif player_wins == None:
                print(80 * '-')
                if self.lang == 'fa':
                    print('Har do jangavar hamzamaan ba zarbeye akhar jaan baakhtand — hich barandehi vojud nadarad va nabard ba tasavi payan miyaabad.')
                else:
                    print('Both fighters land their final blows at the same time and die on the battlefield — there is no victor, the battle ends in a draw.')
                print(80 * '-')
            else:
                raise ValueError('unexpected player_wins value provided ', str(player_wins))
            if self.lang == 'fa':
                print('Baazi-e khoobi bood, Aafarin...')
            else:
                print('Was a Good Game, GG...')
        elif whether_game_ends == False:
            sleep(2)
            if self.lang == 'fa':
                print('Nobat-e baadi dar sharof-e shoroo ast. Esteghaamat-e har do baazikon 20 vahed afzaayesh miyabad')
            else:
                print('Next turn is about to begin. Both Players Stamina will Increase by 30')
            if sheild_count_down > 1:
                if self.lang == 'fa':
                    print(f'Separ dar {sheild_count_down} nobat digar dar dastres khahad bood')
                else:
                    print(f'Shield will become available in {sheild_count_down} Turns')
            elif sheild_count_down == 1:
                if self.lang == 'fa':
                    print('Separ aknoon dar dastres khahad bood')
                else:
                    print('Shield will be Available Now')
            if self.lang == 'fa':
                print('Vaghti aamadeh hastid Enter ra bezanid.')
            else:
                print('Press Enter when you are ready.')
            input()
        else:
            raise ValueError('unexpected whether_game_ends value provided ', str(whether_game_ends))