import click
import tempfile
import os
import paramiko
from halo import Halo
from app.constants import STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY
from azure.storage.blob import BlobServiceClient


def check_elastic_agent_status(ssh_client):
    try:
        command = "sudo systemctl status elastic-agent"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        stdout.channel.recv_exit_status()
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        click.echo(f"Elastic Agent status output: {output}")
        click.echo(f"Elastic Agent status error: {error}")

        if "could not be found" in error:
            return "not_found"
        elif "inactive" in output or "failed" in output:
            return "inactive"
        elif "active (running)" in output:
            return "active"
        else:
            return "unknown"
    except Exception as e:
        raise RuntimeError(f"Failed to check Elastic Agent status: {e}")


def copy_http_ca_to_vm(
    vm_ip, os_type, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY, vm_username, vm_password
):
    try:
        blob_service_client = BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
            credential=STORAGE_ACCOUNT_KEY,
        )

        container_name = "secrets-elk"
        blob_name = "http_ca.crt"

        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )
        target_path = f"/home/{vm_username}/http_ca.crt"

        # Create a temporary file to store the downloaded blob
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            local_path = temp_file.name

        with Halo(
            text=click.style("Downloading http_ca.crt...", fg="green"), spinner="dots"
        ):
            with open(local_path, "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())
            click.echo(f"File downloaded successfully to {local_path}")

        with Halo(
            text=click.style("Copying http_ca.crt to VM...", fg="green"), spinner="dots"
        ):
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(vm_ip, username=vm_username, password=vm_password)
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(local_path, target_path)
            sftp_client.close()
            click.echo("File copied to target machine successfully.")

        # Clean up temporary file
        os.remove(local_path)

    except Exception as e:
        click.echo(f"Failed to copy file: {e}")
        raise RuntimeError(f"Failed to copy file: {e}")


def install_elastic_agent(ssh_client, username):
    try:
        commands = [
            "curl -L -O https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.14.1-linux-x86_64.tar.gz",
            "tar xzvf elastic-agent-8.14.1-linux-x86_64.tar.gz",
            f"cd elastic-agent-8.14.1-linux-x86_64 && echo 'Y' | sudo ./elastic-agent install --url=https://10.53.2.11:8220 --enrollment-token=c2pzbWVKQUI5WHZkQlluMVJlTVY6eHA4YTRCclFTVW05Nk94dmhhdFhEZw== --certificate-authorities=/home/{username}/http_ca.crt",
        ]

        with Halo(
            text=click.style("Installing Elastic Agent...", fg="green"), spinner="dots"
        ):
            for command in commands:
                stdin, stdout, stderr = ssh_client.exec_command(command)
                stdout.channel.recv_exit_status()
                output = stdout.read().decode("utf-8")
                error = stderr.read().decode("utf-8")
                click.echo(f"Command: {command}\nOutput: {output}\nError: {error}")

        click.echo("Elastic Agent installed successfully.")

    except Exception as e:
        raise RuntimeError(f"Error installing Elastic Agent: {e}")


def restart_elastic_agent(ssh_client):
    try:
        command = "sudo systemctl restart elastic-agent"
        with Halo(
            text=click.style("Restarting Elastic Agent...", fg="green"), spinner="dots"
        ):
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            click.echo(f"Output: {output}\nError: {error}")

        click.echo("Elastic Agent restarted successfully.")

    except Exception as e:
        raise RuntimeError(f"Error restarting Elastic Agent: {e}")


def uninstall_elastic_agent(ssh_client):
    try:
        command = "sudo /opt/Elastic/Agent/elastic-agent uninstall"

        with Halo(text="Uninstalling Elastic Agent...", spinner="dots"):
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            click.echo(f"Command: {command}\nOutput: {output}\nError: {error}")

        click.echo("Elastic Agent uninstalled successfully.")

    except Exception as e:
        raise RuntimeError(f"Error uninstalling Elastic Agent: {e}")
