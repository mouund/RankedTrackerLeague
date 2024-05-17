FROM python:3.10
ADD requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /opt/app
WORKDIR /opt/app
CMD ["python3" , "main.py"]