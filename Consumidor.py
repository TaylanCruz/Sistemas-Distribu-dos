import pika
import datetime

# Função para receber e exibir mensagens
def receive_messages(username):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='chat_queue')

    def callback(ch, method, properties, body):
        sender, message = body.decode().split('>>', 1)
        if sender != username:
            timestamp = datetime.date.today()  # Obtém a data atual
            print(f"{timestamp} - {sender}: {message}")

    channel.basic_consume(queue='chat_queue', on_message_callback=callback, auto_ack=True)

    print(f"Bem-vindo à sala de chat, {username}! Para sair, digite 'sair'.")

    channel.start_consuming()

# Função para receber mensagens de um grupo
def receive_group_messages(username, group_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    group_queue = f'group_queue_{group_name}'
    
    def callback(ch, method, properties, body):
        sender, message = body.decode().split('>>', 1)
        if sender != username:
            timestamp = datetime.date.today()  # Obtém a data atual
            print(f"{timestamp} - {sender} (grupo {group_name}): {message}")

    channel.queue_declare(queue=group_queue)
    channel.basic_consume(queue=group_queue, on_message_callback=callback, auto_ack=True)

    print(f"Bem-vindo ao grupo {group_name}, {username}! Para sair, digite 'sair'.")

    channel.start_consuming()


if __name__ == '__main__':
    username = input("Digite seu nome de usuário: ")

    # Verifica se o usuário existe (pode ser implementado melhor)
    with open("users.txt", "r") as file:
        users = file.read().splitlines()
    if username not in users:
        print("Usuário não encontrado. Registre-se antes de entrar na sala de chat.")
    else:
        receive_messages(username)
