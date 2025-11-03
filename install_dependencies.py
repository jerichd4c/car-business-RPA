import subprocess
import sys
import os


def run_command(command: str) -> bool:
    """Run a shell command and print it; return True on success, False on failure."""
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(command)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando {command}: {e.stderr}")
        return False


def install_requirements() -> None:
    """Install dependencies from requirements.txt if present; fallback to a basic list."""
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        print("\nInstalando dependencias desde requirements.txt...")
        run_command(f"{sys.executable} -m pip install -r {req_file}")
    else:
        print("\nrequirements.txt no encontrado. Instalando lista básica de dependencias...")
        dependencies = [
            "pandas==1.5.3",
            # use >=3.1.0 for compatibility with pandas when reading Excel files
            "openpyxl>=3.1.0",
            "matplotlib==3.6.2",
            "twilio==7.16.0",
            "fpdf2==2.7.4",
            "python-dotenv==0.21.0",
            "requests==2.28.2",
            "selenium==4.15.0",
            "pywhatkit==5.4",
            "webdriver-manager==4.0.1",
            "schedule==1.2.0",
        ]
        for dep in dependencies:
            run_command(f"{sys.executable} -m pip install {dep}")


def configure_chromedriver() -> None:
    """Install ChromeDriver via webdriver-manager and write its path into .env."""
    print("\nConfigurando Chrome Driver...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        # from selenium import webdriver  # not actually used here

        driver_path = ChromeDriverManager().install()
        print(f"Chrome Driver instalado en: {driver_path}")

        # update .env file
        env_path = ".env"
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updated = False
        for i, line in enumerate(lines):
            if line.startswith("CHROME_DRIVER_PATH="):
                lines[i] = f"CHROME_DRIVER_PATH={driver_path}\n"
                updated = True
                break

        if not updated:
            lines.append(f"CHROME_DRIVER_PATH={driver_path}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        print("✅ Ruta de ChromeDriver actualizada en .env")

    except Exception as e:
        print(f"Error configurando Chrome Driver: {e}")


def main():
    print("Instalando dependencias...")
    print("=" * 50)

    # update pip first
    print("\nActualizando pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip")

    # install dependencies from requirements.txt (preferred)
    install_requirements()

    # install and configure ChromeDriver
    configure_chromedriver()

    print("\nInstalación de dependencias completada.")


if __name__ == "__main__":
    main()
