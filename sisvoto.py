import sqlite3
from datetime import datetime, timezone, timedelta

# Configuração de adaptação de datetime para SQLite
sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
sqlite3.register_converter("TIMESTAMP", lambda value: datetime.fromisoformat(value.decode() if isinstance(value, bytes) else value))

def inicializar_bd(cursor, conn, turmas):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            turma TEXT,
            voto TEXT NOT NULL,
            horario TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    for turma in turmas:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{turma}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );
        ''')
    conn.commit()

def registrar_dados(cursor, conn, alunos):
    for turma, dados in alunos.items():
        cursor.executemany(f'INSERT OR IGNORE INTO "{turma}" (nome, email) VALUES (?, ?)', dados)
    conn.commit()

def registrar_voto(email, turma, voto, cursor, conn):
    try:
        horario_local = datetime.now(timezone.utc) - timedelta(hours=3)
        cursor.execute("INSERT INTO votos (email, turma, voto, horario) VALUES (?, ?, ?, ?)", (email, turma, voto, horario_local))
        conn.commit()
        print(f"Voto '{voto}' registrado com sucesso para a turma '{turma}'!")
    except sqlite3.Error as e:
        print(f"Erro ao registrar voto: {e}")

def verificar_email(email, turma, cursor):
    cursor.execute(f'SELECT nome FROM "{turma}" WHERE email = ?', (email,))
    aluno = cursor.fetchone()
    if aluno:
        cursor.execute("SELECT * FROM votos WHERE email = ?", (email,))
        return aluno[0], cursor.fetchone() is not None
    return None, False

def processar_voto(turma, cursor, conn):
    email = input(f"Digite seu e-mail para votar na turma {turma}: ")
    nome_aluno, duplicado = verificar_email(email, turma, cursor)
    if nome_aluno:
        if duplicado:
            print(f"{nome_aluno} (Turma: {turma}), você já votou.")
        else:
            print(f"Bem-vindo(a), {nome_aluno} (Turma: {turma})!")
            opcoes = {'1': 'Chapa 1', '2': 'Voto Nulo', '3': 'Voto em Branco'}
            while True:
                voto = input("\nEscolha sua opção de voto:\n1 - Chapa 1\n2 - Voto Nulo\n3 - Voto em Branco\nDigite o número correspondente: ")
                if voto in opcoes:
                    registrar_voto(email, turma, opcoes[voto], cursor, conn)

                    # Contagem de votos após o registro
                    cursor.execute(f'SELECT COUNT(*) FROM "{turma}"')
                    total_alunos = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(DISTINCT email) FROM votos WHERE turma = ?", (turma,))
                    alunos_que_votaram = cursor.fetchone()[0]
                    alunos_faltantes = total_alunos - alunos_que_votaram

                    print(f"\nResumo da turma {turma}:")
                    print(f"- Total de alunos: {total_alunos}")
                    print(f"- Alunos que já votaram: {alunos_que_votaram}")
                    print(f"- Alunos que ainda não votaram: {alunos_faltantes}\n")

                    break
                print("Opção inválida. Tente novamente.")
    else:
        print(f"E-mail não cadastrado na turma {turma}.")

def alterar_votos(cursor, conn):
    cursor.execute("UPDATE votos SET voto = 'Voto Nulo' WHERE voto = 'Voto em Branco'")
    conn.commit()
    print("Atualização concluída: votos em branco foram alterados para 'Voto Nulo'.")

def gerar_relatorio(cursor):
    senha_correta = "s3nh4s3cr3t4"
    if input("Digite a senha para acessar os relatórios: ") == senha_correta:
        cursor.execute("SELECT voto, turma, COUNT(*) AS total FROM votos GROUP BY voto, turma ORDER BY total DESC")
        votos_por_candidato = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM votos")
        total_votantes = cursor.fetchone()[0]
        print("\nRelatório de Votos (por turma):")
        for candidato, turma, total in votos_por_candidato:
            print(f"Candidato {candidato} (Turma {turma}): {total} votos")
        print(f"\nNúmero total de votantes: {total_votantes} votos")
    else:
        print("Senha incorreta. Acesso negado.")

def contar_votos_turma(turmas, cursor):
    try:
        print("\nResumo de votos por turma:")
        for turma in turmas:
            cursor.execute(f'SELECT COUNT(*) FROM "{turma}"')
            total_alunos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT email) FROM votos WHERE turma = ?", (turma,))
            alunos_que_votaram = cursor.fetchone()[0]
            alunos_faltantes = total_alunos - alunos_que_votaram
            print(f"Turma {turma}:")
            print(f"- Total de alunos: {total_alunos}")
            print(f"- Alunos que já votaram: {alunos_que_votaram}")
            print(f"- Alunos que ainda não votaram: {alunos_faltantes}\n")
    except sqlite3.Error as e:
        print(f"Erro ao contar votos: {e}")

def main():
    turmas = ["1MB", "2MA", "3DS", "3MA", "9MD", "9MC"]
    alunos = {
        "1MB": [("Aluno C", "alunoC@exemplo.com"), ("Aluno D", "alunoD@exemplo.com")],
        "2MA": [("Aluno A", "alunoA@exemplo.com"), ("Aluno B", "alunoB@exemplo.com")],
        "9MD": [("Aluno X", "alunoX@exemplo.com"), ("Aluno Y", "alunoY@exemplo.com")],
        "9MC": [("Aluno Z", "alunoZ@exemplo.com"), ("Aluno W", "alunoW@exemplo.com")]
    }

    conn = sqlite3.connect('sisvoto.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()
    inicializar_bd(cursor, conn, turmas)
    registrar_dados(cursor, conn, alunos)

    while True:
        opcao = input("\nSistema de Votação:\n1 - Votar na turma 1MB\n2 - Votar na turma 2MA\n3 - Votar na turma 3DS\n4 - Votar na turma 3MA\n5 - Votar na turma 9MD\n6 - Votar na turma 9MC\n7 - Gerar relatório de votos\n8 - Atualizar votos\n9 - Contar votos por turma\n10 - Sair\nDigite sua escolha: ")
        if opcao in ['1', '2', '3', '4', '5', '6']:
            processar_voto(turmas[int(opcao) - 1], cursor, conn)
        elif opcao == '7':
            gerar_relatorio(cursor)
        elif opcao == '8':
            alterar_votos(cursor, conn)
        elif opcao == '9':
            contar_votos_turma(turmas, cursor)
        elif opcao == '10':
            print("Encerrando o sistema...")
            break
        else:
            print("Opção inválida. Tente novamente.")
    conn.close()

if __name__ == "__main__":
    main()
