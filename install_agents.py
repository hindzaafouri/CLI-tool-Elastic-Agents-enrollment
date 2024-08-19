import click
import time
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.subscription import SubscriptionClient
import paramiko
from halo import Halo


def get_credentials():
    try:
        credential = DefaultAzureCredential()
        return credential
    except Exception as e:
        raise click.ClickException(f"Failed to retrieve Azure credentials: {e}")


def get_compute_client(subscription_id, credential):
    return ComputeManagementClient(credential, subscription_id)


def get_network_client(subscription_id, credential):
    return NetworkManagementClient(credential, subscription_id)


def get_subscription_client(credential):
    return SubscriptionClient(credential)


def list_subscriptions(subscription_client):
    return list(subscription_client.subscriptions.list())


def list_resource_groups(resource_client):
    return list(resource_client.resource_groups.list())


def list_vms(compute_client, resource_group_name):
    try:
        vm_list = compute_client.virtual_machines.list(resource_group_name)
        vms = list(vm_list)
        if not vms:
            raise click.ClickException(
                f"No VMs found in resource group '{resource_group_name}'"
            )
        return vms
    except Exception as e:
        raise click.ClickException(
            f"Error listing VMs in resource group '{resource_group_name}': {e}"
        )


def get_vm_ip_and_os_type(compute_client, network_client, resource_group_name, vm_name):
    vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
    os_type = vm.storage_profile.os_disk.os_type
    network_interface_id = vm.network_profile.network_interfaces[0].id
    interface_name = network_interface_id.split("/")[-1]
    sub_id = network_interface_id.split("/")[4]
    network_interface = network_client.network_interfaces.get(sub_id, interface_name)
    private_ip = network_interface.ip_configurations[0].private_ip_address
    return private_ip, os_type


