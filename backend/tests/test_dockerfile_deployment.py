"""
Tests for Dockerfile/deployment fix validation:
- Root-level Dockerfile exists and is valid multi-stage build
- render.yaml, .dockerignore, docker-compose.yml exist and are correct
- server.py has StaticFiles import and SPA catch-all route
- Live API health check
"""
import pytest
import requests
import os
import re
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
REPO_ROOT = Path("/app")


# ---- File Existence Tests ----

class TestDockerfileExists:
    """Verify all deployment files exist at correct paths"""

    def test_root_dockerfile_exists(self):
        assert (REPO_ROOT / "Dockerfile").exists(), "Root-level Dockerfile is missing!"

    def test_backend_dockerfile_still_exists(self):
        """Old backend Dockerfile should still exist (no regression)"""
        assert (REPO_ROOT / "backend" / "Dockerfile").exists()

    def test_render_yaml_exists(self):
        assert (REPO_ROOT / "render.yaml").exists(), "render.yaml missing!"

    def test_dockerignore_exists(self):
        assert (REPO_ROOT / ".dockerignore").exists(), ".dockerignore missing!"

    def test_docker_compose_exists(self):
        assert (REPO_ROOT / "docker-compose.yml").exists(), "docker-compose.yml missing!"


# ---- Root Dockerfile Content Tests ----

class TestRootDockerfileContent:
    """Verify root Dockerfile is a valid multi-stage build"""

    @pytest.fixture(autouse=True)
    def read_dockerfile(self):
        self.content = (REPO_ROOT / "Dockerfile").read_text()

    def test_stage1_uses_node18(self):
        assert "FROM node:18-slim" in self.content or "FROM node:18" in self.content, \
            "Stage 1 must use node:18 image"

    def test_stage1_named_frontend_builder(self):
        assert "AS frontend-builder" in self.content, \
            "Stage 1 must be named 'frontend-builder'"

    def test_stage2_uses_python311(self):
        assert "FROM python:3.11-slim" in self.content or "FROM python:3.11" in self.content, \
            "Stage 2 must use python:3.11 image"

    def test_react_app_backend_url_empty(self):
        assert 'REACT_APP_BACKEND_URL=""' in self.content or "REACT_APP_BACKEND_URL=''" in self.content, \
            "REACT_APP_BACKEND_URL must be set to empty string for same-origin /api/* calls"

    def test_cmd_uses_port_env_var(self):
        assert "PORT:-8001" in self.content or "${PORT}" in self.content, \
            "CMD must reference PORT env var"

    def test_cmd_uses_uvicorn(self):
        assert "uvicorn" in self.content, "CMD must use uvicorn"

    def test_cmd_uses_sh_c(self):
        assert 'sh -c' in self.content or '"sh", "-c"' in self.content, \
            "CMD must use sh -c for PORT expansion"

    def test_copies_frontend_build_to_static(self):
        assert "COPY --from=frontend-builder" in self.content, \
            "Stage 2 must copy React build from frontend-builder stage"
        assert "static" in self.content.split("COPY --from=frontend-builder")[1].split("\n")[0], \
            "React build must be copied to static directory"

    def test_runs_yarn_build(self):
        assert "yarn build" in self.content, "Dockerfile must run yarn build for React"

    def test_exposes_port(self):
        assert "EXPOSE" in self.content, "Dockerfile must EXPOSE a port"


# ---- render.yaml Content Tests ----

class TestRenderYaml:
    """Verify render.yaml is correct for Render Docker deployment"""

    @pytest.fixture(autouse=True)
    def read_render_yaml(self):
        self.content = (REPO_ROOT / "render.yaml").read_text()

    def test_dockerfile_path_is_root(self):
        assert "dockerfilePath: ./Dockerfile" in self.content, \
            "render.yaml must point to root Dockerfile"

    def test_docker_context_is_root(self):
        assert "dockerContext: ." in self.content, \
            "render.yaml dockerContext must be '.' (repo root)"

    def test_service_type_is_web(self):
        assert "type: web" in self.content, "render.yaml service type must be 'web'"

    def test_runtime_is_docker(self):
        assert "runtime: docker" in self.content, "render.yaml runtime must be 'docker'"


# ---- docker-compose.yml Content Tests ----

class TestDockerCompose:
    """Verify docker-compose.yml uses root Dockerfile"""

    @pytest.fixture(autouse=True)
    def read_compose(self):
        self.content = (REPO_ROOT / "docker-compose.yml").read_text()

    def test_uses_root_context(self):
        assert "context: ." in self.content, \
            "docker-compose.yml must use root context '.'"

    def test_uses_root_dockerfile(self):
        assert "dockerfile: Dockerfile" in self.content, \
            "docker-compose.yml must reference root Dockerfile"

    def test_port_env_var_set(self):
        assert "PORT=" in self.content, "docker-compose.yml must set PORT env var"


# ---- server.py Static Files Tests ----

class TestServerPyStaticFiles:
    """Verify server.py has correct static file serving for production"""

    @pytest.fixture(autouse=True)
    def read_server(self):
        self.content = (REPO_ROOT / "backend" / "server.py").read_text()

    def test_staticfiles_imported(self):
        assert "StaticFiles" in self.content, "StaticFiles must be imported in server.py"

    def test_fileresponse_imported(self):
        assert "FileResponse" in self.content, "FileResponse must be imported in server.py"

    def test_static_build_dir_defined(self):
        assert "STATIC_BUILD_DIR" in self.content, \
            "STATIC_BUILD_DIR variable must be defined in server.py"

    def test_static_dir_uses_static_folder(self):
        # Should reference "static" directory
        assert '"static"' in self.content or "'static'" in self.content or \
               '/ "static"' in self.content or "/ 'static'" in self.content, \
            "server.py must reference 'static' directory for build output"

    def test_spa_catchall_route_exists(self):
        assert "full_path:path" in self.content, \
            "SPA catch-all route @app.get('/{full_path:path}') must exist"

    def test_spa_returns_index_html(self):
        assert "index.html" in self.content, \
            "Catch-all route must return index.html"

    def test_conditional_mount_exists(self):
        """Ensure static files only mounted if directory exists (dev-safe)"""
        assert "STATIC_BUILD_DIR.exists()" in self.content, \
            "Static mount must be conditional on directory existing"


# ---- Live API Tests ----

class TestLiveAPI:
    """Verify live API is operational"""

    def test_health_endpoint_returns_ok(self):
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok", f"Health status not 'ok': {data}"

    def test_health_database_connected(self):
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("database") == "connected", f"Database not connected: {data}"

    def test_health_response_structure(self):
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "version" in data
        assert "storage_mode" in data

    def test_courses_endpoint_accessible(self):
        response = requests.get(f"{BASE_URL}/api/courses", timeout=10)
        assert response.status_code == 200

    def test_frontend_root_accessible(self):
        """Root path should return HTTP 200"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200
