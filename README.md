# Docsend Scraper
This flask app converts a docsend slidedeck into a pdf

## Deployment
### To run locally:
In a python 3 virtualenv:
```
python setup.py install
FLASK_ENV=<development|production> python autoapp.py
```

### To run in a Docker container
```
docker build -t 'docsend:latest' .
docker container run -p<port>:5000 --name <container name> docsend
```
