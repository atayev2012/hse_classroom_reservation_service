import grpc
from concurrent import futures
import auth_service_pb2_grpc, auth_service_pb2

class AuthService(auth_service_pb2_grpc.AuthServiceServicer):
    def Login(self, request, context):
        print(f"Received Login request with email: {request.email}")

        return auth_service_pb2.LoginResponse(
            status_code=200,
            status="OK",
            details=f"Email successfully received: {request.email}"
        )

def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    auth_service_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    server.add_insecure_port("[::]:5050")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    server()



