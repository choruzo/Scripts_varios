import paramiko
import os
import sys
import time
import getpass
import requests
import re
import datetime # Importar el módulo datetime

# --- Configuration ---
# Define una lista de tus hosts ESXi
ESXI_HOSTS = [
    'ip_hosts_esxi',  # <--- Reemplaza con la IP o hostname de tu host ESXi
    'ip_hosts_esxi_2', # <--- Agrega tus otros hosts aquí
    'ip_hosts_esxi_3',  # <--- Y así sucesivamente
]
ESXI_USER = 'root'                      # <--- Usuario para SSH (generalmente root)
LOCAL_DOWNLOAD_DIR = '.'                # <--- Directorio local para guardar las copias de seguridad
ESXI_SSH_PORT = 22                      # <--- Puerto SSH (predeterminado)

# --- Function to download the backup ---
# --- Function to download the backup ---
def download_esxi_backup_http(hostname, port, username, password, local_dir):
    """
    Connects to ESXi via SSH, runs the backup command, extracts the HTTP link,
    and downloads the file via HTTP into the specified local_dir.
    """
    print(f"\n--- Procesando host: {hostname} ---")

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Conectando a {hostname}...")
    try:
        ssh_client.connect(hostname, port=port, username=username, password=password, timeout=10)
        print("Conexión SSH establecida.")
    except paramiko.AuthenticationException:
        print("Error: Autenticación fallida. Revisa el usuario y la contraseña para este host.")
        # Close connection if it was partially opened before failure
        if ssh_client and ssh_client.get_transport() is not None:
             ssh_client.close()
        return False
    except paramiko.SSHException as ssh_err:
        print(f"Error SSH: {ssh_err}")
        if ssh_client and ssh_client.get_transport() is not None:
             ssh_client.close()
        return False
    except Exception as e:
        print(f"Error de conexión: {e}")
        if ssh_client and ssh_client.get_transport() is not None:
             ssh_client.close()
        return False

    http_download_url = None
    try:
        # --- Execute the backup command ---
        backup_command = "vim-cmd hostsvc/firmware/backup_config"
        print(f"Ejecutando comando: {backup_command}")
        try:
            stdin, stdout, stderr = ssh_client.exec_command(backup_command)

            # Give the command a moment to potentially produce output/errors
            time.sleep(2)
            # Read all output and errors
            output_lines = stdout.readlines()
            errors_lines = stderr.readlines()

            output = "".join(output_lines).strip()
            errors = "".join(errors_lines).strip()

            if errors:
                print(f"Advertencia/Error de ejecución del comando en ESXi:\n{errors}")

            if not output:
                 print("El comando se ejecutó, pero no se recibió salida.")
                 print("Asegúrate de que SSH esté habilitado y el comando se ejecute correctamente manualmente.")
                 return False

            print(f"Salida bruta del comando:\n---\n{output}\n---")

            # --- Parse the output to find the HTTP URL ---
            for line in output_lines:
                 match = re.search(r'Bundle can be downloaded at : (https?://.*?)\s*$', line.strip())
                 if match:
                      # The URL might contain '*' for the hostname, replace with actual hostname
                      http_download_url = match.group(1).replace('http://*/', f'http://{hostname}/')
                      http_download_url = http_download_url.replace('https://*/', f'https://{hostname}/') # Also handle https
                      break

            if http_download_url:
                print(f"URL de descarga detectada: {http_download_url}")
            else:
                 print("No se pudo encontrar la URL de descarga en la salida del comando.")
                 print("La salida no coincidió con el formato esperado 'Bundle can be downloaded at : <URL>'")
                 return False

        except Exception as e:
            print(f"Error al ejecutar el comando o analizar la salida: {e}")
            return False

        finally:
             # Close the SSH session after command execution
             if ssh_client and ssh_client.get_transport() is not None and ssh_client.get_transport().is_active():
                 ssh_client.close()
                 print("Conexión SSH cerrada.")


        # --- Download the backup file using HTTP/HTTPS ---
        if not http_download_url:
             print("No se identificó URL de descarga. No se puede proceder con la descarga HTTP.")
             return False

        try:
            print(f"Descargando copia de seguridad desde URL: {http_download_url}")

            # Determine local file path and generate unique name
            url_path = requests.utils.urlparse(http_download_url).path
            remote_filename = os.path.basename(url_path)

            # Generate unique filename: hostname-YYYYMMDD_HHMMSS.ext
            timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            # Use the hostname or IP, replace dots/colons with underscores for filename compatibility
            safe_hostname = hostname.replace('.', '_').replace(':', '_')
            base_name, ext = os.path.splitext(remote_filename) # Get original extension
            new_local_filename = f"{safe_hostname}-{timestamp_str}{ext}"

            # local_dir is now the date-stamped folder
            local_backup_path = os.path.join(local_dir, new_local_filename)


            # Use requests to download the file
            with requests.get(http_download_url, stream=True, verify=False) as r: # verify=False bypasses SSL cert check (use with caution)
                r.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

                total_size_in_bytes = int(r.headers.get('content-length', 0))
                block_size = 8192 # 8KB chunks
                # downloaded_size = 0 # Optional: for progress tracking

                print(f"Iniciando descarga a {local_backup_path}...")
                with open(local_backup_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            # downloaded_size += len(chunk) # Optional: for progress tracking
                            # sys.stdout.write(f"Descargado: {downloaded_size}/{total_size_in_bytes} bytes\r")
                            # sys.stdout.flush()

                # sys.stdout.write("\n") # Ensure newline after progress


            print("Descarga completa.")
            return True # Success

        except requests.exceptions.RequestException as req_err:
            print(f"Error de descarga HTTP: {req_err}")
            print("Verifica si la interfaz web de ESXi es accesible desde esta máquina.")
            print("Si usas HTTPS, puede que necesites configurar la verificación SSL o usar verify=False (usado aquí).")
            return False
        except Exception as e:
            print(f"Error durante la descarga HTTP: {e}")
            return False

    finally:
        # This finally block is inside the try block for command execution/parsing,
        # so it only cleans up if SSH connection was successfully made.
        pass # SSH cleanup moved before HTTP download


# --- Main execution ---
if __name__ == "__main__":
    if not ESXI_HOSTS:
        print("Error: No hay hosts ESXi configurados en la lista ESXI_HOSTS.")
        sys.exit(1)

    # 1. Get the current working directory
    current_dir = os.getcwd()
    print("")
    print(" -- Habilita ssh si no lo esta en los servidores de ESXi -- ")
    print("")
    print(f"Directorio actual de ejecución: {current_dir}")

    # 2. Create the date-stamped directory name (YYYYMMDD)
    today_date_str = datetime.date.today().strftime('%Y%m%d')
    backup_directory_path = os.path.join(current_dir, today_date_str)

    # 3. Create the directory if it doesn't exist
    if not os.path.exists(backup_directory_path):
        print(f"Creando directorio de copia de seguridad: {backup_directory_path}")
        try:
            os.makedirs(backup_directory_path)
        except Exception as e:
            print(f"Error al crear el directorio '{backup_directory_path}': {e}")
            sys.exit(1)
    else:
        print(f"El directorio '{backup_directory_path}' ya existe. Las copias de seguridad se guardarán allí.")

    # Get password once for all hosts
    esxi_password = getpass.getpass(f"Introduce la contraseña para {ESXI_USER} en los hosts ESXi: ")

    successful_backups = []
    failed_hosts = []

    # 4. Loop through hosts and call the download function, passing the new directory path
    for host in ESXI_HOSTS:
        # Pass the newly created date-stamped directory path to the function
        if download_esxi_backup_http(host, ESXI_SSH_PORT, ESXI_USER, esxi_password, backup_directory_path):
            successful_backups.append(host)
        else:
            failed_hosts.append(host)

    print("\n--- Resumen del proceso ---")
    if successful_backups:
        print("Copias de seguridad exitosas para los hosts:")
        for host in successful_backups:
            print(f"- {host}")
    if failed_hosts:
        print("Falló la copia de seguridad para los hosts:")
        for host in failed_hosts:
            print(f"- {host}")
    if not successful_backups and not failed_hosts:
         print("No se procesó ningún host.")

    print("--- Fin del proceso ---")