def copy_http_ca_to_vm(vm_ip, os_type, storage_account_name, storage_account_key):
    try:
        blob_service_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=storage_account_key,
        )

        if os_type.lower() == "linux":
            container_name = "secrets-elk"
            blob_name = "http_ca.crt"

            blob_client = blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            with open("/tmp/http_ca.crt", "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())

            click.echo("File downloaded successfully to /tmp/http_ca.crt")

            click.echo("Waiting for 5 seconds...")
            with Halo(text="Copying file to VM...", spinner="dots"):
                time.sleep(5)

            # Prompt user for username and password
            username = click.prompt("Enter VM username")
            password = click.prompt("Enter VM password", hide_input=True)

            with Halo(text="Connecting to VM...", spinner="dots"):
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(vm_ip, username=username, password=password)

                sftp_client = ssh_client.open_sftp()
                sftp_client.put("/tmp/http_ca.crt", "/tmp/http_ca.crt")
                sftp_client.close()

                click.echo("File copied to target machine successfully.")

                # Check and handle Elastic Agent status
                handle_elastic_agent_status(ssh_client, username)

                ssh_client.close()

        elif os_type.lower() == "windows":
            click.echo("Windows OS detected. Handle Windows logic here.")
        else:
            raise click.ClickException(
                f"Unsupported OS type '{os_type}'. Cannot proceed."
            )

    except Exception as e:
        raise click.ClickException(
            f"Failed to copy file and install Elastic Agent: {e}"
        )


def handle_elastic_agent_status(ssh_client, username):
    try:
        # Command to check Elastic Agent status
        command = "sudo systemctl status elastic-agent"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        click.echo("Elastic Agent status check output:")
        click.echo(output)
        if error:
            click.echo("Elastic Agent status check error:")
            click.echo(error)

        if "could not be found" in error:
            click.echo("Elastic Agent not found. Installing Elastic Agent...")
            install_elastic_agent(ssh_client, username)
        elif "inactive" in output or "failed" in output:
            click.echo(
                "Elastic Agent is inactive or failed. Restarting Elastic Agent..."
            )
            restart_elastic_agent(ssh_client)
        elif "active (running)" in output:
            click.echo(
                "Elastic Agent is installed and running. The machine is being monitored."
            )
        else:
            click.echo("Unexpected status for Elastic Agent. Output:\n", output)

    except Exception as e:
        raise click.ClickException(f"Error handling Elastic Agent status: {e}")


def install_elastic_agent(ssh_client, username):
    try:
        commands = [
            "curl -L -O https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.14.1-linux-x86_64.tar.gz",
            "tar xzvf elastic-agent-8.14.1-linux-x86_64.tar.gz",
            "cd elastic-agent-8.14.1-linux-x86_64 && echo 'Y' | sudo ./elastic-agent install --url=https://10.53.2.11:8220 --enrollment-token=c2pzbWVKQUI5WHZkQlluMVJlTVY6eHA4YTRCclFTVW05Nk94dmhhdFhEZw== --certificate-authorities=/tmp/http_ca.crt",
        ]

        with Halo(text="Installing Elastic Agent...", spinner="dots"):
            for command in commands:
                stdin, stdout, stderr = ssh_client.exec_command(command)
                stdout.channel.recv_exit_status()  # Wait for command to complete
                output = stdout.read().decode("utf-8")
                error = stderr.read().decode("utf-8")
                click.echo(f"Command: {command}\nOutput: {output}\nError: {error}")

        click.echo("Elastic Agent installed successfully.")

    except Exception as e:
        raise click.ClickException(f"Error installing Elastic Agent: {e}")


def restart_elastic_agent(ssh_client):
    try:
        command = "sudo systemctl restart elastic-agent"
        with Halo(text="Restarting Elastic Agent...", spinner="dots"):
            stdin, stdout, stderr = ssh_client.exec_command(command)
            stdout.channel.recv_exit_status()  # Wait for command to complete
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            click.echo(f"Output: {output}\nError: {error}")

        click.echo("Elastic Agent restarted successfully.")

    except Exception as e:
        raise click.ClickException(f"Error restarting Elastic Agent: {e}")


@click.group()
def cli():
    pass


@cli.command()
def main():
    try:
        credential = get_credentials()
        subscription_client = get_subscription_client(credential)
        subscriptions = list_subscriptions(subscription_client)

        click.echo("List of Subscriptions:")
        for idx, sub in enumerate(subscriptions, start=1):
            click.echo(f"{idx}. {sub.display_name} ({sub.subscription_id})")

        sub_index = (
            click.prompt("Enter the number of the subscription to use", type=int) - 1
        )
        chosen_subscription = subscriptions[sub_index]
        subscription_id = chosen_subscription.subscription_id
        click.echo(
            f"Chosen subscription: {chosen_subscription.display_name} ({subscription_id})"
        )

        compute_client = get_compute_client(subscription_id, credential)
        network_client = get_network_client(subscription_id, credential)
        resource_client = ResourceManagementClient(credential, subscription_id)

        rg_list = list_resource_groups(resource_client)

        click.echo("List of Resource Groups:")
        for idx, rg in enumerate(rg_list, start=1):
            click.echo(f"{idx}. {rg.name}")

        rg_index = (
            click.prompt("Enter the number of the resource group to list VMs", type=int)
            - 1
        )
        chosen_rg = rg_list[rg_index].name
        click.echo(f"Chosen resource group: {chosen_rg}")

        vms = list_vms(compute_client, chosen_rg)

        if vms:
            vm_index = (
                click.prompt("Enter the number of the VM to copy http_ca.crt", type=int)
                - 1
            )
            selected_vm = vms[vm_index]
            click.echo(f"Copying http_ca.crt to VM '{selected_vm.name}'...")

            vm_name = selected_vm.name
            vm_ip, os_type = get_vm_ip_and_os_type(
                compute_client, network_client, chosen_rg, vm_name
            )

            storage_account_name = "sapfe"
            storage_account_key = "JYUQkMiI6C8G6uTbgKfpX0XY4ubTZSl3WSLJ8Omn/fj2LCDiBx1DUMlNCDsnkvw/Hf/PWn7kS0ns+AStF308RA=="

            copy_http_ca_to_vm(
                vm_ip, os_type, storage_account_name, storage_account_key
            )

    except Exception as e:
        raise click.ClickException(f"Error: {e}")


if __name__ == "__main__":
    cli()
