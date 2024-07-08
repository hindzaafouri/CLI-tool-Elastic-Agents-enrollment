import click
import time
import paramiko
from halo import Halo
from azure.storage.blob import BlobServiceClient
from app.constants import STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY

def copy_http_ca_to_vm(vm_ip, os_type):
    try:
        blob_service_client = BlobServiceClient(
            account_url=f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
            credential=STORAGE_ACCOUNT_KEY
        )

        if os_type.lower() == "linux":
            container_name = "secrets-elk"
            blob_name = "http_ca.crt"

            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            with open("/tmp/http_ca.crt", "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())

            click.echo("File downloaded successfully to /tmp/http_ca.crt")

            click.echo("Waiting for 5 seconds...")
            with Halo(text='Copying file to VM...', spinner='dots'):
                time.sleep(5)

            # Prompt user for username and password
            username = click.prompt("Enter VM username")
            password = click.prompt("Enter VM password", hide_input=True)

            with Halo(text='Connecting to VM...', spinner='dots'):
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(vm_ip, username=username, password=password)

                sftp_client = ssh_client.open_sftp()
                sftp_client.put('/tmp/http_ca.crt', '/tmp/http_ca.crt')
                sftp_client.close()

                click.echo("File copied to target machine successfully.")

                # Check and handle Elastic Agent status
                handle_elastic_agent_status(ssh_client, username)

                ssh_client.close()

        elif os_type.lower() == "windows":
            click.echo("Windows OS detected. Handle Windows logic here.")
        else:
            raise click.ClickException(f"Unsupported OS type '{os_type}'. Cannot proceed.")

    except Exception as e:
        raise click.ClickException(f"Failed to copy file and install Elastic Agent: {e}")

def handle_elastic_agent_status(ssh_client, username):
    try:
        # Command to check Elastic Agent status
        command = "sudo systemctl status elastic-agent"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')

        click.echo("Elastic Agent status check output:")
        click.echo(output)
        if error:
            click.echo("Elastic Agent status check error:")
            click.echo(error)

        if "could not be found" in error:
            click.echo("Elastic Agent not found. Installing Elastic Agent...")
            install_elastic_agent(ssh_client, username)
        elif "inactive" in output or "failed" in output:
            click.echo("Elastic Agent is inactive or failed. Restarting Elastic Agent...")
            restart_elastic_agent(ssh_client)
        elif "active (running)" in output:
            click.echo("Elastic Agent is installed and running. The machine is being monitored.")
        else:
            click.echo("Unexpected status for Elastic Agent. Output:\n", output)

    except Exception as e:
        raise click.ClickException(f"Error handling Elastic Agent status: {e}")

def install_elastic_agent(ssh_client, username):
    try:
        commands = [
            "curl -L -O https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.14.1-linux-x86_64.tar.gz",
            "tar xzvf elastic-agent-8.14.1-linux-x86_64.tar.gz",
            "cd elastic-agent-8.14.1-linux-x86_64 && echo 'Y' | sudo ./elastic-agent install --url=https://10.53.2.11:8220 --enrollment-token=c2pzbWVKQUI5WHZkQlluMVJlTVY6eHA4YTRCclFTVW05Nk94dmhhdFhEZw== --certificate-authorities=/tmp/http_ca.crt"
        ]

        with Halo(text='Installing Elastic Agent...', spinner='dots'):
            for command in commands:
                stdin, stdout, stderr = ssh_client.exec_command(command)
                stdout.channel.recv_exit_status()  # Wait for command to complete
                output = stdout.read().decode('utf-8')
                error = stderr.read().decode('utf-8')
                click.echo(f"Command: {command}\nOutput: {output}\nError: {error}")

        click.echo("Elastic Agent installed successfully.")

    except Exception as e:
        raise click.ClickException(f"Error installing Elastic Agent: {e}")

def restart_elastic_agent(ssh_client):
    try:
        command = "sudo systemctl restart elastic-agent"
        with Halo(text='Restarting Elastic Agent...', spinner='dots'):
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()  # Wait for command to complete
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

        click.echo("Elastic Agent restart output:")
        click.echo(output)
        if error:
            click.echo("Elastic Agent restart error:")
            click.echo(error)
        else:
            click.echo("Elastic Agent restarted successfully.")

    except Exception as e:
        raise click.ClickException(f"Error restarting Elastic Agent: {e}")

