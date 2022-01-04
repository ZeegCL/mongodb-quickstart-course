import datetime
from os import error
from colorama import Fore
from infrastructure.switchlang import switch
import services.data_service as svc
import infrastructure.state as state
from utils import error_msg, success_msg, unknown_command
from dateutil import parser


def run():
    print(' ****************** Welcome host **************** ')
    print()

    show_commands()

    while True:
        action = get_action()

        with switch(action) as s:
            s.case('c', create_account)
            s.case('a', log_into_account)
            s.case('l', list_cages)
            s.case('r', register_cage)
            s.case('u', update_availability)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')
            s.case(['x', 'bye', 'exit', 'exit()'], exit_app)
            s.case('?', show_commands)
            s.case('', lambda: None)
            s.default(unknown_command)

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('Login to your [a]ccount')
    print('[L]ist your cages')
    print('[R]egister a cage')
    print('[U]pdate cage availability')
    print('[V]iew your bookings')
    print('Change [M]ode (guest or host)')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def create_account():
    print(' ****************** REGISTER **************** ')
    name = input('Enter your name:')
    email = input('Enter your e-mail:')
    
    user_account = svc.find_account_by_email(email)
    if user_account:
        error_msg("The account already exists")
        return
    
    new_account = svc.create_account(name, email)
    
    if not new_account:
        error_msg("There was an error creating the account.")
        return
    
    state.active_account = new_account
    success_msg(f"The account was created successfully! (ID: {state.active_account.id})")
    
    

def log_into_account():
    print(' ****************** LOGIN **************** ')

    email = input("Enter your email: ").strip().lower()
    account = svc.find_account_by_email(email)
    
    if not account:
        error_msg("Sorry! We couldn't find an account related to that email.")
        return
    
    state.active_account = account
    success_msg("Logged in successfully.")


def register_cage():
    print(' ****************** REGISTER CAGE **************** ')

    if not state.active_account:
        error_msg("You must log-in first.")
        return
    
    name = input('Enter cage name: ')
    
    while True:
        try:
            price = float(input('Enter cage price: '))
            break
        except Exception as e:
            error_msg("Incorrect number.")

    while True:
        try:
            square_meters = float(input('Enter cage square meters: '))
            break
        except Exception as e:
            error_msg("Incorrect number.")

    has_toys = False
    while True:
        try:
            option = input('Does the cage have toys? (y/n): ')
            if not option in ["y", "n"]:
                raise error("Incorrect option")
            
            has_toys = option == "y"
            break
        except Exception as e:
            error_msg(str(e))
    
    is_carpeted = False
    while True:
        try:
            option = input('Is the cage carpeted? (y/n): ')
            if not option in ["y", "n"]:
                raise error("Incorrect option")
            
            is_carpeted = option == "y"
            break
        except Exception as e:
            error_msg(str(e))
    
    allow_dangerous_snakes = False
    while True:
        try:
            option = input('Does the cage allow dangerous snakes? (y/n): ')
            if not option in ["y", "n"]:
                raise error("Incorrect option")
            
            allow_dangerous_snakes = option == "y"
            break
        except Exception as e:
            error_msg(str(e))
    
    
    cage = svc.create_cage(state.active_account, name, price, square_meters, has_toys, is_carpeted, allow_dangerous_snakes)
    
    if not cage:
        error_msg("There was an error creating the cage.")
        return
    
    state.reload_account()
    success_msg(f"Cage {cage.name} was created successfully!")



def list_cages(supress_header=False):
    if not supress_header:
        print(' ******************     Your cages     **************** ')

    if not state.active_account:
        error_msg("You must log-in first.")
        return

    cages = svc.find_cages_for_user(state.active_account)

    if not cages:
        error_msg("You don't have any cages registered.")
        return

    print(f"You have {len(cages)} cages registered.")
    for idx, cage in enumerate(cages):
        print(f"[{idx+1}] {cage.name} - ${cage.price}/day")
        for booking in cage.bookings:
            print("\t* Booking: {}, {} days, booked? {}".format(
                booking.check_in_date,
                (booking.check_out_date - booking.check_in_date).days,
                'YES' if booking.booked_date is not None else 'NO'
            ))


def update_availability():
    print(' ****************** Add available date **************** ')

    if not state.active_account:
        print("You must log-in first.")
        return
    
    list_cages(True)
    
    cage_number = input("Enter cage number: ")
    if not cage_number.isdigit():
        error_msg("Incorrect cage number.")
        return
    
    cage_number = int(cage_number)
    
    cages = svc.find_cages_for_user(state.active_account)
    selected_cage = cages[cage_number-1]
    success_msg(f"Selected cage {selected_cage.name}")

    start_date = parser.parse(input("Enter start date (YYYY-MM-DD): "))
    days = int(input("How many days will this cage be available?: "))
    svc.add_available_date(
        state.active_account,
        selected_cage,
        start_date,
        days
    )
    success_msg(f"Added available date for cage {selected_cage.name}")

def view_bookings():
    print(' ****************** Your bookings **************** ')

    if not state.active_account:
        error_msg("You must log-in first.")
        return
    
    cages = svc.find_cages_for_user(state.active_account)
    bookings = [
        (cage, booking)
        for cage in cages
        for booking in cage.bookings
        if booking.booked_date is not None
    ]
    
    print(f"You have {len(bookings)} bookings.")
    for cage, booking in bookings:
        print("\t* Cage {}, booked date: {}, from {} for {} days".format(
            cage.name, 
            datetime.date(booking.booked_date.year, booking.booked_date.month, booking.booked_date.day),
            datetime.date(booking.check_in_date.year, booking.check_in_date.month, booking.check_in_date.day),
            booking.duration_in_days
        ))
    

def exit_app():
    print()
    print('bye')
    raise KeyboardInterrupt()


def get_action():
    text = '> '
    if state.active_account:
        text = f'{state.active_account.name}> '

    action = input(Fore.YELLOW + text + Fore.WHITE)
    return action.strip().lower()