import os
import base64
from unittest.mock import MagicMock, patch
from app.vm_operations import (
    check_elastic_agent_status,
    copy_http_ca_to_vm,
    install_elastic_agent,
    restart_elastic_agent,
    uninstall_elastic_agent
)

@patch("paramiko.SSHClient")
def test_check_elastic_agent_status(mock_ssh_client):
    mock_ssh = mock_ssh_client.return_value
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = "Elastic Agent is active (running)".encode("utf-8")
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
    
    status = check_elastic_agent_status(mock_ssh)
    
    assert status == "active"

import base64
from unittest.mock import MagicMock, patch

# def decode_base64_with_padding(data: bytes) -> bytes:
#     padding = b'=' * (-len(data) % 4)
#     return base64.b64decode(data + padding)

# @patch("azure.storage.blob.BlobServiceClient")
# @patch("paramiko.SSHClient")
# @patch("tempfile.NamedTemporaryFile")
# def test_copy_http_ca_to_vm(mock_tempfile, mock_ssh_client, mock_blob_service_client):
#     # Mock tempfile.NamedTemporaryFile to return a specific file path
#     temp_file_mock = MagicMock()
#     temp_file_mock.name = os.path.join(os.environ["TEMP"], "http_ca.crt")
#     mock_tempfile.return_value = temp_file_mock

#     # Mock SSH client and SFTP
#     mock_ssh = mock_ssh_client.return_value
#     mock_sftp = MagicMock()
#     mock_ssh.open_sftp.return_value = mock_sftp

#     # Mock BlobClient and download_blob
#     mock_blob_client = MagicMock()
#     mock_download_stream = MagicMock()

#     # Simulate base64 encoding and decoding of blob content
#     content = b"dummy content"
#     encoded_content = base64.b64encode(content).decode('utf-8')  # Encoding to mimic Azure Blob content
#     mock_download_stream.readall.return_value = decode_base64_with_padding(encoded_content.encode('utf-8'))  # Ensure decoding works with bytes

#     mock_blob_client.download_blob.return_value = mock_download_stream
#     mock_blob_service_client.return_value.get_blob_client.return_value = mock_blob_client

#     # Mocking os.name for Windows systems
#     with patch("os.name", "nt"):
#         copy_http_ca_to_vm("1.2.3.4", "Linux", "test_storage", "test_key", "user", "password")



@patch("paramiko.SSHClient")
def test_install_elastic_agent(mock_ssh_client):
    mock_ssh = mock_ssh_client.return_value
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
    
    install_elastic_agent(mock_ssh, "user")
    
    commands = [
        "curl -L -O https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.14.1-linux-x86_64.tar.gz",
        "tar xzvf elastic-agent-8.14.1-linux-x86_64.tar.gz",
        "cd elastic-agent-8.14.1-linux-x86_64 && echo 'Y' | sudo ./elastic-agent install --url=https://10.53.2.11:8220 --enrollment-token=c2pzbWVKQUI5WHZkQlluMVJlTVY6eHA4YTRCclFTVW05Nk94dmhhdFhEZw== --certificate-authorities=/home/user/http_ca.crt"
    ]
    
    for command in commands:
        mock_ssh.exec_command.assert_any_call(command)

@patch("paramiko.SSHClient")
def test_restart_elastic_agent(mock_ssh_client):
    mock_ssh = mock_ssh_client.return_value
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
    
    restart_elastic_agent(mock_ssh)
    
    mock_ssh.exec_command.assert_called_once_with("sudo systemctl restart elastic-agent")

@patch("paramiko.SSHClient")
def test_uninstall_elastic_agent(mock_ssh_client):
    mock_ssh = mock_ssh_client.return_value
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)
    
    uninstall_elastic_agent(mock_ssh)
    
    mock_ssh.exec_command.assert_called_once_with("sudo /opt/Elastic/Agent/elastic-agent uninstall")
