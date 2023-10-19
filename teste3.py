import pika
import datetime
import threading

# Configurações do RabbitMQ
RABBITMQ_HOST = '127.0.0.1'
RABBITMQ_PORT = 5672

# Inicialize a conexão RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT))
channel = connection.channel()

# Inicialize o dicionário group_connections
group_connections = {}

def setup_group(group_name):
    if group_name in group_connections:
        return

    # Declare uma troca de grupo
    group_exchange = f'group_exchange_{group_name}'
    channel.exchange_declare(exchange=group_exchange, exchange_type='fanout')

    # Crie uma fila exclusiva para cada membro do grupo
    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue

    # Vincule a fila à troca do grupo
    channel.queue_bind(exchange=group_exchange, queue=queue_name)

    # Adicione a fila à lista de conexões do grupo
    group_connections[group_name] = {'queue': queue_name}

def send_group_message(username, group_name):
    setup_group(group_name)
    
    print(f'Bem-vindo, {username}! Você entrou no grupo {group_name}')
    print(f'Digite "Sair" para sair')
    
    while True:
        message = input(f'#{group_name} >> ')
        if message.lower() == 'sair':
            break
        else:
            group_exchange = f'group_exchange_{group_name}'
            channel.basic_publish(exchange=group_exchange, routing_key='', body=f'{username}#{group_name} diz: {message}')
    
    print(f'Até logo, {username}')

def receive_group_messages(username, group_name):
    setup_group(group_name)
    
    queue_name = group_connections[group_name]['queue']

    def callback(ch, method, properties, body):
        timestamp = datetime.datetime.now().strftime("(%d/%m/%Y às %H:%M)")
        formatted_message = f"{timestamp} {username}#{group_name} diz: {body.decode('utf-8')}"
        print(formatted_message)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print(f'Você está recebendo mensagens do grupo {group_name}.')
    channel.start_consuming()

if __name__ == '__main__':
    username = input("User: ")

    print("Bem-vindo ao sistema de chat utilizando o RabbitMQ")
    print("Digite 'sair' para sair.")

    while True:
        command = input("Digite um comando (ex: !join Grupo1, !leave Grupo1): ")

        if command.startswith('!join'):
            _, group_name = command.split(' ', 1)
            receive_group_messages(username, group_name)
        elif command == 'sair':
            break
        else:
            print("Comando inválido.")

