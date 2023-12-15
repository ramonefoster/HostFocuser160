import socket

# IP address and port of the device
device_ip = '192.168.1.100'  # Replace this with your device's IP
device_port = 5555  # Replace this with the appropriate port number

# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to the device
    client_socket.connect((device_ip, device_port))
    print(f"Connected to {device_ip}:{device_port}")

    # Send data to the device
    message = "Hello, device!"
    client_socket.sendall(message.encode())

    # Receive data from the device
    data = client_socket.recv(1024)
    print(f"Received: {data.decode()}")

except socket.error as e:
    print(f"Socket error: {e}")

finally:
    # Close the socket connection
    client_socket.close()
