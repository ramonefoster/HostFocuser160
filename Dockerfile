FROM python:3.11

# stdout and stderr streams directly
ENV PYTHONUNBUFFERED 1
# Do not write .pyc bytecode files to disk
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /focuser160

# Install dependencies
COPY requirements.txt /focuser160/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . /focuser160/

# Set the command to run your application
CMD ["python", "main.py"]