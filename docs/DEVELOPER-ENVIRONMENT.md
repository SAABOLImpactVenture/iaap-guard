# Portable Developer Environment

IaaP Guard includes a repository-defined development container so the same working environment can be used from GitHub Codespaces or from local VS Code with Dev Containers and Docker Desktop.

## What the environment provides

The dev container uses Python 3.12 and installs:

- repository application and CI dependencies;
- GNU `make`;
- GitHub CLI (`gh`);
- AWS CLI;
- AWS SAM CLI;
- Docker-in-Docker with Docker Compose v2;
- VS Code support for Python, YAML, GitHub Actions, Docker, and AWS tooling.

After creation, `.devcontainer/post-create.sh` installs Python dependencies and runs `make validate` so a newly created environment starts from a validated repository state.

## GitHub Codespaces

Create a Codespace from the repository and allow the `.devcontainer/devcontainer.json` configuration to build. The Codespace is independent of any Docker installation, Python installation, or AWS credential files on the device used to open it.

Use the terminal to confirm the environment:

```bash
bash .devcontainer/verify-toolchain.sh
```

A Codespace can be opened from a desktop browser, mobile browser, or VS Code while retaining the same repository-defined tooling.

## Local VS Code and Docker Desktop

On a workstation with Docker Desktop and the VS Code Dev Containers extension installed, open the repository and choose **Reopen in Container**. The same `.devcontainer/devcontainer.json` definition is used locally.

The local Docker Desktop installation is therefore useful, but it is no longer a prerequisite for development when Codespaces is available.

## AWS authentication boundary

AWS credentials are deliberately **not** stored in the dev-container definition and should never be committed to the repository.

The presence of the AWS CLI and SAM CLI does not grant AWS access. Interactive development or deployment still requires approved short-lived authentication, such as AWS IAM Identity Center/SSO or another organization-approved mechanism.

To test whether an authenticated session is already available, use:

```bash
aws sts get-caller-identity
```

Do not print, copy, or commit the contents of AWS credential files.

For automated deployment, the preferred future model is GitHub Actions using AWS workload identity/OIDC rather than long-lived developer credentials.

## Docker boundary

Codespaces uses Docker-in-Docker inside the development container. It does not connect to or inherit containers, images, volumes, or credentials from Docker Desktop on a personal workstation.

Local VS Code may use Docker Desktop to host the same dev-container definition, but repository behavior should not depend on workstation-specific Docker state.

## Validation

The `Dev container portability` workflow builds the repository dev container and runs `.devcontainer/verify-toolchain.sh`. This verifies the toolchain and executes the deterministic repository validation suite.

An actual interactive Codespace launch remains the final usability proof; a successful CI build proves the container definition can be built and validated, not that every browser/mobile interaction has been exercised.

## Local state excluded from Git

The repository `.gitignore` excludes common Python caches, virtual environments, local environment files, AWS/SAM working directories, and other workstation-specific state. Secrets and credential material must remain outside version control.
