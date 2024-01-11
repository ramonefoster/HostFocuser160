import zmq

context = zmq.Context()
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://200.131.64.237:7005")

# Subscribe to multiple topics
subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

print("Client Online")
poller = zmq.Poller()
poller.register(subscriber, zmq.POLLIN)

while True:
    socks = dict(poller.poll(100))
    if socks.get(subscriber) == zmq.POLLIN:
        message = subscriber.recv().decode()
        # topic = message[0]
        # data = message[1]  # Assuming the data is received as the second part of the multipart message
        print(f"Received: {message}")

