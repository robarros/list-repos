import os
import boto3
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import requests

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar o cliente boto3 para o CodePipeline
client = boto3.client(
    'codepipeline',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

########### ASSUME ROLE ###########
# Função para assumir a role e criar uma sessão boto3
# def assume_role(role_arn):
#     sts_client = boto3.client('sts')
#     assumed_role_object = sts_client.assume_role(
#         RoleArn=role_arn,
#         RoleSessionName="AssumeRoleSession1"
#     )
#     credentials = assumed_role_object['Credentials']
#     return boto3.client(
#         'codecommit',
#         aws_access_key_id=credentials['AccessKeyId'],
#         aws_secret_access_key=credentials['SecretAccessKey'],
#         aws_session_token=credentials['SessionToken'],
#         region_name=os.getenv('AWS_REGION')
#     )

# # Inicializar o cliente boto3 assumindo a role
# role_arn = os.getenv('AWS_ROLE_ARN')
# client = assume_role(role_arn)
###########



# URL e Token do GitHub a partir das variáveis de ambiente
GITHUB_URL = os.getenv('GITHUB_URL')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_PER_PAGE = int(os.getenv('GITHUB_PER_PAGE', 100))  # Valor padrão de 100 se não estiver definido
GITHUB_PAGE = int(os.getenv('GITHUB_PAGE', 1))            # Valor padrão de 1 se não estiver definido

# URL, usuário e token do Jenkins a partir das variáveis de ambiente
JENKINS_URL = os.getenv('JENKINS_URL')
JENKINS_USER = os.getenv('JENKINS_USER')
JENKINS_TOKEN = os.getenv('JENKINS_TOKEN')

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

# Rota para obter a lista de repositórios do GitHub
@app.route('/github', methods=['GET'])
def get_github_repos():
    try:
        per_page = request.args.get('per_page', GITHUB_PER_PAGE)
        page = request.args.get('page', GITHUB_PAGE)
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        params = {
            'per_page': per_page,
            'page': page
        }
        response = requests.get(f'{GITHUB_URL}', headers=headers, params=params)
        repos = [repo['name'] for repo in response.json()]
        return jsonify(repos), 200
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar repositórios do GitHub: {e}"}), 500

# Rota para obter o total de repositórios do GitHub
@app.route('/github/total', methods=['GET'])
def get_total_github_repos():
    try:
        per_page = request.args.get('per_page', GITHUB_PER_PAGE)
        page = request.args.get('page', GITHUB_PAGE)
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        params = {
            'per_page': per_page,
            'page': page
        }
        response = requests.get(f'{GITHUB_URL}', headers=headers, params=params)
        total_repos = len(response.json())
        return jsonify({'total_repositorios': total_repos}), 200
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar total de repositórios do GitHub: {e}"}), 500

# Rota para obter a lista de pipelines do Jenkins
@app.route('/jenkins', methods=['GET'])
def list_pipelines():
    try:
        response = requests.get(f'{JENKINS_URL}/api/json', auth=(JENKINS_USER, JENKINS_TOKEN))
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
        response = requests.get(f'{JENKINS_URL}/api/json', auth=(JENKINS_USER, JENKINS_TOKEN))
        if response.status_code == 200:
            data = response.json()
            total = len(data['jobs'])
            return jsonify({'total_pipelines': total}), 200
        else:
            return jsonify({'error': 'Falha ao buscar total de pipelines do Jenkins'}), response.status_code
    except Exception as e:
        return jsonify({'error': f"Erro ao buscar total de pipelines do Jenkins: {e}"}), 500

# Rota de healthcheck
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'ok'}), 200

# Iniciar o servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)

