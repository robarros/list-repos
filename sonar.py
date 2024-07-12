from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Configurações do SonarQube
SONARQUBE_URL = "http://seu-sonarqube-url"
SONARQUBE_API_TOKEN = "seu-token-aqui"

@app.route('/projects', methods=['GET'])
def list_projects():
    try:
        response = requests.get(
            f"{SONARQUBE_URL}/api/projects/search",
            auth=(SONARQUBE_API_TOKEN, ''),
            verify=False
        )
        response.raise_for_status()  # Verifica se a requisição teve sucesso
        projects = response.json()
        return jsonify(projects)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
