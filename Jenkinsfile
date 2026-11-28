
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME = "quiz-devops-dev"
        CONTAINER_NAME = "quiz-devops-dev-${BUILD_NUMBER}"
        APP_PORT = "5001"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                bat 'git rev-parse HEAD > commit.txt'
            }
        }

        stage('Setup & Verify') {
            steps {
                bat 'python --version'
                bat 'python -m py_compile app.py'
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker --version'
                bat 'docker build -t %IMAGE_NAME%:%BUILD_NUMBER% .'
            }
        }

        stage('Run Container') {
            steps {
                bat '''
                    docker rm -f %CONTAINER_NAME% 2>NUL
                    docker run -d --name %CONTAINER_NAME% -p %APP_PORT%:5000 %IMAGE_NAME%:%BUILD_NUMBER%
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                bat '''
                powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok=$false; for($i=0;$i -lt 30;$i++){ try { $r=Invoke-WebRequest -Uri 'http://localhost:%APP_PORT%/health' -TimeoutSec 3; if($r.StatusCode -eq 200){$ok=$true; 'Health check OK (HTTP 200)' | Out-File -FilePath smoke-result.txt; break } } catch { Start-Sleep -Seconds 2 } }; if(-not $ok){ 'Health check FAILED' | Out-File -FilePath smoke-result.txt; exit 1 }"
                '''
            }
        }

        stage('Archive Artifacts') {
            steps {
                bat 'docker logs %CONTAINER_NAME% > container.log 2>&1'
                archiveArtifacts artifacts: 'commit.txt,smoke-result.txt,container.log', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            bat '''
                docker rm -f %CONTAINER_NAME% 2>NUL
                docker image rm %IMAGE_NAME%:%BUILD_NUMBER% 2>NUL
                exit /b 0
            '''
        }
    }
}
