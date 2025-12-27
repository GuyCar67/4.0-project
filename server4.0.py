"""
HTTP Server Shell
Author: Guy Carmeli
Purpose: Provide a basis for Ex. 4
Note: The code is written in a simple way, without classes,
log files or other utilities, for educational purpose
Usage: Fill the missing functions and constants
27/12/25
"""

import os
import socket
import logging

QUEUE_SIZE = 10
IP = '0.0.0.0'
PORT = 80
SOCKET_TIMEOUT = 2
MAX_PACKET_SIZE = 1024
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
WEBROOT = os.path.join(PROJECT_DIR, 'webroot')


def asserts_checkup():
    """
    Tests the logic functions to ensure they behave as expected
    before starting the server.
    """
    good_request = "GET /index.html HTTP/1.1\r\nHost: localhost\r\n"
    assert validate_http_request(good_request) == (True, "/index.html")

    bad_method = "POST /index.html HTTP/1.1\r\nHost: localhost\r\n"
    assert validate_http_request(bad_method) == (False, None)

    not_3_parts = "Hello World"
    assert validate_http_request(not_3_parts) == (False, None)

    assert get_file_data("this_is_why_we_clash.txt") is None

    logging.info("!*asserts passed*!")


def get_file_data(file_name):
    """
    Get data from file
    :param file_name: the name of the file
    :return: the file data in a string
    """
    if not os.path.isfile(file_name):
        logging.error("File not found")
        return None
    with open(file_name, 'rb') as file:
        return file.read()


def handle_client_request(resource, client_socket):
    """
    Check the required resource, generate proper HTTP response and send to client
    :param resource: the required resource
    :param client_socket: a socket for the communication with the client
    :return: None
    """
    if resource == '/':
        uri = 'index.html'
    else:
        uri = resource
    if uri == '/moved':
        http_response = (
            "HTTP/1.1 302 Found\r\n"
            "Location: /\r\n"
            "Content-Length: 0\r\n"
            "\r\n"
        )
        client_socket.send(http_response.encode())
        return

    if uri == '/forbidden':
        client_socket.send(
            "HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n".encode()
        )
        return

    if uri == '/error':
        client_socket.send(
            "HTTP/1.1 500 Internal Server Error\r\nContent-Length: 0\r\n\r\n".encode()
        )
        return

    filename = os.path.join(WEBROOT, uri.lstrip('/').replace('/', os.sep))

    if '.' in uri:
        file_type = uri.split('.')[-1].lower()
    else:
        file_type = ''

    ext_type = "text/plain"
    if file_type == 'html':
        ext_type = "text/html;charset=utf-8"
    elif file_type == 'jpg':
        ext_type = "image/jpeg"
    elif file_type == 'css':
        ext_type = "text/css"
    elif file_type == 'js':
        ext_type = "text/javascript; charset=UTF-8"
    elif file_type == 'txt':
        ext_type = "text/plain"
    elif file_type == 'ico':
        ext_type = "image/x-icon"
    elif file_type == 'gif':
        ext_type = "image/jpeg"
    elif file_type == 'png':
        ext_type = "image/png"

    data = get_file_data(filename)
    if data is None:
        client_socket.send(
            "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n".encode()
        )
        return

    header = "HTTP/1.1 200 OK\r\n"
    header += f"Content-Type: {ext_type}\r\n"
    header += f"Content-Length: {len(data)}\r\n\r\n"
    http_response = header.encode() + data
    client_socket.send(http_response)


def validate_http_request(request):
    """
   Check if request is a valid HTTP request and returns TRUE / FALSE and
    the requested URL
    :param request: the request which was received from the client
    :return: a tuple of (True/False - depending if the request is valid,
    the requested resource )
    """
    try:
        request_line = request.split('\r\n')
        request_line = request_line[0]
        request_seperated = request_line.split(' ')
        if len(request_seperated) == 3:
            if request_seperated[0] == 'GET':
                if request_seperated[2] == 'HTTP/1.1':
                    return True, request_seperated[1]
        return False, None
    except Exception as exception:
        logging.error("validate http request: " + str(exception))
        return False, None


def handle_client(client_socket):
    """
    Handles client requests: verifies client's requests are legal HTTP,
    calls function to handle the requests
    :param client_socket: the socket for the communication with the client
    :return: None
    """
    logging.info('client connected')
    while_flag = True
    while while_flag:
        try:
            packet = client_socket.recv(MAX_PACKET_SIZE).decode()
            if not packet:
                logging.info("client disconnected")
                while_flag = False
            else:
                logging.info(f"request received:\n{packet}")
                valid_http, resource = validate_http_request(packet)
                if valid_http:
                    logging.info(f'got a valid http request for: {resource}')
                    handle_client_request(resource, client_socket)
                else:
                    logging.error('error: not a valid http request')
                    client_socket.send(
                        "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n".encode()
                    )
                    while_flag = False

        except socket.timeout:
            logging.info("socket timed out - closing connection")
            while_flag = False
        except Exception as errr:
            logging.error(f"error handling client: {errr}")
            while_flag = False

    logging.info('closing connection')
    client_socket.close()


def main():
    # Open a socket and loop forever while waiting for clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        logging.info("listening for connections on port %d" % PORT)

        while True:
            client_socket, client_address = server_socket.accept()
            try:
                logging.info('new connection received')
                client_socket.settimeout(SOCKET_TIMEOUT)
                handle_client(client_socket)
            except socket.error as err:
                logging.error('received socket exception - ' + str(err))
            finally:
                client_socket.close()
    except socket.error as err:
        logging.error('received socket exception - ' + str(err))
    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(
        filename='4.0SERVER.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asserts_checkup()
    main()