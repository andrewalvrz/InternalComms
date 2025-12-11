import grpc
from concurrent import futures
import chat_pb2
import chat_pb2_grpc
import threading
import queue

VALID_TOKENS = {"token1", "token2", "token3"}

class ChatServicer(chat_pb2_grpc.ChatServicer):
    def __init__(self):
        self.clients = []
        self.lock = threading.Lock()

    def Join(self, request_iterator, context):
        # First message is username + token
        first_msg = next(request_iterator)
        user = first_msg.user
        token = first_msg.text

        if token not in VALID_TOKENS:
            print(f"Access denied for user {user}")
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Invalid token")
        print(f"User {user} connected with token {token}")

        q = queue.Queue()
        with self.lock:
            self.clients.append(q)

        # Thread to receive messages from this client
        def receive():
            try:
                for msg in request_iterator:
                    with self.lock:
                        for client_q in self.clients:
                            client_q.put(msg)
                          except grpc.RpcError:
                pass
            finally:
                with self.lock:
                    self.clients.remove(q)
                    print(f"User {user} disconnected")

        threading.Thread(target=receive, daemon=True).start()

        while True:
            msg = q.get()
            yield chat_pb2.Message(user=msg.user, text=msg.text)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started on port 50051, waiting for clients...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

