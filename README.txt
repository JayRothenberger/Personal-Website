#on heroku make sure to run this command for the code to work on a new pipeline/app
heroku run python manage.py migrate
#on desktop run
python manage.py migrate --run-syncdb