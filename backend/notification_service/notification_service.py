import signal
import grpc
from concurrent import futures
import notification_service_pb2_grpc, notification_service_pb2
from config import config

class NotificationService(notification_service_pb2_grpc.NotificationServiceServicer):
    def SendVerificationCode(self, request, context):
        pass
    
    
    # def Login(self, request, context):
    #     print(f"Received Login request with email: {request.email}")

        # return auth_service_pb2.LoginResponse(
        #     status_code=200,
        #     status="OK",
        #     details=f"Email successfully received: {request.email}"
        # )

def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    notification_service_pb2_grpc.add_NotificationServiceServicer_to_server(NotificationService(), server)
    server.add_insecure_port(f"[::]:{config.port}")
    
    def handle_shutdown(signum, frame):
        stop_event = server.stop(5)
        stop_event.wait()
        print("Notification Service Terminated")

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    server.start()
    print(f"Notification Service starting at {config.host}:{config.port}")
    
    server.wait_for_termination()


if __name__ == "__main__":
    server()



