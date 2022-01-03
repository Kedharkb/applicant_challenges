FROM python:3.8-alpine
RUN mkdir /app
ADD . /app
WORKDIR /app
RUN pip3 install --upgrade pip
ENTRYPOINT ["python"]