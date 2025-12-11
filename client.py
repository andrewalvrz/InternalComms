import grpc
import chat_pb2
import chat_pb2_grpc
import threading
import queue

SERVER_IP = "100.1XX.XX.XX"  # Azure VM Tailscale IP

def run(user, token):
    channel = grpc.insecure_channel(f"{SERVER_IP}:50051")
    stub = chat_pb2_grpc.ChatStub(channel)
    message_queue = queue.Queue()

    # Generator for sending messages to the server
    def message_generator():
        # First message is token for authentication
        yield chat_pb2.Message(user=user, text=token)
        while True:
            msg = message_queue.get()
            if msg == "/quit":
                return
            yield chat_pb2.Message(user=user, text=msg)

    # Thread to receive messages from server
    def listen_server(responses):
        try:
            for msg in responses:
                # Avoid printing own message twice
                if msg.user != user:
                    print(f"[{msg.user}] {msg.text}")
        except grpc.RpcError as e:
            print(f"Server disconnected: {e}")

    # Start streaming RPC
    responses = stub.Join(message_generator())
    threading.Thread(target=listen_server, args=(responses,), daemon=True).start()

    # Main loop to read user input
    while True:
        text = input()
        message_queue.put(text)
        if text == "/quit":
            break

if __name__ == "__main__":
    name = input("Enter your username: ")
    token = input("Enter your access token (token1, token2, token3): ")
    run(name, token)
