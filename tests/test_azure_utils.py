import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import patch, MagicMock
from app.azure_utils import (
    get_credentials,
    get_compute_client,
    get_network_client,
    get_resource_client,
    list_subscriptions,
    list_resource_groups,
    list_vms,
    get_vm_ip_and_os_type
)

def test_get_credentials():
    with patch("app.azure_utils.DefaultAzureCredential") as mock_credential:
        mock_credential.return_value = MagicMock()
        credential = get_credentials()
        assert credential is not None

def test_get_compute_client():
    mock_credential = MagicMock()
    subscription_id = "test-subscription-id"
    
    with patch("app.azure_utils.ComputeManagementClient") as mock_client:
        client = get_compute_client(subscription_id, mock_credential)
        mock_client.assert_called_once_with(mock_credential, subscription_id)
        assert client is not None

def test_get_network_client():
    mock_credential = MagicMock()
    subscription_id = "test-subscription-id"
    
    with patch("app.azure_utils.NetworkManagementClient") as mock_client:
        client = get_network_client(subscription_id, mock_credential)
        mock_client.assert_called_once_with(mock_credential, subscription_id)
        assert client is not None

def test_get_resource_client():
    mock_credential = MagicMock()
    subscription_id = "test-subscription-id"
    
    with patch("app.azure_utils.ResourceManagementClient") as mock_client:
        client = get_resource_client(subscription_id, mock_credential)
        mock_client.assert_called_once_with(mock_credential, subscription_id)
        assert client is not None

def test_list_subscriptions():
    mock_subscription_client = MagicMock()
    mock_subscription_client.subscriptions.list.return_value = [
        MagicMock(display_name="Test Subscription", subscription_id="1234")
    ]

    subscriptions = list_subscriptions(mock_subscription_client)
    assert len(subscriptions) == 1
    assert subscriptions[0].display_name == "Test Subscription"

def test_list_resource_groups():
    mock_resource_client = MagicMock()
    mock_resource_group = MagicMock()
    mock_resource_group.name = "TestResourceGroup"
    mock_resource_client.resource_groups.list.return_value = [mock_resource_group]

    resource_groups = list_resource_groups(mock_resource_client)
    assert len(resource_groups) == 1
    assert resource_groups[0].name == "TestResourceGroup"

def test_list_vms():
    mock_compute_client = MagicMock()
    mock_vm = MagicMock()
    mock_vm.name = "test-vm"
    mock_compute_client.virtual_machines.list.return_value = [mock_vm]

    vms = list_vms(mock_compute_client, "test-rg")
    assert len(vms) == 1
    assert vms[0].name == "test-vm"

def test_get_vm_ip_and_os_type():
    mock_compute_client = MagicMock()
    mock_network_client = MagicMock()
    resource_group_name = "test-rg"
    vm_name = "test-vm"
    
    mock_vm = MagicMock()
    mock_vm.storage_profile.os_disk.os_type = "Linux"
    mock_vm.network_profile.network_interfaces[0].id = "/subscriptions/sub-id/resourceGroups/test-rg/providers/Microsoft.Network/networkInterfaces/test-nic"
    mock_network_interface = MagicMock()
    mock_network_interface.ip_configurations[0].private_ip_address = "10.0.0.1"
    
    mock_compute_client.virtual_machines.get.return_value = mock_vm
    mock_network_client.network_interfaces.get.return_value = mock_network_interface
    
    private_ip, os_type = get_vm_ip_and_os_type(mock_compute_client, mock_network_client, resource_group_name, vm_name)
    
    assert private_ip == "10.0.0.1"
    assert os_type == "Linux"