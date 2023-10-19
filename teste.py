import pika
import datetime
import threading

# Dicionário para rastrear as conexões dos grupos
group_connections = {}

def send_message(username, recipient):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    
    recipient_queue = f'chat_queue_{recipient}'
    channel.queue_declare(queue=recipient_queue)
    
    print(f"Bem-vindo, {username}! Você entrou na sala de chat.")
    print(f'Digite "Sair" para sair')
    
    while True:
        message = input(f'@{recipient}>> ')
        if message.lower() == 'sair':
            break
        elif message.startswith('@'):
            with open('users.txt', 'r') as file:
                users = file.read().splitlines()
            new_user = message.split('@')
            if new_user[1] in users:
                recipient = new_user[1]
                recipient_queue = f'chat_queue_{recipient}'
            else:
                print('Usuário não encontrado')
        else:
            channel.basic_publish(exchange='', routing_key=recipient_queue, body=f'@{username} diz: {message}')
    
    connection.close()
    print(f"Até logo, {username}!")

def send_group_message(username, group_name, message):
    if group_name not in group_connections:
        print(f"Grupo '{group_name}' não existe.")
        return
    group_exchange = f'group_exchange_{group_name}'
    channel = group_connections[group_name]['channel']

    channel.basic_publish(exchange=group_exchange, routing_key='', body=f'{username} diz: {message}')

def receive_group_messages(username, group_name):
    if group_name not in group_connections:
        print(f"Grupo '{group_name}' não existe.")
        return

    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()

    group_exchange = f'group_exchange_{group_name}'
    channel.exchange_declare(exchange=group_exchange, exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=group_exchange, queue=queue_name)

    def callback(ch, method, properties, body):
        timestamp = datetime.datetime.now().strftime("(%d/%m/%Y às %H:%M)")
        formatted_message = f"{timestamp} {username}#{group_name} diz: {body.decode('utf-8')}"
        print(formatted_message)
        print(f'@{method.routing_key}>> ', end='', flush=True)

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    thread = threading.Thread(target=channel.start_consuming)
    thread.daemon = True
    thread.start()

def receive_messages(username, queue_type, recipient=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()

    if queue_type == 'user':
        queue_name = f'chat_queue_{username}'
    elif queue_type == 'group':
        queue_name = f'group_queue_{recipient}'
    else:
        print("Tipo de fila inválido.")
        return

    def callback(ch, method, properties, body):
        timestamp = datetime.datetime.now().strftime("(%d/%m/%Y às %H:%M)")
        if queue_type == 'group':
            formatted_message = f"{timestamp} {recipient}#{username} diz: {body.decode('utf-8')}"
        else:
            formatted_message = f"{timestamp} {body.decode('utf-8')}"
        print(formatted_message)
        print(f'@{method.routing_key}>> ', end='', flush=True)

    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    thread = threading.Thread(target=channel.start_consuming)
    thread.daemon = True
    thread.start()
    
# Função para criar um grupo
def create_group(group_name, creator):
    if group_name in group_connections:
        print(f"Grupo '{group_name}' já existe.")
        return

    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    
    group_exchange = f'group_exchange_{group_name}'
    channel.exchange_declare(exchange=group_exchange, exchange_type='fanout')
    
    # Adiciona o criador automaticamente ao grupo
    add_user_to_group(creator, group_name)
    
    print(f"Grupo '{group_name}' criado.")
    
    # Adicione o novo grupo ao dicionário de conexões
    group_connections[group_name] = {'channel': channel}

    connection.close()


def add_user_to_group(username, group_name):
    with open(f"{group_name}.txt", 'a') as file:
        file.write(username + '\n')

    # Se o usuário adicionado não for o criador, notifica o criador
    if username != group_name:
        notify_group_creator(username, group_name)

def notify_group_creator(username, group_name):
    # Implemente aqui a lógica para notificar o criador do grupo
    print(f"{username} foi adicionado ao grupo '{group_name}' por {group_name}. Notificar o criador.")

# Função para remover um usuário de um grupo
def remove_user_from_group(username, group_name):
    # Lê os membros atuais do grupo a partir do arquivo
    with open(f"{group_name}.txt", 'r') as file:
        members = file.read().splitlines()

    # Verifica se o usuário está no grupo antes de removê-lo
    if username in members:
        members.remove(username)

        # Reescreve o arquivo com a lista atualizada de membros
        with open(f"{group_name}.txt", 'w') as file:
            for member in members:
                file.write(member + '\n')

# Função para remover um grupo
def remove_group(group_name):
    # Remove o arquivo do grupo
    import os
    try:
        os.remove(f"{group_name}.txt")
    except FileNotFoundError:
        pass

if __name__ == '__main__':
    username = input("User: ")

    with open('users.txt', 'r') as file:
        users = file.read().splitlines()
    with open('groups.txt', 'r') as file1:
        groups = file1.read().splitlines()

    if username not in users:
        print("Usuário não encontrado. Registre-se antes de entrar na sala de chat.")
    else:
        current_group = None
        print("Bem-Vindo ao sistema de chat utilizando o RabbitMQ")
        print("Os comandos propostos estão de acordo com o pedido nos relatórios 1 e 2")
        print("Digite 'sair' para sair:")

        thread_individual = threading.Thread(target=receive_messages, args=(username, 'user'))
        thread_individual.daemon = True
        thread_individual.start()

        while True:
            send = input(f"{('#' + current_group) if current_group else '>>'}")
            if send.startswith('@'):
                user = send.split('@')
                if user[1] in users:
                    send_message(username, user[1])
                else:
                    print('Usuário não encontrado, consulte a lista de usuários para confirmar')
            elif send.startswith('#'):
                group_name = send[1:]
                if group_name in groups:
                    current_group = group_name
                    thread_group = threading.Thread(target=receive_group_messages, args=(username, group_name))
                    thread_group.daemon = True
                    thread_group.start()
                    print(f'#{group_name}>> ')
                else:
                    print("Grupo não encontrado, consulte a lista de grupos.")
            elif send.startswith('!addGroup'):
                _, group_name = send.split(' ', 1)
                create_group(group_name, username)
                print(f"Grupo '{group_name}' criado.")
                groups.append(group_name)      
                # Adicione o novo grupo ao dicionário de conexões
                group_connections[group_name] = {'channel': pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))}
            elif send.startswith('!addUser'):
                _, user_to_add, group_name = send.split(' ', 2)
                add_user_to_group(user_to_add, group_name)
                print(f"Usuário '{user_to_add}' foi adicionado ao grupo '{group_name}'.")
            elif send.startswith('!delFromGroup'):
                _, user_to_remove, group_name = send.split(' ', 2)
                remove_user_from_group(user_to_remove, group_name)
                print(f"Usuário '{user_to_remove}' foi removido do grupo '{group_name}'.")
            elif send.startswith('!removeGroup'):
                _, group_name = send.split(' ', 1)
                remove_group(group_name)
                print(f"Grupo '{group_name}' removido.")
                groups.remove(group_name)  # Remova o grupo da lista de grupos
            elif current_group:
                # Se estiver em um grupo, envie a mensagem para o grupo
                send_group_message(username, current_group, send)
            elif send == 'sair':
                break
            else:
                print("Comando inválido.")

