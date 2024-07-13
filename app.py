import os
import boto3
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import requests
import threading
from requests.auth import HTTPBasicAuth


# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# def assume_role(role_arn):
#     sts_client = boto3.client('sts')
#     assumed_role_object = sts_client.assume_role(
#         RoleArn=role_arn,
#         RoleSessionName="AssumeRoleSession"
#     )
#     credentials = assumed_role_object['Credentials']
#     return boto3.client(
#         'codepipeline',
#         aws_access_key_id=credentials['AccessKeyId'],
#         aws_secret_access_key=credentials['SecretAccessKey'],
#         aws_session_token=credentials['SessionToken'],
#         region_name=os.getenv('AWS_REGION')
#     )

# # Assumir a role usando a variável de ambiente AWS_ROLE_ARN
# role_arn = os.getenv('AWS_ROLE_ARN')
# client = assume_role(role_arn)

# URL e Token do GitHub a partir das variáveis de ambiente
GITHUB_URL = os.getenv('GITHUB_URL')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_PER_PAGE = int(os.getenv('GITHUB_PER_PAGE', 100))  # Valor padrão de 100 se não estiver definido

# URL, usuário e token do Jenkins a partir das variáveis de ambiente
JENKINS_URL = os.getenv('JENKINS_URL')
JENKINS_USER = os.getenv('JENKINS_USER')
JENKINS_TOKEN = os.getenv('JENKINS_TOKEN')

# URL e Token do SONARQUBE a partir das variáveis de ambiente
SONARQUBE_URL = os.getenv('SONARQUBE_URL')
SONARQUBE_TOKEN = os.getenv('SONARQUBE_TOKEN')

# Inicializar o Flask
app = Flask(__name__)

# Rota para listar todos os pipelines no CodePipeline
@app.route('/codepipeline', methods=['GET'])
def get_pipeline_list():
    try:
        response = client.list_pipelines()
        pipeline_list = [pipeline['name'] for pipeline in response['pipelines']]
        return jsonify({'pipelines': pipeline_list}), 200
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar pipelines: {e}"}), 500

# Rota para obter o total de repositórios do CodePipeline
@app.route('/codepipeline/total', methods=['GET'])
def get_pipeline_count():
    try:
        response = client.list_pipelines()
        pipeline_count = len(response['pipelines'])
        return jsonify({'total_pipelines': pipeline_count}), 200
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar pipelines: {e}"}), 500

# Função para obter todos os repositórios do GitHub usando threads para paginar
def fetch_all_github_repos():
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    repos = []
    threads = []
    page = 1

    def fetch_page(page):
        params = {
            'per_page': GITHUB_PER_PAGE,
            'page': page
        }
        response = requests.get(f'{GITHUB_URL}', headers=headers, params=params)
        if response.status_code != 200:
            raise Exception(f"Erro ao buscar repositórios do GitHub: {response.status_code}")
        data = response.json()
        repos.extend([repo['name'] for repo in data])

    # Estimar o número de páginas com base em uma consulta inicial
    initial_response = requests.get(f'{GITHUB_URL}', headers=headers, params={'per_page': 1})
    total_repos = int(initial_response.headers.get('X-Total-Count', 0))
    total_pages = (total_repos // GITHUB_PER_PAGE) + 1

    for page in range(1, total_pages + 1):
        thread = threading.Thread(target=fetch_page, args=(page,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return repos

# Rota para obter a lista de repositórios do GitHub
@app.route('/github', methods=['GET'])
def get_github_repos():
    try:
        repos = fetch_all_github_repos()
        return jsonify(repos), 200
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar repositórios do GitHub: {e}"}), 500

# Rota para obter o total de repositórios do GitHub
@app.route('/github/total', methods=['GET'])
def get_total_github_repos():
    try:
        repos = fetch_all_github_repos()
        total_repos = len(repos)
        return jsonify({'total_repositorios': total_repos}), 200
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar total de repositórios do GitHub: {e}"}), 500

# Rota para obter a lista de pipelines do Jenkins
@app.route('/jenkins', methods=['GET'])
def list_pipelines():
    try:
        response = requests.get(f'{JENKINS_URL}/api/json', auth=(JENKINS_USER, JENKINS_TOKEN), verify=False)
        if response.status_code == 200:
            data = response.json()
            pipeline_names = [job['name'] for job in data['jobs']]
            return jsonify(pipeline_names), 200
        else:
            return jsonify({'error': 'Falha ao buscar pipelines do Jenkins'}), response.status_code
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar pipelines do Jenkins: {e}"}), 500

# Rota para obter o total de pipelines do Jenkins
@app.route('/jenkins/total', methods=['GET'])
def total_pipelines():
    try:
        response = requests.get(f'{JENKINS_URL}/api/json', auth=(JENKINS_USER, JENKINS_TOKEN), verify=False)
        if response.status_code == 200:
            data = response.json()
            total = len(data['jobs'])
            return jsonify({'total_pipelines': total}), 200
        else:
            return jsonify({'error': 'Falha ao buscar total de pipelines do Jenkins'}), response.status_code
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar total de pipelines do Jenkins: {e}"}), 500

def get_coverage(project_key):
    url = f"{SONARQUBE_URL}/api/measures/component"
    params = {
        'component': project_key,
        'metricKeys': 'coverage'
    }
    response = requests.get(url, auth=HTTPBasicAuth(SONARQUBE_TOKEN, ''), verify=False)
    if response.status_code == 200:
        dados = response.json()
        measures = dados.get('component', {}).get('measures', [])
        for measure in measures:
            if measure['metric'] == 'coverage':
                return measure['value']
    return 'N/A'

@app.route('/sonarqube', methods=['GET'])
def listar_projetos():
    url = f"{SONARQUBE_URL}/api/projects/search"
    response = requests.get(url, auth=HTTPBasicAuth(SONARQUBE_TOKEN, ''), verify=False)
    
    if response.status_code == 200:
        dados = response.json()
        projetos = dados.get('components', [])
        projetos_info = []
        for projeto in projetos:
            nome_projeto = projeto['name']
            key_projeto = projeto['key']
            coverage = get_coverage(key_projeto)
            projetos_info.append({
                'nome': nome_projeto,
                'coverage': coverage
            })
        # Ordena os projetos pelo nome
        projetos_info.sort(key=lambda x: x['nome'])
        return jsonify(projetos_info), 200
    else:
        return jsonify({"erro": "Não foi possível acessar o SonarQube"}), response.status_code

@app.route('/sonarqube/total', methods=['GET'])
def contar_projetos():
    url = f"{SONARQUBE_URL}/api/projects/search"
    response = requests.get(url, auth=HTTPBasicAuth(SONARQUBE_TOKEN, ''), verify=False)
    
    if response.status_code == 200:
        dados = response.json()
        total_projetos = dados.get('paging', {}).get('total', 0)
        return jsonify({"total": total_projetos}), 200
    else:
        return jsonify({"erro": "Não foi possível acessar o SonarQube"}), response.status_code

# Rota de healthcheck
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'ok'}), 200

# Iniciar o servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
