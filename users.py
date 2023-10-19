import os

# Função para registrar um novo usuário
def register_user():
    username = input("Digite um nome de usuário para registro: ")
    if username.strip():
        with open("users.txt", "a") as file:
            file.write(username + "\n")
        print(f"Usuário '{username}' registrado com sucesso!")
    else:
        print("Nome de usuário inválido.")

# Função para criar um novo grupo
def create_group():
    group_name = input("Digite um nome para o novo grupo: ")
    if group_name.strip():
        with open("groups.txt", "a") as file:
            file.write(group_name + "\n")
        print(f"Grupo '{group_name}' criado com sucesso!")
    else:
        print("Nome de grupo inválido.")

# Função para verificar se um usuário existe
def user_exists(username):
    with open("users.txt", "r") as file:
        users = file.read().splitlines()
    return username in users

if __name__ == '__main__':
    if not os.path.exists("users.txt"):
        open("users.txt", "w").close()  # Cria o arquivo de usuários se não existir
    if not os.path.exists("groups.txt"):
        open("groups.txt", "w").close()  # Cria o arquivo de grupos se não existir

    while True:
        print("\nEscolha uma opção:")
        print("1. Registrar novo usuário")
        print("2. Criar novo grupo")
        print("3. Sair")

        choice = input("Opção: ")

        if choice == "1":
            register_user()
        elif choice == "2":
            create_group()
        elif choice == "3":
            exit()
        else:
            print("Opção inválida. Escolha novamente.")
