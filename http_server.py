import socket
import sys
import traceback
import os
import subprocess
import mimetypes


def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return b"\r\n".join([b"HTTP/1.1 200 OK",
                         b"Content-Type: " + mimetype,
                         b"",
                         body])


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""

    return b"\r\n".join([b"HTTP/1.1 405 Method Not Allowed",
                         b"",
                         b"Method not allowed on this server"])


def response_not_found():
    """Returns a 404 Not Found response"""

    return b"\r\n".join([b"HTTP/1.1 404 Not Found",
                         b""])


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """

    method, path, _ = request.strip().split("\r\n")[0].split(" ")
    if method != 'GET':
        raise NotImplementedError(method)

    return path


def response_path(uri):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """
    home = "./webroot"
    content = b"not implemented"
    mime_type = b"not implemented"
    path = home + uri

    # Raise a NameError if the requested content is not present under webroot.
    if uri == "/":
        req_item = path
    else:
        req_item = path.split("/")[-1]
        for _, dirs, files in os.walk(home):
            if req_item in dirs or req_item in files:
                break
        else:
            raise NameError(f'Invalid path: {path}')

    if os.path.isfile(path):
        f_ext = "." + req_item.split(".")[-1]

        try:
            mime_type = mimetypes.types_map[f_ext].encode("utf-8")
        except KeyError:
            raise NameError(f'Invalid file type: {f_ext}')

        if f_ext.endswith(".py"):
            content = subprocess.check_output([sys.executable, "make_time.py"])
        else:
            content = b""
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(32)
                    if not chunk:
                        break
                    content += chunk
    else:
        mime_type = b"text/plain"
        for _, dirs, files in os.walk(path):
            content = ", ".join(dirs + files).encode("utf-8")
            break

    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                response = ""
                try:
                    path = parse_request(request)
                    content, mime_type = response_path(path)
                except NotImplementedError:
                    response = response_method_not_allowed()
                except NameError:
                    response = response_not_found()
                else:
                    response = response_ok(body=content, mimetype=mime_type)

                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)
