# azure_utils.py

from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.subscription import SubscriptionClient
from app.constants import STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY


def get_credentials():
    try:
        credential = DefaultAzureCredential()
        return credential
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve Azure credentials: {e}")


def get_compute_client(subscription_id, credential):
    return ComputeManagementClient(credential, subscription_id)


def get_network_client(subscription_id, credential):
    return NetworkManagementClient(credential, subscription_id)


def get_subscription_client(credential):
    return SubscriptionClient(credential)


def get_resource_client(subscription_id, credential):
    try:
        return ResourceManagementClient(credential, subscription_id)
    except Exception as e:
        raise RuntimeError(f"Failed to get Resource Management client: {e}")


def list_subscriptions(subscription_client):
    try:
        return list(subscription_client.subscriptions.list())
    except Exception as e:
        raise RuntimeError(f"Error listing subscriptions: {e}")


def list_resource_groups(resource_client):
    try:
        return list(resource_client.resource_groups.list())
    except Exception as e:
        raise RuntimeError(f"Error listing resource groups: {e}")


def list_vms(compute_client, resource_group_name):
    try:
        vm_list = compute_client.virtual_machines.list(resource_group_name)
        return list(vm_list)
    except Exception as e:
        raise RuntimeError(
            f"Error listing VMs in resource group '{resource_group_name}': {e}"
        )


def get_vm_ip_and_os_type(compute_client, network_client, resource_group_name, vm_name):
    try:
        vm = compute_client.virtual_machines.get(resource_group_name, vm_name)
        os_type = vm.storage_profile.os_disk.os_type
        network_interface_id = vm.network_profile.network_interfaces[0].id
        interface_name = network_interface_id.split("/")[-1]
        sub_id = network_interface_id.split("/")[4]
        network_interface = network_client.network_interfaces.get(
            sub_id, interface_name
        )
        private_ip = network_interface.ip_configurations[0].private_ip_address
        return private_ip, os_type
    except Exception as e:
        raise RuntimeError(f"Error getting VM IP and OS type for VM '{vm_name}': {e}")
