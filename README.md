# Smart Seat Reservation (Django)

## Setup
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_seats        # 60 seats + user1/user2/user3 (password: test1234)
    python manage.py runserver
Do alag browsers / incognito me user1 aur user2 se login karke same seat try karo.

## Tests
    python manage.py test seats
PostgreSQL pe concurrency test (20 threads, 1 seat) bhi chalta hai.
