FROM python:3.9
WORKDIR /code
USER root
RUN apt-get update -y

COPY ./ /code/

RUN python -m pip install -r requirements.txt
RUN python -m pip install pydantic_sqlalchemy==0.0.9 --no-deps

CMD ["python", "main.py"]

# docker build -t arima-backend-images .
# docker run -d --name arima-backend -e endpoint_gateway_iot=http://172.26.176.1:8080/api -e development=0 -e db_endpoint=172.26.176.1 --restart always -p 3007:3007 -v volume_arima_cache:/code/arima_models arima-backend-images
