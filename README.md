# Power Exchange Prices

This web application fetch electricity prices, which could be found on the well known Power Exchanges, 
from Entsoe Transparency Platform [restful API](https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html).

In order to use it, you must register an account on this [link](https://transparency.entsoe.eu/usrm/user/createPublicUser)
and also you will need to demand a Web Api Security Token. 
After you obtain a token, set it as an environment variable. 


#### How to run application

1) Install all necesery packages 
```
pip install -r requirements.txt
```

2) Install and run Redis

3) Start a development server
```
python manage.py runserver
```

4) Run the Celery worker
```
celery -A project worker -l INFO -P gevent
```

5) Navigate to http://localhost:8000/berza
