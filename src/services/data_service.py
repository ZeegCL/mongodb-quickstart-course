import datetime
from typing import List
import bson
from mongoengine.connection import ConnectionFailure
from mongoengine.errors import ValidationError
from data.cages import Cage
from data.owners import Owner
from data.snakes import Snake
from data.bookings import Booking
from utils import error_msg
from pymongo.errors import ServerSelectionTimeoutError


def create_account(name: str, email: str) -> Owner:
    owner = Owner()
    owner.name = name
    owner.email = email
    try:
        owner.save()
        return owner
    except ConnectionFailure as e:
        error_msg("Oops! There was an error connecting to the database.")
    except ValidationError as e:
        error_msg(str(e))
    
    return None


def find_account_by_email(email: str) -> Owner:
    try:
        # account = Owner.objects().filter(email=email).first() # Long version
        account = Owner.objects(email=email).first()
    except ServerSelectionTimeoutError as e:
        error_msg("Oops! There was an error connecting to the database.")
        return None

    return account


def create_cage(owner: Owner, name: str, price: float, square_meters: float, is_carpeted: bool, has_toys: bool, allow_dangerous_snakes: bool) -> Cage:
    cage = Cage()
    cage.name = name
    cage.price = price
    cage.square_meters = square_meters
    cage.is_carpeted = is_carpeted
    cage.has_toys = has_toys
    cage.allow_dangerous_snakes = allow_dangerous_snakes
    
    try:
        cage.save()
        account = find_account_by_email(owner.email)
        account.cage_ids.append(cage.id)
        account.save()
        
        return cage
    except ConnectionFailure as e:
        error_msg("Oops! There was an error connecting to the database.")
    except ValidationError as e:
        error_msg(str(e))
        
    return None


def find_cages_for_user(owner: Owner) -> Cage:
    cages = list(Cage.objects(id__in = owner.cage_ids))
    return cages


def add_available_date(owner: Owner, cage: Cage, start_date: datetime.datetime, days: int) -> bool:
    try:
        booking = Booking()
        booking.check_in_date = start_date
        booking.check_out_date = start_date + datetime.timedelta(days=days)
        
        cage = Cage.objects(id=cage.id).first()
        cage.bookings.append(booking)
        cage.save()
        return True
    except ConnectionFailure as e:
        error_msg("Oops! There was an error connecting to the database.")
    except ValidationError as e:
        error_msg(str(e))
        
    return False


def create_snake(account: Owner, name: str, species: str, length: float, is_venomous: bool) -> Snake:
    snake = Snake()
    snake.name = name
    snake.species = species
    snake.length = length
    snake.is_venomous = is_venomous
    
    try:
        snake.save()
        
        owner = find_account_by_email(account.email)
        owner.snake_ids.append(snake.id)
        owner.save()
        return snake
    except ConnectionFailure as e:
        error_msg("Oops! There was an error connecting to the database.")
    except ValidationError as e:
        error_msg(str(e))
        
    return None


def get_snakes_for_user(user_id: bson.ObjectId) -> List[Snake]:
    owner = Owner.objects(id=user_id).first()
    snakes = Snake.objects(id__in = owner.snake_ids).all()

    return list(snakes)


def get_available_cages(checkin: datetime.datetime, checkout: datetime.datetime, snake: Snake) -> List[Cage]:
    min_size = snake.length / 4
    query = Cage.objects() \
        .filter(square_meters__gte=min_size) \
        .filter(bookings__check_in_date__lte=checkin) \
        .filter(bookings__check_out_date__gte=checkout)
    
    if snake.is_venomous:
        query = query.filter(allow_dangerous_snakes=True)
    
    cages = query.order_by('price', '-square_meters').all()
    
    matching_cages = []
    for c in cages:
        for b in c.bookings:
            if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id is None:
                matching_cages.append(c)

    return matching_cages


def book_cage(account: Owner, snake: Snake, cage: Cage, checkin: datetime.datetime, checkout: datetime.datetime) -> bool:
    booking = None
    for b in cage.bookings:
        if b.check_in_date <= checkin and b.check_out_date >= checkout and b.guest_snake_id is None:
            booking = b
            break
    
    booking.guest_owner_id = account.id
    booking.booked_date = datetime.datetime.now()
    booking.guest_snake_id = snake.id
    
    cage.save()
    

def get_bookings_for_user(email: str) -> List[Booking]:
    account = find_account_by_email(email)
    booked_cages = Cage.objects() \
        .filter(bookings__guest_owner_id=account.id) \
        .only('bookings', 'name')
    
    def map_cage_to_booking(cage, booking):
        booking.cage = cage
        return booking
    
    bookings = [map_cage_to_booking(cage, booking) 
                for cage in booked_cages
                for booking in cage.bookings
                    if booking.guest_owner_id == account.id]

    return bookings