import datetime
from copy import Error, error
from infrastructure.switchlang import switch
import program_hosts as hosts
import infrastructure.state as state
import services.data_service as svc
from utils import error_msg, success_msg
from dateutil import parser


def run():
    print(' ****************** Welcome guest **************** ')
    print()

    show_commands()

    while True:
        action = hosts.get_action()

        with switch(action) as s:
            s.case('c', hosts.create_account)
            s.case('l', hosts.log_into_account)

            s.case('a', add_a_snake)
            s.case('y', view_your_snakes)
            s.case('b', book_a_cage)
            s.case('v', view_bookings)
            s.case('m', lambda: 'change_mode')

            s.case('?', show_commands)
            s.case('', lambda: None)
            s.case(['x', 'bye', 'exit', 'exit()'], hosts.exit_app)

            s.default(hosts.unknown_command)

        state.reload_account()

        if action:
            print()

        if s.result == 'change_mode':
            return


def show_commands():
    print('What action would you like to take:')
    print('[C]reate an account')
    print('[L]ogin to your account')
    print('[B]ook a cage')
    print('[A]dd a snake')
    print('View [y]our snakes')
    print('[V]iew your bookings')
    print('[M]ain menu')
    print('e[X]it app')
    print('[?] Help (this info)')
    print()


def add_a_snake():
    print(' ****************** Add a snake **************** ')
    
    if not state.active_account:
        error_msg("You must log-in first.")
        return

    name = input("What's the name of your snake?: ")
    species = input("What's the species of your snake?: ")
    while True:
        try:
            length = float(input("What's the length in inches of your snake? (enter a decimal number): "))
            break
        except Exception as e:
            error_msg("Incorrect number.")

    is_venomous = False
    while True:
        try:
            option = input("Is your snake venomous? (y/n): ")
            if not option in ["y", "n"]:
                raise Error("Incorrect option")
            
            is_venomous = option == "y"
            break
        except Exception as e:
            error_msg(str(e))
    
    snake = svc.create_snake(state.active_account, name, species, length, is_venomous)
    if snake:
        state.reload_account()
        success_msg(f"Snake added successfully with id {snake.id}")


def view_your_snakes():
    print(' ****************** Your snakes **************** ')

    if not state.active_account:
        error_msg("You must log-in first.")
        return
    
    # TODO: Get snakes from DB, show details list
    snakes = svc.get_snakes_for_user(state.active_account.id)
    print(f"You have {len(snakes)} snakes.")
    for snake in snakes:
        print("\t* {} is a {} that is {}m long and is {}venomous".format(
            snake.name,
            snake.species,
            snake.length,
            "" if snake.is_venomous else "not "
            ))
   


def book_a_cage():
    print(' ****************** Book a cage **************** ')
    
    if not state.active_account:
        error_msg("You must log-in first.")
        return
    
    # TODO: Verify they have a snake
    snakes = svc.get_snakes_for_user(state.active_account.id)
    if not snakes:
        error_msg("You must add a snake first.")
        return
    
    print("Let's start by finding available cages.")
    start_text = input("Check-in date (YYYY-MM-DD): ")
    if not start_text:
        error_msg("Cancelled")
        return
    
    checkin = parser.parse(start_text)
    checkout = parser.parse(input("Check-out date (YYYY-MM-DD): "))
    
    if checkin >= checkout:
        error_msg("Check-out must be after check-in.")
        return
    
    print("Which snake do you want to book?")
    for idx, snake in enumerate(snakes):
        print(f"[{idx}] {snake.name}")
        
    snake = snakes[int(input("Enter snake number: ")) - 1]
    
    cages = svc.get_available_cages(checkin, checkout, snake)
    print(f"Found {len(cages)} available cages.")
    for idx, cage in enumerate(cages):
        print("[{}] {} with {}m - carpeted: {} - has toys: {}".format(
            idx + 1,
            cage.name,
            cage.square_meters,
            'yes' if cage.is_carpeted else 'no',
            'yes' if cage.has_toys else 'no'
        ))
    cage = cages[int(input("Which cage would you like to book?: ")) - 1]
    svc.book_cage(state.active_account, snake, cage, checkin, checkout)
    success_msg("Successfully booked {} for {} at ${}/night".format(
        cage.name,
        snake.name,
        cage.price
    ))


def view_bookings():
    print(' ****************** Your bookings **************** ')
    
    if not state.active_account:
        error_msg("You must log-in first.")
        return
    
    snakes = {s.id: s for s in svc.get_snakes_for_user(state.active_account.id)}
    bookings = svc.get_bookings_for_user(state.active_account.email)
    
    print(f"You have {len(bookings)} bookings.")    
    for booking in bookings:
        print("\t* Snake: {} is booked at {} from {} for {} days".format(
            snakes.get(booking.guest_snake_id).name,
            booking.cage.name,
            datetime.date(booking.check_in_date.year, booking.check_in_date.month, booking.check_in_date.day),
            (booking.check_out_date - booking.check_in_date).days
        ))
