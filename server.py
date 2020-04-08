#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if login in self.server.users_online:
                    self.transport.write(f"Логин {login} занят, попробуйте другой\r\n".encode())
                else:
                    self.login = login
                    self.server.users_online.append(self.login)
                    self.transport = self.transport
                    self.transport.write(f"Привет, {self.login}!\r\n".encode())
                    self.send_history()
            else:
                self.transport.write("Неверный логин, начните ввод с 'login:'\r\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        print(f"Клиент {self.login} вышел")
        self.server.clients.remove(self)

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.message_history.append(message.encode())

        for user in self.server.clients:
            if self != user:
                user.transport.write(message.encode())

    def send_history(self):
        for message in reversed(self.server.message_history[-1:-11:-1]):
            self.transport.write(message)


class Server:
    clients: list
    users_online: list
    message_history: list

    def __init__(self):
        self.clients = []
        self.users_online = []
        self.message_history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")

