FROM python:3.8-alpine
RUN mkdir /app
ADD . /app
WORKDIR /app
RUN pip3 install --upgrade pip
CMD ["python", "app.py","1","{'date': '2021-01-01T08:00:00+00:00','doctor': 'Dr. Smith'}","{'name':'Kedhar', 'dob':'08-07-1994', 'email':'kedhar.kb@gmail.com'}"]