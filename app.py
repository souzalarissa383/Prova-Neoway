from flask import Flask, request, jsonify  # Importa as bibliotecas necessárias do Flask
import sqlite3  # Importa a biblioteca SQLite para manipulação do banco de dados
import re  # Importa a biblioteca para expressões regulares, usada na validação

app = Flask(__name__)  # Cria uma instância da aplicação Flask

# Função para conectar ao banco de dados SQLite
def get_db_connection():
    return sqlite3.connect('clientes.db')  # Retorna uma nova conexão ao banco de dados

# Função para validar o CPF
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)  # Remove caracteres não numéricos do CPF
    if len(cpf) != 11:  # Verifica se o CPF tem 11 dígitos
        return False  # Retorna False se o CPF não tiver 11 dígitos
    # Validação do CPF utilizando fórmula específica
    primeiro_digito = sum(int(d) * (10 - i) for i, d in enumerate(cpf[:9])) % 11  # Calcula o primeiro dígito verificador
    segundo_digito = sum(int(d) * (11 - i) for i, d in enumerate(cpf[:10])) % 11  # Calcula o segundo dígito verificador
    # Compara os dígitos calculados com os dígitos finais do CPF
    return cpf[-2:] == f"{primeiro_digito % 10}{segundo_digito % 10}"  # Retorna True se os dígitos verificadores estiverem corretos

# Rota para upload do arquivo
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']  # Obtém o arquivo enviado na requisição
    lines = file.read().decode('utf-8').strip().splitlines()  # Lê o conteúdo do arquivo, decodifica e divide em linhas
    conn = get_db_connection()  # Conecta ao banco de dados
    cursor = conn.cursor()  # Cria um cursor para executar comandos SQL

    clientes_inseridos = []  # Lista para armazenar os clientes inseridos

    # Processa cada linha do arquivo
    for line in lines:
        data = line.split()  # Divide a linha em partes (dados)
        if len(data) == 8 and validar_cpf(data[0]):  # Verifica se a linha contém 8 dados e se o CPF é válido
            cursor.execute('''
                INSERT OR IGNORE INTO clientes (cpf, private, incompleto, data_ultima_compra, 
                ticket_medio, ticket_ultima_compra, loja_frequente, loja_ultima_compra) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', tuple(data))  # Insere os dados no banco de dados
            
            # Adiciona os dados do cliente à lista em formato de dicionário
            cliente_dict = {
                'cpf': data[0],
                'private': data[1],
                'incompleto': data[2],
                'data_ultima_compra': None if data[3] == 'NULL' else data[3],
                'ticket_medio': None if data[4] == 'NULL' else data[4],
                'ticket_ultima_compra': None if data[5] == 'NULL' else data[5],
                'loja_frequente': None if data[6] == 'NULL' else data[6],
                'loja_ultima_compra': None if data[7] == 'NULL' else data[7]
            }
            clientes_inseridos.append(cliente_dict)  # Adiciona o dicionário à lista

    conn.commit()  # Salva todas as alterações feitas no banco
    cursor.close()  # Fecha o cursor
    conn.close()  # Fecha a conexão com o banco
    
    # Retorna a mensagem de sucesso e os dados dos clientes inseridos
    return jsonify({
        'message': 'Arquivo carregado com sucesso!',
        'clientes': clientes_inseridos  # Inclui os dados dos clientes inseridos
    }), 200  # Retorna uma resposta JSON com status 200

# Rota para listar todos os clientes em formato JSON
@app.route('/clientes', methods=['GET'])
def listar_clientes():
    conn = get_db_connection()  # Conecta ao banco de dados
    cursor = conn.cursor()  # Cria um cursor

    cursor.execute('SELECT * FROM clientes')  # Executa a consulta para obter todos os registros
    clientes = cursor.fetchall()  # Obtém todos os registros retornados

    # Formata os dados em uma lista de dicionários
    lista_clientes = []
    for cliente in clientes:
        lista_clientes.append({
            'id': cliente[0],
            'cpf': cliente[1],
            'private': cliente[2],
            'incompleto': cliente[3],
            'data_ultima_compra': None if cliente[4] == 'NULL' else cliente[4],
            'ticket_medio': None if cliente[5] == 'NULL' else cliente[5],
            'ticket_ultima_compra': None if cliente[6] == 'NULL' else cliente[6],
            'loja_frequente': None if cliente[7] == 'NULL' else cliente[7],
            'loja_ultima_compra': None if cliente[8] == 'NULL' else cliente[8]
        })

    cursor.close()  # Fecha o cursor
    conn.close()  # Fecha a conexão com o banco
    return jsonify(lista_clientes), 200  # Retorna a lista de clientes em formato JSON

# Função para inicializar o banco de dados
def init_db():
    conn = get_db_connection()  # Conecta ao banco de dados
    cursor = conn.cursor()  # Cria um cursor
    # Cria a tabela de clientes se ela não existir
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  # ID único e auto-incrementável
            cpf TEXT UNIQUE,  # CPF único
            private TEXT,
            incompleto TEXT,
            data_ultima_compra TEXT,
            ticket_medio REAL,
            ticket_ultima_compra REAL,
            loja_frequente TEXT,
            loja_ultima_compra TEXT
        );
    ''')
    conn.commit()  # Salva as alterações no banco
    cursor.close()  # Fecha o cursor
    conn.close()  # Fecha a conexão com o banco

# Rota para inicializar o banco de dados
@app.route('/init', methods=['GET'])
def initialize():
    init_db()  # Chama a função para inicializar o banco de dados
    return jsonify({'message': 'Banco de dados inicializado com sucesso!'}), 200  # Retorna mensagem de sucesso em formato JSON

# Inicia o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)  # Inicia a aplicação em modo de depuração (debug)
