# Elastic Agent Enrollment CLI Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line interface for automating Elastic Agent enrollment with Fleet Server on Azure Virtual Machines.

## Features

### Azure Integration
- 🔍 **Subscription Discovery** - List and select Azure subscriptions interactively
- 📦 **Resource Group Navigation** - Browse and choose resource groups containing VMs
- 🖥️ **VM Inventory** - View all virtual machines within selected resource groups
- 🌐 **Network Intelligence** - Automatically detect VM IP addresses and OS types

### Elastic Agent Management
- ✅ **Agent Status Checks** - Detect if Elastic Agent is installed/running/inactive
- 🚀 **One-Click Installation** - Automated Elastic Agent deployment to target VMs
- 🔄 **Agent Restart** - Restart inactive Elastic Agent services
- 🗑️ **Clean Uninstallation** - Complete removal of Elastic Agent from VMs

### Secure Operations
- 🔐 **Credential Management** - Secure password input with hidden prompts
- 🔑 **SSH Authentication** - Secure remote connections to VMs
- 📜 **Certificate Handling** - Automated HTTP CA certificate deployment
- 🛡️ **Error Handling** - Comprehensive exception management

### User Experience
- 🎨 **Colorful CLI Interface** - Visual feedback with colored output
- ⏳ **Progress Indicators** - Spinner animations for long-running operations
- ❓ **Interactive Prompts** - Guided step-by-step workflow
- ↔️ **Multi-OS Support** - Handles both Windows and Linux VMs

### Operational Efficiency
- 🔄 **Idempotent Workflow** - Safe to rerun on already-managed VMs
- 📝 **Configuration-Free** - No config files needed for basic operation

## Prerequisites

### Azure Requirements
- ☁️ **Azure Account** - Active Azure subscription with contributor permissions
- 🔑 **Azure Credentials** - One of these authentication methods:
  - `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` environment variables
  - [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) logged-in session
  - Managed Identity (if running on Azure resources)

### Target VM Requirements
- 🖥️ **Virtual Machines** - Azure VMs running either:
  - Linux (Ubuntu/CentOS/RHEL recommended)
  - Windows Server 2016+
  - HTTP CA Certificate - Available in Azure Blob Storage (for agent enrollment)
- 🔌 **Network Connectivity**:
  - Open SSH port (22 for Linux)
  - WinRM configured (for Windows VMs)
  - Outbound internet access for agent installation
    
## Installation
```bash
git clone https://github.com/hindzaafouri/CLI-tool-Elastic-Agents-enrollment.git
cd CLI-tool-Elastic-Agents-enrollment
pip install -r requirements.txt 
