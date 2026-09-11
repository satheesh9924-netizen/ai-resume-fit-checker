pipeline {
    agent any
    environment {
        COMPOSE_PROJECT_NAME = "ai-resume-fit-checker-${env.BUILD_NUMBER}"
    }
    triggers {
        githubPush()
        pollSCM('H/2 * * * *')
    }
    stages {
        stage('Checkout') {
            steps { checkout scm }
        }
        stage('Verify Docker Environment') {
            steps {
                sh '''
                    command -v docker >/dev/null 2>&1 || { echo "ERROR: docker CLI not found on this agent. Install Docker and ensure the Jenkins user can reach /var/run/docker.sock."; exit 1; }
                    docker version >/dev/null 2>&1 || { echo "ERROR: docker CLI found but cannot reach the daemon. Add the Jenkins user to the 'docker' group (or grant socket access) and restart the agent."; exit 1; }
                    docker compose version >/dev/null 2>&1 || { echo "ERROR: 'docker compose' (Compose v2 plugin) not available. Install the Docker Compose plugin -- the legacy docker-compose v1 binary will not work here."; exit 1; }
                '''
            }
        }
        stage('Build & Run Tests (Docker)') {
            steps {
                sh 'rm -rf target && mkdir -p target'
                sh 'docker compose build playwright-tests'
                sh 'docker compose run --rm playwright-tests'
            }
        }
        stage('Resume/JD Matcher AI Tests') {
            steps {
                withCredentials([string(credentialsId: 'abacus-api-key', variable: 'ABACUS_API_KEY')]) {
                    sh 'rm -rf resume-matcher/target && mkdir -p resume-matcher/target'
                    sh 'docker compose build resume-matcher-tests'
                    sh 'docker compose run --rm resume-matcher-tests'
                }
            }
        }
        stage('AI Failure Triage') {
            steps {
                withCredentials([string(credentialsId: 'abacus-api-key', variable: 'ABACUS_API_KEY')]) {
                    sh 'rm -rf ai-triage/target && mkdir -p ai-triage/target'
                    sh 'docker compose build ai-triage-tests ai-triage-run'
                    sh 'docker compose run --rm ai-triage-tests'
                    sh 'docker compose run --rm ai-triage-run'
                }
            }
        }
    }
    post {
        always {
            sh '''
                docker run --rm \
                    -v "$(pwd)/target:/target" \
                    -v "$(pwd)/resume-matcher/target:/resume-matcher-target" \
                    -v "$(pwd)/ai-triage/target:/ai-triage-target" \
                    alpine chown -R "$(id -u):$(id -g)" /target /resume-matcher-target /ai-triage-target || true
            '''
            sh 'docker compose down --volumes --remove-orphans || true'
            junit testResults: '**/target/surefire-reports/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'target/screenshots/*.png, target/traces/*.zip, target/surefire-reports/**, resume-matcher/target/surefire-reports/**, ai-triage/target/surefire-reports/**, ai-triage/target/triage-report.md', allowEmptyArchive: true
            step([$class: 'AllureReportPublisher', includeProperties: false, jdk: '', results: [
                [path: 'target/allure-results'],
                [path: 'resume-matcher/target/allure-results'],
                [path: 'ai-triage/target/allure-results']
            ]])
        }
    }
}
