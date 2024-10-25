# Foi utilizado Flask para criar a API, junto com sqlite para manipular o banco de dados e o re para validar o CPF.
from flask import Flask, request, jsonify  
import sqlite3  
import re 

# Cria a instância do Flask
app = Flask(__name__) 

#Aqui temos uma função simples que abre a conexão com o banco de dados. Ela será chamada sempre que precisarmos realizar operações no banco.
def get_db_connection():
    return sqlite3.connect('clientes.db') 

#A primeira coisa que fazemos é remover qualquer caractere que não seja numérico usando expressões, assim garantimos que o CPF seja tratado corretamente.
def validar_cpf(cpf):
    # Apos isso removemos caracteres não numéricos e verificamos se o CPF tem 11 dígitos. Depois calculamos os dígitos para garantir que o CPF seja válido.
    cpf = re.sub(r'\D', '', cpf)
    if len(cpf) != 11: 
        return False  
    
    # Para os primeiros 9 dígitos do CPF, multiplicamos cada um pelo valor de uma sequência decrescente (10 a 2).
    # Depois somamos todos esses resultados e pegamos o resto da divisão por 11.
    primeiro_digito = sum(int(d) * (10 - i) for i, d in enumerate(cpf[:9])) % 11 

    # Para os primeiros 10 dígitos multiplicamos cada um por uma sequência decrescente (11 a 2).
    # Somamos esses resultados e pegamos o resto da divisão por 11.
    segundo_digito = sum(int(d) * (11 - i) for i, d in enumerate(cpf[:10])) % 11  

    # Retorna True se os dois dígitos calculados forem iguais aos dois últimos dígitos do CPF
    return cpf[-2:] == f"{primeiro_digito % 10}{segundo_digito % 10}" 

# "A primeira rota é a /upload, que permite o envio de um arquivo com dados dos clientes.
@app.route('/upload', methods=['POST'])

def upload_file():
    # Pegamos o arquivo enviado, lemos o conteúdo e dividindo cada linha em uma lista.
    file = request.files['file']  #
    lines = file.read().decode('utf-8').strip().splitlines() 

    # Conecta ao banco de dados e cria um cursor para executar comandos SQL
    conn = get_db_connection()  
    cursor = conn.cursor()  

    # Lista para armazenar dados dos clientes que forem inseridos no banco
    clientes_inseridos = []  

    # Alem de processar cada linha do arquivo dividimos os dados e verificamos se o CPF é válido antes de inserir no banco de dados.
    for line in lines:
        data = line.split()  # Divide a linha em partes (dados)
        if len(data) == 8 and validar_cpf(data[0]):  # Verifica se a linha contém 8 dados e se o CPF é válido
            # Aqui estamos inserindo os dados dos clientes no banco de dados, usando INSERT OR IGNORE para evitar duplicatas.
            cursor.execute('''
                INSERT OR IGNORE INTO clientes (cpf, private, incompleto, data_ultima_compra, 
                ticket_medio, ticket_ultima_compra, loja_frequente, loja_ultima_compra) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', tuple(data))  
            
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
        'clientes': clientes_inseridos  
    }), 200 

# A próxima rota é a /clientes, que retorna todos os registros em formato JSON.
@app.route('/clientes', methods=['GET'])
def listar_clientes():
    # Conecta ao banco de dados e cria um cursor para executar comandos SQL
    conn = get_db_connection()  
    cursor = conn.cursor() 

    # Executa uma consulta SQL para obter todos os registros na tabela `clientes`
    cursor.execute('SELECT * FROM clientes Where private = "0"')  
    clientes = cursor.fetchall() 

    # Pegamos cada cliente do banco e formatamos para ser enviado como resposta JSON.
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


# Por fim temos a rota /init, que inicializa o banco de dados, criando a tabela de clientes se ainda não existir.
def init_db():
    conn = get_db_connection() 
    cursor = conn.cursor()  

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cpf TEXT UNIQUE,  
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
