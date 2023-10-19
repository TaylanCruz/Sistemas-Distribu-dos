import pika
import datetime
import threading
import time


# Função para enviar mensagens privadas
def send_message(username, recipient):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    # Crie uma fila específica para o destinatário
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
                novo_user = file.read().splitlines()
            new_user = message.split('@')
            if new_user[1] in novo_user:
                recipient = new_user[1]  # Atualiza o destinatário
                recipient_queue = f'chat_queue_{recipient}'
            else:
                print('Usuário não encontrado')
        elif message.startswith('!'):
            another = message.split()
            tensor = another[0].split('!')
            if tensor[1] == 'addGroup':
            	if another[1] == '':
            	    print("Insira um nome para o grupo após !addGroup %nome%")
            	else:
            	    with open("groups.txt",'a') as file:
            	       novo = another[1]
            	       file.write(novo + '\n')            	
	            	 
        else:
            channel.basic_publish(exchange='', routing_key='chat_queue', body=f'@{recipient}>> {message}')
    	
    connection.close()
    print(f"Até logo, {username}!")


# Função para enviar mensagem para um grupo
def send_group_message(username, group_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    # Crie uma fila específica para o grupo
    group_queue = f'group_queue_{group_name}'
    channel.queue_declare(queue=group_queue)

    print(f"Bem-vindo, {username}! Você entrou no grupo {group_name}.")
    print(f'Digite "Sair" para sair')

    while True:
        message = input(f'{group_name}>> ')
        if message.lower() == 'sair':
            break
        else:
            channel.basic_publish(exchange='', routing_key=group_queue, body=f'{username}>> {message}')

    connection.close()
    print(f"Até logo, {username}!")

def receive_messages(username):
    connection = pika.BlockingConnection(pika.ConnectionParameters('127.0.0.1'))
    channel = connection.channel()
    user_queue = f'chat_queue_{username}'
    
    def callback(ch, method, properties, body):
        timestamp = datetime.datetime.now().strftime("(%d/%m/%Y às %H:%M)")
        sender, message = body.split(' diz: ', 1)
        formatted_message = f"{timestamp} {sender} {message}"
        print(formatted_message)
    
    channel.queue_declare(queue=user_queue)
    channel.basic_consume(queue=user_queue, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ == '__main__':
    username = input("User: ")

    #Verifica se o usuário existe
    with open('users.txt','r') as file:
        users = file.read().splitlines()
    if username not in users:
        print("Usuário não encontrado. Registri-se antes de entrar na sala de chat.")
    else:
        print("Digite 'sair' para sair:")
        thread = threading.Thread(target=receive_messages, args=(username,))
        thread.daemon=True
        thread.start()
    
        while True:
            send = input(">>")
            if send.startswith('@'):
                user = send.split('@')
                if user[1] in users:
                    send_message(username, user[1])
                else:
                    print('Usuário não encontrado, consulte a lista de usuários para confirmar')
            elif send == 'sair':
                break

