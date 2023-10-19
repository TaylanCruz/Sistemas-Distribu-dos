import pika
import datetime
import threading

# Inicialize o dicionário group_connections
group_connections = {}

def load_group_connections():
    global group_connections  # Declare a variável group_connections como global
    with open('groups.txt', 'r') as file:
        groups = file.read().splitlines()

    for group_name in groups:
        connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
        channel = connection.channel()
    
        group_exchange = f'group_exchange_{group_name}'
        channel.exchange_declare(exchange=group_exchange, exchange_type='fanout')
        
        group_connections[group_name] = {'channel': channel}

# Antes de iniciar a interação com o usuário, chame a função para carregar os grupos existentes
load_group_connections()

def send_message(username, recipient):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    
    recipient_queue = f'chat_queue_{recipient}'
    channel.queue_declare(queue=recipient_queue)
    
    print(f"Bem-vindo, {username}! Você entrou na sala de chat.")
    print(f'Digite "Sair" para sair')
    
    while True:
        message = input(f'@{recipient} >> ')
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

def send_group_message(username, group_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    
    group_exchange = f'group_exchange_{group_name}'
    channel.exchange_declare(exchange=group_exchange, exchange_type='fanout')

    result = channel.queue_declare('', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange=group_exchange, queue=queue_name)

    group_connections[group_name] = {'queue': queue_name}

    print(f'Bem-vindo, {username}! Você entrou no grupo {group_name}')
    print(f'Digite "Sair" para sair')
    
    while True:
        message = input(f'#{group_name} >> ')
        if message.lower() == 'sair':
            break
        elif message.startswith('#'):
            with open('groups.txt', 'r') as file:
                groups = file.read().splitlines()
            new_group = message.split('#')
            if new_group[1] in groups:
                group_name = new_group[1]
                group_exchange = f'group_exchange_{group_name}'
            else:
                print("Grupo não encontrado")
        else:
            formatted_message = f'{username}#grupo1 diz: {message}'
            print(formatted_message)  # Exibe a mensagem no terminal do remetente
            channel.basic_publish(exchange=group_exchange, routing_key='', body=formatted_message)
    
    print(f'Até logo, {username}')

# Define a dictionary to store message history for each group
group_message_history = {}










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
        
def receive_messages(username, queue_type, recipient=None):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()

    queue_name = f'chat_queue_{username}'
    
    def callback(ch, method, properties, body):
        timestamp = datetime.datetime.now().strftime("(%d/%m/%Y às %H:%M)")
        formatted_message = f"{timestamp} {body.decode('utf-8')}"
        print(formatted_message)

    channel.queue_declare(queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    thread = threading.Thread(target=channel.start_consuming)
    thread.daemon = True
    thread.start()
    
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

    # Salve o nome do grupo no arquivo groups.txt
    with open('groups.txt', 'a') as groups_file:
        groups_file.write(group_name + '\n')
    name_group = group_name + '.txt'
    with open(name_group, 'w') as arquivo:
        arquivo.write(creator)

    connection.close()


def add_user_to_group(username, group_name):
    # Verifique se o grupo existe
    if group_name not in group_connections:
        print(f"Grupo '{group_name}' não existe.")
        return

    # Adicione o usuário ao arquivo do grupo
    with open(f"{group_name}.txt", 'a') as file:
        file.write(username + '\n')

    # Notifique o criador do grupo
    if username != group_name:
        notify_group_creator(username, group_name)

def notify_group_creator(username, group_name):
    # Verifique se o grupo existe
    if group_name not in group_connections:
        print(f"Grupo '{group_name}' não existe.")
        return

    # Implemente aqui a lógica para notificar o criador do grupo
    print(f"{username} foi adicionado ao grupo '{group_name}' por {group_name}. Notificar o criador.")

# Função para remover um usuário de um grupo
def remove_user_from_group(username, group_name):
    # Verifique se o grupo existe
    if group_name not in group_connections:
        print(f"Grupo '{group_name}' não existe.")
        return

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
    # Verifique se o grupo existe
    if group_name not in group_connections:
        print(f"Grupo '{group_name}' não existe.")
        return

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
            send = input(f">>")
            if send.startswith('@'):
                user = send.split('@')
                if user[1] in users:
                    send_message(username, user[1])
                else:
                    print('Usuário não encontrado, consulte a lista de usuários para confirmar')
            elif send.startswith('#'):
                group = send.split('#')
                if group[1] in groups:
                    send_group_message(username, group[1])    
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

