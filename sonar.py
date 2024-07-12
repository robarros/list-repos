import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Configurações do SonarQube
SONARQUBE_URL = os.getenv('SONARQUBE_URL')
SONARQUBE_USERNAME = os.getenv('SONARQUBE_USERNAME')
SONARQUBE_PASSWORD = os.getenv('SONARQUBE_PASSWORD')

@app.route('/projects', methods=['GET'])
def list_projects():
    try:
        response = requests.get(
            f"{SONARQUBE_URL}/api/projects/search",
            auth=(SONARQUBE_USERNAME, SONARQUBE_PASSWORD),
            verify=False
        )
        response.raise_for_status()  # Verifica se a requisição teve sucesso
        projects_data = response.json()
        
        # Extraindo os nomes dos projetos
        projects = []
        if 'components' in projects_data:
            projects = [{'name': project['name'], 'key': project['key']} for project in projects_data['components']]
            
        return jsonify(projects)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
