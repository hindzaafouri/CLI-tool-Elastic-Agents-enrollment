import click
import paramiko
from halo import Halo
from app.azure_utils import get_credentials, get_subscription_client, get_compute_client, get_network_client, list_subscriptions, list_resource_groups, list_vms, get_vm_ip_and_os_type, get_resource_client
from app.vm_operations import check_elastic_agent_status, copy_http_ca_to_vm, install_elastic_agent, restart_elastic_agent, uninstall_elastic_agent
from app.constants import STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY

@click.command()
def main():
    try:
        credential = get_credentials()
        subscription_client = get_subscription_client(credential)
        with Halo(text="Listing subscriptions...", spinner='dots'):
            subscriptions = list_subscriptions(subscription_client)

        click.echo("List of Subscriptions:")
        for idx, sub in enumerate(subscriptions, start=1):
            click.echo(f"{idx}. {sub.display_name} ({sub.subscription_id})")

        sub_index = click.prompt(click.style("Enter the number of the subscription to use", fg='green'), type=int) - 1
        chosen_subscription = subscriptions[sub_index]
        subscription_id = chosen_subscription.subscription_id
        click.echo(f"Chosen subscription: {chosen_subscription.display_name} ({subscription_id})")

        compute_client = get_compute_client(subscription_id, credential)
        network_client = get_network_client(subscription_id, credential)
        resource_client = get_resource_client(subscription_id, credential)

        # Prompt for operation: enroll or unenroll
        click.echo("Operations:")
        click.echo("  1. Enroll new Azure VM for monitoring")
        click.echo("  2. Unenroll Azure VM")
        operation = click.prompt(click.style("Enter the number of the operation you want to perform", fg='green'), type=int)


        if operation == 1:  # Enroll VM
            with Halo(text="Listing resource groups...", spinner='dots'):
                rg_list = list_resource_groups(resource_client)

            click.echo("List of Resource Groups:")
            for idx, rg in enumerate(rg_list, start=1):
                click.echo(f"{idx}. {rg.name}")

            rg_index = click.prompt(click.style("Enter the number of the resource group to list VMs", fg='green'), type=int) - 1
            chosen_rg = rg_list[rg_index].name
            click.echo(f"Chosen resource group: {chosen_rg}")

            with Halo(text="Listing VMs...", spinner='dots'):
                vms = list_vms(compute_client, chosen_rg)

            if vms:
                click.echo("List of VMs:")
                for idx, vm in enumerate(vms, start=1):
                    click.echo(f"{idx}. {vm.name}")

                vm_index = click.prompt(click.style("Enter the number of the VM to proceed", fg='green'), type=int) - 1
                selected_vm = vms[vm_index]
                click.echo(f"Selected VM: {selected_vm.name}")

                vm_name = selected_vm.name
                vm_ip, os_type = get_vm_ip_and_os_type(compute_client, network_client, chosen_rg, vm_name)
                click.echo(f"VM IP: {vm_ip}, OS Type: {os_type}")

                # Prompt user for VM credentials
                vm_username = click.prompt(click.style("Enter VM username", fg='green'))
                vm_password = click.prompt(click.style("Enter VM password", fg='green'), hide_input=True)

                # Connect to VM and check Elastic Agent status
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(vm_ip, username=vm_username, password=vm_password)

                status = check_elastic_agent_status(ssh_client)
                if status == "not_found":
                    click.echo(f"Elastic Agent not found on VM {vm_name}. Proceeding with installation.")
                    copy_http_ca_to_vm(vm_ip, os_type, STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY)
                    install_elastic_agent(ssh_client, vm_username)
                elif status == "inactive":
                    click.echo(f"Elastic Agent is inactive on VM {vm_name}. Restarting.")
                    restart_elastic_agent(ssh_client)
                elif status == "active":
                    click.echo(f"Elastic Agent is already running on VM {vm_name}. VM is being monitored.")
                else:
                    click.echo(f"Unknown status for Elastic Agent on VM {vm_name}.")

                ssh_client.close()

        elif operation == 2:  # Unenroll VM
            rg_list = list_resource_groups(resource_client)

            click.echo("List of Resource Groups:")
            for idx, rg in enumerate(rg_list, start=1):
                click.echo(f"{idx}. {rg.name}")

            rg_index = click.prompt(click.style("Enter the number of the resource group to list VMs", fg='green'), type=int) - 1
            chosen_rg = rg_list[rg_index].name
            click.echo(f"Chosen resource group: {chosen_rg}")

            vms = list_vms(compute_client, chosen_rg)

            if vms:
                click.echo("List of VMs:")
                for idx, vm in enumerate(vms, start=1):
                    click.echo(f"{idx}. {vm.name}")

                vm_index = click.prompt(click.style("Enter the number of the VM to unenroll", fg='green'), type=int) - 1
                selected_vm = vms[vm_index]
                click.echo(f"Selected VM to unenroll: {selected_vm.name}")

                vm_name = selected_vm.name
                vm_ip, os_type = get_vm_ip_and_os_type(compute_client, network_client, chosen_rg, vm_name)
                click.echo(f"VM IP: {vm_ip}, OS Type: {os_type}")

                # Prompt user for VM credentials
                vm_username = click.prompt(click.style("Enter VM username", fg='green'))
                vm_password = click.prompt(click.style("Enter VM password", fg='green'), hide_input=True)

                # Connect to VM and uninstall Elastic Agent
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(vm_ip, username=vm_username, password=vm_password)

                uninstall_elastic_agent(ssh_client)
                ssh_client.close()

        else:
            click.echo("Invalid operation. Please choose 1 or 2.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    main()

