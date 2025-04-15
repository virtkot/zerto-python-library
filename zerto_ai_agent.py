import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import urllib3
import json
from zvma import ZVMAClient
from dotenv import load_dotenv
import openai
import traceback
from zvma import common
#Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ZertoAIAgent:
    def __init__(self, args):
        self.zvma_client = ZVMAClient(
            zvm_address=args.zvm_address,
            client_id=args.client_id,
            client_secret=args.client_secret,
            verify_certificate=not args.ignore_ssl
        )
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def _define_functions(self):
        return [
            {
                "name": "ASK_VPG_NAME",
                "description": "Ask user to provide a VPG name when creating a VPG without specified name",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_vpg",
                "description": "Create a new Virtual Protection Group",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the VPG"},
                        "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
                        "rpo_seconds": {"type": "integer", "description": "Recovery Point Objective in seconds"},
                        "journal_history_hours": {"type": "integer", "description": "Journal retention period in hours"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "list_vpgs",
                "description": "List all Virtual Protection Groups (VPGs)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Filter by VPG name"},
                        "status": {"type": "string", "enum": ["Initializing", "MeetingSLA", "NotMeetingSLA", "FailingOver", "Moving", "Deleting", "Recovered"]},
                    }
                }
            },
            {
                "name": "delete_vpg",
                "description": "Delete a Virtual Protection Group. If VPG name is not provided, will ask for it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG to delete"},
                        "force": {"type": "boolean", "description": "Force delete the VPG"},
                        "keep_recovery_volumes": {"type": "boolean", "description": "Keep recovery volumes after deletion"}
                    }
                }  # Removed "required": ["vpg_name"] to allow empty calls
            },
            {
                "name": "add_vm_to_vpg",
                "description": "Add a VM to an existing VPG",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG"},
                        "vm_name": {"type": "string", "description": "Name of the VM to add"}
                    },
                    "required": ["vpg_name", "vm_name"]
                }
            },
            {
                "name": "create_vpg_checkpoint",
                "description": "Create a checkpoint for a VPG",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG"},
                        "checkpoint_name": {"type": "string", "description": "Name for the checkpoint"}
                    },
                    "required": ["vpg_name", "checkpoint_name"]
                }
            },

            # Failover Operations
            {
                "name": "start_failover_test",
                "description": "Initiate a failover test for a VPG",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG to test"}
                    },
                    "required": ["vpg_name"]
                }
            },
            {
                "name": "stop_failover_test",
                "description": "Stop a failover test",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG"},
                        "success": {"type": "boolean", "description": "Whether the test was successful"}
                    },
                    "required": ["vpg_name"]
                }
            },

            # Alert Management
            {
                "name": "get_alerts",
                "description": "Get current alerts from the system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["Error", "Warning", "Info"]},
                        "is_dismissed": {"type": "boolean", "description": "Filter by dismissed status"}
                    }
                }
            },

            # VRA Management
            {
                "name": "list_vras",
                "description": "List all Virtual Replication Appliances",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },

            # Site Management
            {
                "name": "get_site_details",
                "description": "Get information about the local site",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_peer_sites",
                "description": "List all paired sites",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },

            # Resource Management
            {
                "name": "list_datastores",
                "description": "List available datastores",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_networks",
                "description": "List available networks",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },

            # VM Operations
            {
                "name": "list_vms",
                "description": "List virtual machines",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Filter by VPG name"},
                        "status": {"type": "string", "description": "Filter by protection status"}
                    }
                }
            },

            # Reporting
            {
                "name": "get_recovery_report",
                "description": "Get recovery operation reports",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Filter by VPG name"},
                        "operation_type": {"type": "string", "enum": ["Failover", "FailoverTest", "Move"]}
                    }
                }
            },

            # License Management
            {
                "name": "get_license_info",
                "description": "Get current license information",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },

            # Encryption Detection
            {
                "name": "list_suspected_volumes",
                "description": "List volumes suspected of being encrypted",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_encryption_detection_types",
                "description": "Get available encryption detection types",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },

            # Recovery Operations
            {
                "name": "get_recovery_reports",
                "description": "Get detailed recovery operation reports",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string", "description": "Start time for report range"},
                        "end_time": {"type": "string", "description": "End time for report range"},
                        "recovery_type": {"type": "string", "enum": ["Failover", "FailoverTest", "Move"]},
                        "state": {"type": "string", "enum": ["Success", "Fail"]}
                    }
                }
            },
            {
                "name": "get_recovery_scripts",
                "description": "List available recovery scripts",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_vra",
                "description": "Deploy a new Virtual Replication Appliance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host_name": {"type": "string", "description": "Name of the host to deploy VRA on"},
                        "network_name": {"type": "string", "description": "Network for the VRA"},
                        "ip_config_type": {"type": "string", "enum": ["Static", "DHCP"]},
                        "ip_address": {"type": "string", "description": "IP address for static configuration"},
                        "subnet_mask": {"type": "string", "description": "Subnet mask for static configuration"},
                        "default_gateway": {"type": "string", "description": "Default gateway for static configuration"}
                    },
                    "required": ["host_name", "network_name", "ip_config_type"]
                }
            },
            {
                "name": "delete_vra",
                "description": "Remove a Virtual Replication Appliance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vra_identifier": {"type": "string", "description": "Identifier of the VRA to remove"}
                    },
                    "required": ["vra_identifier"]
                }
            },
            {
                "name": "upgrade_vra",
                "description": "Upgrade a Virtual Replication Appliance",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vra_identifier": {"type": "string", "description": "Identifier of the VRA to upgrade"}
                    },
                    "required": ["vra_identifier"]
                }
            },
            {
                "name": "pair_site",
                "description": "Pair with another Zerto site",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hostname": {"type": "string", "description": "Hostname of the site to pair with"},
                        "port": {"type": "integer", "description": "Port number (default: 9071)"}
                    },
                    "required": ["hostname"]
                }
            },
            {
                "name": "unpair_site",
                "description": "Remove pairing with a site",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_identifier": {"type": "string", "description": "Identifier of the site to unpair"}
                    },
                    "required": ["site_identifier"]
                }
            },
            {
                "name": "update_license",
                "description": "Update Zerto license with a new key",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "license_key": {"type": "string", "description": "New license key to apply"}
                    },
                    "required": ["license_key"]
                }
            },
            {
                "name": "list_volumes",
                "description": "List volumes for a specific VM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vm_name": {"type": "string", "description": "Name of the VM"},
                        "include_temp": {"type": "boolean", "description": "Include temporary volumes"}
                    },
                    "required": ["vm_name"]
                }
            },
            {
                "name": "get_volume_info",
                "description": "Get detailed information about a specific volume",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "volume_id": {"type": "string", "description": "ID of the volume"},
                        "vm_name": {"type": "string", "description": "Name of the VM owning the volume"}
                    },
                    "required": ["volume_id", "vm_name"]
                }
            },
            {
                "name": "list_tasks",
                "description": "List recent tasks and their status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["InProgress", "Completed", "Failed"]},
                        "type": {"type": "string", "description": "Type of task to filter"},
                        "limit": {"type": "integer", "description": "Maximum number of tasks to return"}
                    }
                }
            },
            {
                "name": "get_task_info",
                "description": "Get detailed information about a specific task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "ID of the task"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "list_service_profiles",
                "description": "List all service profiles",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_service_profile",
                "description": "Create a new service profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the service profile"},
                        "description": {"type": "string", "description": "Description of the service profile"},
                        "rpo": {"type": "integer", "description": "Recovery Point Objective in seconds"},
                        "history": {"type": "integer", "description": "Journal history in hours"}
                    },
                    "required": ["name", "rpo", "history"]
                }
            },
            {
                "name": "get_session_info",
                "description": "Get information about the current session",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_repositories",
                "description": "List all backup repositories",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "add_repository",
                "description": "Add a new backup repository",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the repository"},
                        "path": {"type": "string", "description": "Path to the repository"},
                        "type": {"type": "string", "enum": ["Local", "Network", "AWS", "Azure"]},
                        "capacity_in_gb": {"type": "integer", "description": "Repository capacity in GB"}
                    },
                    "required": ["name", "path", "type"]
                }
            },
            {
                "name": "get_server_time",
                "description": "Get the current server date and time",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "list_zorgs",
                "description": "List all Zerto organizations (ZORGs)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Filter by ZORG name"}
                    }
                }
            },
            {
                "name": "create_zorg",
                "description": "Create a new Zerto organization",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the ZORG"},
                        "contact_name": {"type": "string", "description": "Contact person name"},
                        "contact_email": {"type": "string", "description": "Contact email address"},
                        "contact_phone": {"type": "string", "description": "Contact phone number"}
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "list_virtualization_sites",
                "description": "List all virtualization sites",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["vCenter", "HyperV", "Azure", "AWS"]},
                        "status": {"type": "string", "enum": ["Paired", "Unpaired"]}
                    }
                }
            },
            {
                "name": "get_site_settings",
                "description": "Get virtualization site settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_identifier": {"type": "string", "description": "Site identifier"}
                    },
                    "required": ["site_identifier"]
                }
            },
            {
                "name": "update_site_settings",
                "description": "Update virtualization site settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_identifier": {"type": "string", "description": "Site identifier"},
                        "default_rpo": {"type": "integer", "description": "Default RPO in seconds"},
                        "default_journal_history": {"type": "integer", "description": "Default journal history in hours"},
                        "bandwidth_limit": {"type": "integer", "description": "Bandwidth limit in Mbps"}
                    },
                    "required": ["site_identifier"]
                }
            },
            {
                "name": "list_events",
                "description": "List system events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["All", "VPG", "VRA", "Site", "License"]},
                        "from_date": {"type": "string", "description": "Start date (ISO format)"},
                        "to_date": {"type": "string", "description": "End date (ISO format)"},
                        "limit": {"type": "integer", "description": "Maximum number of events to return"}
                    }
                }
            },
            {
                "name": "get_event_details",
                "description": "Get detailed information about a specific event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "string", "description": "ID of the event"}
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "add_recovery_script",
                "description": "Add a new recovery script",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the script"},
                        "description": {"type": "string", "description": "Description of the script"},
                        "script_content": {"type": "string", "description": "Content of the script"},
                        "timeout": {"type": "integer", "description": "Script timeout in seconds"}
                    },
                    "required": ["name", "script_content"]
                }
            },
            {
                "name": "delete_recovery_script",
                "description": "Delete a recovery script",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script_id": {"type": "string", "description": "ID of the script to delete"}
                    },
                    "required": ["script_id"]
                }
            },
            {
                "name": "get_system_settings",
                "description": "Get system-wide settings and tweaks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["General", "Performance", "Network", "Security"]}
                    }
                }
            },
            {
                "name": "update_system_settings",
                "description": "Update system-wide settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "performance_optimization": {"type": "boolean", "description": "Enable performance optimization"},
                        "max_concurrent_replications": {"type": "integer", "description": "Maximum concurrent replications"},
                        "compression_level": {"type": "string", "enum": ["None", "Normal", "High"]},
                        "bandwidth_limit": {"type": "integer", "description": "Global bandwidth limit in Mbps"}
                    }
                }
            },
            {
                "name": "create_vm_snapshot",
                "description": "Create a snapshot of a virtual machine",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vm_name": {"type": "string", "description": "Name of the VM"},
                        "snapshot_name": {"type": "string", "description": "Name for the snapshot"},
                        "description": {"type": "string", "description": "Description of the snapshot"},
                        "memory": {"type": "boolean", "description": "Include memory in snapshot"}
                    },
                    "required": ["vm_name", "snapshot_name"]
                }
            },
            {
                "name": "remove_vm_snapshot",
                "description": "Remove a snapshot from a virtual machine",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vm_name": {"type": "string", "description": "Name of the VM"},
                        "snapshot_name": {"type": "string", "description": "Name of the snapshot to remove"}
                    },
                    "required": ["vm_name", "snapshot_name"]
                }
            },
            {
                "name": "get_vm_nics",
                "description": "Get network interface information for a VM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vm_name": {"type": "string", "description": "Name of the VM"}
                    },
                    "required": ["vm_name"]
                }
            },
            {
                "name": "update_vm_network",
                "description": "Update network settings for a VM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vm_name": {"type": "string", "description": "Name of the VM"},
                        "nic_id": {"type": "string", "description": "ID of the network interface"},
                        "network_name": {"type": "string", "description": "Name of the network to connect to"},
                        "ip_address": {"type": "string", "description": "New IP address"},
                        "subnet_mask": {"type": "string", "description": "New subnet mask"}
                    },
                    "required": ["vm_name", "nic_id", "network_name"]
                }
            },
            {
                "name": "get_network_stats",
                "description": "Get network statistics for a VM or VRA",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_type": {"type": "string", "enum": ["VM", "VRA"]},
                        "entity_name": {"type": "string", "description": "Name of the VM or VRA"},
                        "timeframe": {"type": "string", "enum": ["1hour", "24hours", "7days"]}
                    },
                    "required": ["entity_type", "entity_name"]
                }
            },
            {
                "name": "create_backup",
                "description": "Create a backup of a VPG",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG to backup"},
                        "backup_name": {"type": "string", "description": "Name for the backup"},
                        "repository_name": {"type": "string", "description": "Target repository name"}
                    },
                    "required": ["vpg_name", "backup_name", "repository_name"]
                }
            },
            {
                "name": "restore_backup",
                "description": "Restore from a backup",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "backup_name": {"type": "string", "description": "Name of the backup to restore"},
                        "target_datastore": {"type": "string", "description": "Target datastore for restore"},
                        "power_on": {"type": "boolean", "description": "Power on VMs after restore"}
                    },
                    "required": ["backup_name", "target_datastore"]
                }
            },
            {
                "name": "get_resource_usage",
                "description": "Get resource usage statistics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_type": {"type": "string", "enum": ["CPU", "Memory", "Storage", "Network"]},
                        "timeframe": {"type": "string", "enum": ["1hour", "24hours", "7days", "30days"]},
                        "entity_type": {"type": "string", "enum": ["VPG", "VRA", "Site"]}
                    },
                    "required": ["resource_type"]
                }
            },
            {
                "name": "get_performance_metrics",
                "description": "Get detailed performance metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_type": {"type": "string", "enum": ["IOPs", "Throughput", "Latency", "RPO"]},
                        "vpg_name": {"type": "string", "description": "VPG name for specific metrics"},
                        "interval": {"type": "string", "enum": ["5min", "1hour", "1day"]}
                    },
                    "required": ["metric_type"]
                }
            },
            {
                "name": "get_replication_status",
                "description": "Get detailed replication status",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG"},
                        "include_details": {"type": "boolean", "description": "Include detailed statistics"}
                    },
                    "required": ["vpg_name"]
                }
            },
            {
                "name": "generate_site_report",
                "description": "Generate a comprehensive site report",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["Resource", "Performance", "Protection", "Compliance"]},
                        "time_range": {"type": "string", "enum": ["24hours", "7days", "30days", "custom"]},
                        "start_date": {"type": "string", "description": "Start date for custom range (ISO format)"},
                        "end_date": {"type": "string", "description": "End date for custom range (ISO format)"},
                        "export_format": {"type": "string", "enum": ["JSON", "CSV", "PDF"]}
                    },
                    "required": ["report_type"]
                }
            },
            {
                "name": "analyze_performance_trends",
                "description": "Analyze performance trends and patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "string", "enum": ["RPO", "RTO", "JournalSize", "NetworkUsage", "StorageUsage"]},
                        "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                        "vpg_name": {"type": "string", "description": "Optional VPG name for specific analysis"}
                    },
                    "required": ["metric", "period"]
                }
            },
            {
                "name": "get_sla_compliance",
                "description": "Get SLA compliance statistics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Optional VPG name for specific compliance"},
                        "time_range": {"type": "string", "enum": ["24hours", "7days", "30days"]},
                        "include_details": {"type": "boolean", "description": "Include detailed compliance breakdown"}
                    }
                }
            },
            {
                "name": "get_capacity_planning",
                "description": "Get capacity planning and forecasting",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_type": {"type": "string", "enum": ["Storage", "Network", "Compute"]},
                        "forecast_period": {"type": "string", "enum": ["1month", "3months", "6months", "1year"]},
                        "include_recommendations": {"type": "boolean", "description": "Include optimization recommendations"}
                    },
                    "required": ["resource_type", "forecast_period"]
                }
            },
            {
                "name": "get_protection_assessment",
                "description": "Get protection status assessment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assessment_type": {"type": "string", "enum": ["Coverage", "Gaps", "Risks", "Complete"]},
                        "include_recommendations": {"type": "boolean", "description": "Include remediation recommendations"}
                    },
                    "required": ["assessment_type"]
                }
            },
            {
                "name": "run_health_check",
                "description": "Run a comprehensive health check of the Zerto environment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "check_type": {"type": "string", "enum": ["Quick", "Full", "Custom"]},
                        "components": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["VPGs", "VRAs", "Networks", "Storage", "Connectivity"]},
                            "description": "Components to check in custom mode"
                        }
                    },
                    "required": ["check_type"]
                }
            },
            {
                "name": "schedule_health_check",
                "description": "Schedule recurring health checks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "frequency": {"type": "string", "enum": ["Daily", "Weekly", "Monthly"]},
                        "time": {"type": "string", "description": "Time to run (HH:MM)"},
                        "day": {"type": "string", "description": "Day of week/month for Weekly/Monthly checks"}
                    },
                    "required": ["frequency", "time"]
                }
            },
            {
                "name": "run_dr_test",
                "description": "Run an automated disaster recovery test",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG to test"},
                        "test_type": {"type": "string", "enum": ["Basic", "Full", "Custom"]},
                        "test_network": {"type": "string", "description": "Test network for failover"},
                        "run_scripts": {"type": "boolean", "description": "Execute recovery scripts"},
                        "validate_apps": {"type": "boolean", "description": "Validate applications post-failover"}
                    },
                    "required": ["vpg_name", "test_type"]
                }
            },
            {
                "name": "schedule_dr_test",
                "description": "Schedule automated DR tests",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vpg_name": {"type": "string", "description": "Name of the VPG to test"},
                        "frequency": {"type": "string", "enum": ["Monthly", "Quarterly", "Yearly"]},
                        "test_type": {"type": "string", "enum": ["Basic", "Full", "Custom"]},
                        "notification_email": {"type": "string", "description": "Email for test results"}
                    },
                    "required": ["vpg_name", "frequency", "test_type"]
                }
            },
            {
                "name": "configure_alert_settings",
                "description": "Configure alert notification settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "alert_type": {"type": "string", "enum": ["Email", "SNMP", "Syslog", "REST"]},
                        "enabled": {"type": "boolean", "description": "Enable/disable the alert type"},
                        "recipients": {"type": "array", "items": {"type": "string"}, "description": "List of recipients"},
                        "severity_level": {"type": "string", "enum": ["Error", "Warning", "Info"]},
                        "notification_timeout": {"type": "integer", "description": "Timeout in minutes"}
                    },
                    "required": ["alert_type", "enabled"]
                }
            },
            {
                "name": "configure_external_monitoring",
                "description": "Configure integration with external monitoring systems",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "system_type": {"type": "string", "enum": ["Nagios", "Zabbix", "SolarWinds", "PRTG", "Custom"]},
                        "endpoint_url": {"type": "string", "description": "Monitoring system endpoint URL"},
                        "auth_token": {"type": "string", "description": "Authentication token"},
                        "metrics": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["Performance", "Health", "Alerts", "Resources"]},
                            "description": "Metrics to monitor"
                        },
                        "interval": {"type": "integer", "description": "Monitoring interval in minutes"}
                    },
                    "required": ["system_type", "endpoint_url"]
                }
            },
            {
                "name": "create_alert_rule",
                "description": "Create a custom alert rule",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the alert rule"},
                        "condition": {"type": "string", "description": "Alert condition"},
                        "severity": {"type": "string", "enum": ["Error", "Warning", "Info"]},
                        "entity_type": {"type": "string", "enum": ["VPG", "VRA", "Site", "VM"]},
                        "actions": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["Email", "SNMP", "Syslog", "Script"]},
                            "description": "Actions to take when alert triggers"
                        }
                    },
                    "required": ["name", "condition", "severity"]
                }
            },
            {
                "name": "configure_monitoring_thresholds",
                "description": "Configure monitoring thresholds for various metrics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_type": {"type": "string", "enum": ["RPO", "RTO", "JournalSize", "NetworkUsage", "CPUUsage", "MemoryUsage"]},
                        "warning_threshold": {"type": "number", "description": "Warning level threshold"},
                        "error_threshold": {"type": "number", "description": "Error level threshold"},
                        "measurement_period": {"type": "string", "enum": ["5min", "15min", "1hour", "1day"]},
                        "entity_type": {"type": "string", "enum": ["VPG", "VRA", "Site"]}
                    },
                    "required": ["metric_type", "warning_threshold", "error_threshold"]
                }
            },
            {
                "name": "get_encryption_status",
                "description": "Get encryption status for volumes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "vm_name": {"type": "string", "description": "Filter by VM name"},
                        "include_history": {"type": "boolean", "description": "Include detection history"}
                    }
                }
            },
            {
                "name": "update_detection_settings",
                "description": "Update encryption detection settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "detection_types": {"type": "array", "items": {"type": "string"}, "description": "Types to enable"},
                        "scan_interval": {"type": "integer", "description": "Scan interval in hours"},
                        "confidence_threshold": {"type": "integer", "description": "Minimum confidence level"}
                    },
                    "required": ["detection_types"]
                }
            },
            {
                "name": "update_recovery_script",
                "description": "Update an existing recovery script",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script_id": {"type": "string", "description": "ID of the script to update"},
                        "name": {"type": "string", "description": "New name for the script"},
                        "script_content": {"type": "string", "description": "Updated script content"},
                        "timeout": {"type": "integer", "description": "New timeout value"}
                    },
                    "required": ["script_id"]
                }
            },
            {
                "name": "test_recovery_script",
                "description": "Test a recovery script",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script_id": {"type": "string", "description": "ID of the script to test"},
                        "test_parameters": {"type": "object", "description": "Test parameters"}
                    },
                    "required": ["script_id"]
                }
            },
            {
                "name": "cancel_task",
                "description": "Cancel a running task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "ID of the task to cancel"},
                        "force": {"type": "boolean", "description": "Force cancel the task"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "get_task_history",
                "description": "Get task execution history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_type": {"type": "string", "description": "Filter by task type"},
                        "status": {"type": "string", "enum": ["Success", "Failed", "Canceled"]},
                        "start_date": {"type": "string", "description": "Start date (ISO format)"},
                        "end_date": {"type": "string", "description": "End date (ISO format)"}
                    }
                }
            },
            {
                "name": "get_security_posture",
                "description": "Get overall security posture assessment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_details": {"type": "boolean", "description": "Include detailed security findings"},
                        "categories": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["Access", "Network", "Data", "Compliance"]},
                            "description": "Security categories to assess"
                        }
                    }
                }
            },
            {
                "name": "run_compliance_check",
                "description": "Run compliance check against specific standards",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "standard": {"type": "string", "enum": ["HIPAA", "PCI", "SOX", "GDPR", "ISO27001"]},
                        "scope": {"type": "string", "enum": ["Full", "Delta", "Custom"]},
                        "include_remediation": {"type": "boolean", "description": "Include remediation steps"}
                    },
                    "required": ["standard"]
                }
            },
            {
                "name": "get_audit_logs",
                "description": "Get security audit logs",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string", "description": "Start time (ISO format)"},
                        "end_time": {"type": "string", "description": "End time (ISO format)"},
                        "event_type": {"type": "string", "enum": ["Login", "Configuration", "DataAccess", "SystemChanges"]},
                        "severity": {"type": "string", "enum": ["Info", "Warning", "Critical"]}
                    }
                }
            },
            {
                "name": "verify_security_settings",
                "description": "Verify current security settings against best practices",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "check_categories": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["Authentication", "Encryption", "NetworkSecurity", "DataProtection"]},
                            "description": "Categories to verify"
                        },
                        "generate_report": {"type": "boolean", "description": "Generate detailed report"}
                    }
                }
            },
            {
                "name": "list_available_resources",
                "description": "List available resources for VPG creation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_type": {
                            "type": "string",
                            "enum": ["datastores", "hosts", "networks", "resource_pools", "folders"],
                            "description": "Type of resources to list"
                        },
                        "site_identifier": {"type": "string", "description": "Site identifier"}
                    },
                    "required": ["resource_type"]
                }
            }
        ]

    def handle_function(self, function_name, params):
        try:
            handlers = {
                "list_vpgs": self._handle_list_vpgs,
                "get_alerts": self._handle_get_alerts,
                "start_failover_test": self._handle_start_failover_test,
                "stop_failover_test": self._handle_stop_failover_test,
                "create_vpg": self._handle_create_vpg,
                "delete_vpg": self._handle_delete_vpg,
                "add_vm_to_vpg": self._handle_add_vm_to_vpg,
                "ASK_VPG_NAME": self._handle_ask_vpg_name,
                # ... rest of the handlers ...
            }
            
            handler = handlers.get(function_name)
            if handler:
                return handler(params)
            return f"Unknown function: {function_name}"
        except Exception as e:
            error_traceback = traceback.format_exc()
            logging.error(f"Error in {function_name} at:\n{error_traceback}")
            return f"Error executing {function_name}:\n{error_traceback}"

    def _handle_ask_vpg_name(self, params):
        """Handle VPG name request and creation"""
        vpg_name = input("\nPlease enter a name for the VPG: ")
        result = self._handle_create_vpg({"name": vpg_name})
        
        # Ask about adding VMs
        add_vms = input("\nWould you like to add VMs to this VPG? (yes/no): ")
        if add_vms.lower() == 'yes':
            vm_name = input("Enter VM name to add: ")
            return self._handle_add_vm_to_vpg({
                "vpg_name": vpg_name,
                "vm_name": vm_name
            })
        return result

    def _handle_list_vpgs(self, params):
        vpgs = self.zvma_client.vpgs.list_vpgs()
        logging.debug(f"VPGS: {json.dumps(vpgs, indent=4)}")
        if not vpgs:
            return "No VPGs found."
        
        # Format the VPG list
        return self._format_vpg_list(vpgs)

    def _format_vpg_list(self, vpgs):
        return "\n".join([
            f"VPG: {vpg.get('VpgName', 'Unknown')}\n"
            f"- Status: {common.ZertoVPGStatus.get_name_by_value(vpg.get('Status', 'Unknown'))}\n"
            f"- SubStatus: {common.ZertoVPGSubstatus.get_name_by_value(vpg.get('SubStatus', 'Unknown'))}\n"
            f"- Priority: {common.ZertoVPGPriority.get_name_by_value(vpg.get('Priority', 'Unknown'))}\n"
            f"- VM Count: {vpg.get('VmsCount', 'Unknown')}\n"
            f"- Configured RPO: {vpg.get('ConfiguredRpoSeconds', 'Unknown')} seconds\n"
            f"- Actual RPO: {vpg.get('ActualRPO', 'Unknown')} seconds\n"
            f"- Journal History: {vpg.get('HistoryStatusApi', {}).get('ActualHistoryInMinutes', 'Unknown')} minutes"
            for vpg in vpgs
        ])

    def _handle_get_alerts(self, params):
        alerts = self.zvma_client.alerts.get_alerts(**params)
        if not alerts:
            return "No alerts found."
        return self._format_alerts(alerts)

    def _handle_start_failover_test(self, params):
        vpg_name = params.get("vpg_name")
        task_id = self.zvma_client.vpgs.failover_test(vpg_name)
        return f"Initiated failover test for VPG {vpg_name}. Task ID: {task_id}"

    def _handle_stop_failover_test(self, params):
        vpg_name = params.get("vpg_name")
        success = params.get("success")
        result = self.zvma_client.vpgs.stop_failover_test(vpg_name, success)
        return f"Stopped failover test for VPG {vpg_name}. Result: {result}"

    def _handle_create_vpg(self, params):
        """Handle VPG creation with hardcoded resource selection"""
        if not params.get("name"):
            return "VPG name is required"
        
        # Get local and peer site information
        local_site = self.zvma_client.localsite.get_local_site()
        local_site_identifier = local_site.get('SiteIdentifier')
        
        virtualization_sites = self.zvma_client.virtualization_sites.get_virtualization_sites()
        peer_site = next((site for site in virtualization_sites 
                         if site['SiteIdentifier'] != local_site_identifier), None)
        
        if not peer_site:
            return "No peer site found. Please configure site pairing first."
        
        peer_site_identifier = peer_site['SiteIdentifier']
        
        # Get available resources from peer site
        datastores = self.zvma_client.virtualization_sites.get_virtualization_site_datastores(
            site_identifier=peer_site_identifier
        )
        logging.debug(f"Datastores: {json.dumps(datastores, indent=4)}")
        
        hosts = self.zvma_client.virtualization_sites.get_virtualization_site_hosts(
            site_identifier=peer_site_identifier
        )
        logging.debug(f"Hosts: {json.dumps(hosts, indent=4)}")
        networks = self.zvma_client.virtualization_sites.get_virtualization_site_networks(
            site_identifier=peer_site_identifier
        )
        logging.debug(f"Networks: {json.dumps(networks, indent=4)}")
        
        resource_pools = self.zvma_client.virtualization_sites.get_virtualization_site_resource_pools(
            site_identifier=peer_site_identifier
        )
        logging.debug(f"Resource Pools: {json.dumps(resource_pools, indent=4)}")
        
        folders = self.zvma_client.virtualization_sites.get_virtualization_site_folders(
            site_identifier=peer_site_identifier
        )
        
        # Present resources to user
        print("\nAvailable Datastores:")
        for i, ds in enumerate(datastores, 1):
            print(f"{i}. {ds.get('DatastoreName')} (DatastoreIdentifier: {ds.get('DatastoreIdentifier', 'Unknown')})")
        
        ds_choice = int(input("\nSelect datastore number: ")) - 1
        selected_datastore = datastores[ds_choice]
        
        print("\nAvailable Hosts:")
        for i, host in enumerate(hosts, 1):
            print(f"{i}. {host.get('VirtualizationHostName', 'Unknown')} (HostIdentifier: {host.get('HostIdentifier', 'Unknown')})")
        
        host_choice = int(input("\nSelect host number: ")) - 1
        selected_host = hosts[host_choice]
        
        print("\nAvailable Networks:")
        for i, net in enumerate(networks, 1):
            print(f"{i}. {net.get('VirtualizationNetworkName', 'Unknown')} (NetworkIdentifier: {net.get('NetworkIdentifier', 'Unknown')})")
        
        net_choice = int(input("\nSelect network number: ")) - 1
        selected_network = networks[net_choice]
        
        print("\nAvailable Resource Pools:")
        for i, pool in enumerate(resource_pools, 1):
            print(f"{i}. {pool.get('ResourcepoolName', 'Unknown')} (ResourcePoolIdentifier: {pool.get('ResourcePoolIdentifier', 'Unknown')})")
        
        pool_choice = int(input("\nSelect resource pool number: ")) - 1
        selected_pool = resource_pools[pool_choice]
        
        # Get root folder identifier
        root_folder = next((folder for folder in folders if folder.get('FolderName') == '/'), None)
        if not root_folder:
            return "Could not find root folder"
        
        # Construct VPG structures
        basic = {
            "Name": params["name"],
            "VpgType": "Remote",
            "RpoInSeconds": params.get("rpo_seconds", 300),
            "JournalHistoryInHours": params.get("journal_history_hours", 24),
            "Priority": params.get("priority", "Medium"),
            "UseWanCompression": True,
            "ProtectedSiteIdentifier": local_site_identifier,
            "RecoverySiteIdentifier": peer_site_identifier
        }
        
        journal = {
            "DatastoreIdentifier": selected_datastore["DatastoreIdentifier"],
            "Limitation": {
                "HardLimitInMB": 153600,  # 150GB
                "WarningThresholdInMB": 115200  # 112.5GB
            }
        }
        
        recovery = {
            "DefaultHostIdentifier": selected_host["HostIdentifier"],
            "DefaultDatastoreIdentifier": selected_datastore["DatastoreIdentifier"],
            "DefaultResourcePoolIdentifier": selected_pool["ResourcePoolIdentifier"],
            "DefaultFolderIdentifier": root_folder["FolderIdentifier"]
        }
        
        networks = {
            "Failover": {
                "Hypervisor": {
                    "DefaultNetworkIdentifier": selected_network["NetworkIdentifier"]
                }
            },
            "FailoverTest": {
                "Hypervisor": {
                    "DefaultNetworkIdentifier": selected_network["NetworkIdentifier"]
                }
            }
        }
        
        # Create the VPG
        try:
            vpg_id = self.zvma_client.vpgs.create_vpg(
                basic=basic,
                journal=journal,
                recovery=recovery,
                networks=networks,
                sync=True
            )
            return f"VPG {params['name']} created successfully. VPG ID: {vpg_id}"
        except Exception as e:
            return f"Failed to create VPG: {str(e)}"

    def _handle_delete_vpg(self, params):
        vpg_name = params.get("vpg_name")
        force = params.get("force", False)
        keep_recovery_volumes = params.get("keep_recovery_volumes", True)
        task_id = self.zvma_client.vpgs.delete_vpg(
            vpg_name, 
            force=force, 
            keep_recovery_volumes=keep_recovery_volumes
        )
        return f"Deleting VPG {vpg_name}. Task ID: {task_id}"

    def _handle_add_vm_to_vpg(self, params):
        """Handle adding a VM to an existing VPG with interactive resource selection"""
        vpg_name = params.get("vpg_name")
        vm_name = params.get("vm_name")
        
        # Get local site identifier
        local_site = self.zvma_client.localsite.get_local_site()
        local_site_identifier = local_site.get('SiteIdentifier')
        
        # Get peer site information
        virtualization_sites = self.zvma_client.virtualization_sites.get_virtualization_sites()
        peer_site = next((site for site in virtualization_sites 
                         if site['SiteIdentifier'] != local_site_identifier), None)
        
        if not peer_site:
            return "No peer site found. Please configure site pairing first."
        
        peer_site_identifier = peer_site['SiteIdentifier']
        
        # Get VM identifier using virtualization_sites API
        vms = self.zvma_client.virtualization_sites.get_virtualization_site_vms(
            site_identifier=local_site_identifier
        )
        
        vm_identifier = None
        for vm in vms:
            if vm.get('VmName') == vm_name:
                vm_identifier = vm.get('VmIdentifier')
                break
        
        if not vm_identifier:
            return f"VM {vm_name} not found"
        
        # Get available resources from peer site
        print("\nGetting available resources from peer site...")
        
        # Get and display available hosts
        hosts = self.zvma_client.virtualization_sites.get_virtualization_site_hosts(
            site_identifier=peer_site_identifier
        )
        logging.info(f"Hosts: {json.dumps(hosts, indent=4)}")
        print("\nAvailable Hosts:")
        for i, host in enumerate(hosts, 1):
            print(f"{i}. {host.get('VirtualizationHostName', 'Unknown')}")
        
        host_choice = int(input("\nSelect host number: ")) - 1
        selected_host = hosts[host_choice]
        
        # Get and display available datastores
        datastores = self.zvma_client.virtualization_sites.get_virtualization_site_datastores(
            site_identifier=peer_site_identifier
        )
        logging.debug(f"Datastores: {json.dumps(datastores, indent=4)}")

        print("\nAvailable Datastores:")
        for i, ds in enumerate(datastores, 1):
            print(f"{i}. {ds.get('DatastoreName')} (DatastoreIdentifier: {ds.get('DatastoreIdentifier', 'Unknown')})")
        
        ds_choice = int(input("\nSelect datastore number: ")) - 1
        selected_datastore = datastores[ds_choice]
        
        # Get and display available folders
        folders = self.zvma_client.virtualization_sites.get_virtualization_site_folders(
            site_identifier=peer_site_identifier
        )
        logging.debug(f"Folders: {json.dumps(folders, indent=4)}")
        print("\nAvailable Folders:")
        for i, folder in enumerate(folders, 1):
            print(f"{i}. {folder.get('FolderName', 'Unknown')} (FolderIdentifier: {folder.get('FolderIdentifier', 'Unknown')})")
        
        folder_choice = int(input("\nSelect folder number: ")) - 1
        selected_folder = folders[folder_choice]
        
        # Construct VM payload
        vm_payload = {
            "VmIdentifier": vm_identifier,
            "Recovery": {
                "HostIdentifier": selected_host["HostIdentifier"],
                "DatastoreIdentifier": selected_datastore["DatastoreIdentifier"],
                "FolderIdentifier": selected_folder["FolderIdentifier"]
            }
        }
        
        # Add VM to VPG using the constructed payload
        try:
            task_id = self.zvma_client.vpgs.add_vm_to_vpg(vpg_name, vm_list_payload=vm_payload)
            return f"Added VM {vm_name} to VPG {vpg_name}. Task ID: {task_id}"
        except Exception as e:
            return f"Failed to add VM to VPG: {str(e)}"

    def _handle_create_vpg_checkpoint(self, params):
        vpg_name = params.get("vpg_name")
        checkpoint_name = params.get("checkpoint_name")
        task_id = self.zvma_client.vpgs.create_checkpoint(checkpoint_name, vpg_name=vpg_name)
        return f"Created checkpoint '{checkpoint_name}' for VPG {vpg_name}. Task ID: {task_id}"

    def _handle_list_suspected_volumes(self, params):
        volumes = self.zvma_client.encryptiondetection.list_suspected_volumes()
        if not volumes:
            return "No suspected encrypted volumes found."
        return self._format_suspected_volumes(volumes)

    def _handle_get_encryption_detection_types(self, params):
        types = self.zvma_client.encryptiondetection.get_encryption_detection_types()
        return self._format_detection_types(types)

    def _handle_get_recovery_reports(self, params):
        reports = self.zvma_client.recovery_reports.get_recovery_reports(**params)
        if not reports:
            return "No recovery reports found."
        return self._format_recovery_reports(reports)

    def _handle_get_recovery_scripts(self, params):
        scripts = self.zvma_client.recoveryscripts.get_recovery_scripts()
        if not scripts:
            return "No recovery scripts found."
        return self._format_recovery_scripts(scripts)

    def _handle_create_vra(self, params):
        payload = {
            "HostName": params["host_name"],
            "NetworkName": params["network_name"],
            "IpConfigType": params["ip_config_type"]
        }
        
        if params["ip_config_type"] == "Static":
            payload.update({
                "IpAddress": params["ip_address"],
                "SubnetMask": params["subnet_mask"],
                "DefaultGateway": params["default_gateway"]
            })
        
        result = self.zvma_client.vras.create_vra(payload, sync=True)
        return f"VRA deployment initiated: {result}"

    def _handle_delete_vra(self, params):
        result = self.zvma_client.vras.delete_vra(params["vra_identifier"], sync=True)
        return f"VRA deletion initiated: {result}"

    def _handle_upgrade_vra(self, params):
        result = self.zvma_client.vras.upgrade_vra(params["vra_identifier"])
        return f"VRA upgrade initiated: {result}"

    def _handle_pair_site(self, params):
        hostname = params["hostname"]
        port = params.get("port", 9071)
        
        # First generate a pairing token
        token = self.zvma_client.peersites.generate_token()
        
        # Then pair the site
        result = self.zvma_client.peersites.pair_site(hostname, token, port)
        return f"Site pairing initiated with {hostname}: {result}"

    def _handle_unpair_site(self, params):
        result = self.zvma_client.peersites.delete_peer_site(params["site_identifier"])
        return f"Site unpairing completed: {result}"

    def _handle_update_license(self, params):
        result = self.zvma_client.license.update_license(params["license_key"])
        return f"License update result: {result}"

    def _handle_list_volumes(self, params):
        volumes = self.zvma_client.volumes.list_volumes(
            vm_name=params["vm_name"],
            include_temp=params.get("include_temp", False)
        )
        if not volumes:
            return f"No volumes found for VM {params['vm_name']}"
        return self._format_volumes(volumes)

    def _handle_get_volume_info(self, params):
        volume_info = self.zvma_client.volumes.get_volume_info(
            params["volume_id"],
            vm_name=params["vm_name"]
        )
        if not volume_info:
            return f"No information found for volume {params['volume_id']}"
        return self._format_volume_details(volume_info)

    def _handle_list_tasks(self, params):
        tasks = self.zvma_client.tasks.list_tasks(
            status=params.get("status"),
            type=params.get("type"),
            limit=params.get("limit", 10)
        )
        if not tasks:
            return "No tasks found"
        return self._format_tasks(tasks)

    def _handle_get_task_info(self, params):
        task_info = self.zvma_client.tasks.get_task(params["task_id"])
        if not task_info:
            return f"No information found for task {params['task_id']}"
        return self._format_task_details(task_info)

    def _handle_list_service_profiles(self, params):
        profiles = self.zvma_client.service_profiles.list_service_profiles()
        if not profiles:
            return "No service profiles found"
        return self._format_service_profiles(profiles)

    def _handle_create_service_profile(self, params):
        profile = self.zvma_client.service_profiles.create_service_profile(
            name=params["name"],
            description=params.get("description", ""),
            rpo=params["rpo"],
            history=params["history"]
        )
        return f"Service profile created: {profile['Name']}"

    def _handle_get_session_info(self, params):
        session_info = self.zvma_client.sessions.get_session()
        return self._format_session_info(session_info)

    def _handle_list_repositories(self, params):
        repositories = self.zvma_client.repositories.list_repositories()
        if not repositories:
            return "No repositories found"
        return self._format_repositories(repositories)

    def _handle_add_repository(self, params):
        repository = self.zvma_client.repositories.add_repository(
            name=params["name"],
            path=params["path"],
            type=params["type"],
            capacity_in_gb=params.get("capacity_in_gb")
        )
        return f"Repository added: {repository['Name']}"

    def _handle_get_server_time(self, params):
        time_info = self.zvma_client.server_date_time.get_server_time()
        return self._format_server_time(time_info)

    def _handle_list_zorgs(self, params):
        zorgs = self.zvma_client.zorgs.list_zorgs(name=params.get("name"))
        if not zorgs:
            return "No ZORGs found"
        return self._format_zorgs(zorgs)

    def _handle_create_zorg(self, params):
        zorg = self.zvma_client.zorgs.create_zorg(
            name=params["name"],
            contact_name=params.get("contact_name"),
            contact_email=params.get("contact_email"),
            contact_phone=params.get("contact_phone")
        )
        return f"ZORG created: {zorg['Name']}"

    def _handle_list_virtualization_sites(self, params):
        sites = self.zvma_client.virtualization_sites.list_sites(
            type=params.get("type"),
            status=params.get("status")
        )
        if not sites:
            return "No virtualization sites found"
        return self._format_virtualization_sites(sites)

    def _handle_get_site_settings(self, params):
        settings = self.zvma_client.virtualization_sites.get_site_settings(
            params["site_identifier"]
        )
        return self._format_site_settings(settings)

    def _handle_update_site_settings(self, params):
        site_id = params.pop("site_identifier")
        settings = self.zvma_client.virtualization_sites.update_site_settings(
            site_id,
            **params
        )
        return f"Site settings updated for {site_id}"

    def _handle_list_events(self, params):
        events = self.zvma_client.events.list_events(
            category=params.get("category"),
            from_date=params.get("from_date"),
            to_date=params.get("to_date"),
            limit=params.get("limit", 100)
        )
        if not events:
            return "No events found"
        return self._format_events(events)

    def _handle_get_event_details(self, params):
        event = self.zvma_client.events.get_event(params["event_id"])
        if not event:
            return f"No event found with ID {params['event_id']}"
        return self._format_event_details(event)

    def _handle_add_recovery_script(self, params):
        script = self.zvma_client.recoveryscripts.add_recovery_script(
            name=params["name"],
            description=params.get("description", ""),
            script_content=params["script_content"],
            timeout=params.get("timeout", 300)
        )
        return f"Recovery script added: {script['Name']}"

    def _handle_delete_recovery_script(self, params):
        result = self.zvma_client.recoveryscripts.delete_recovery_script(params["script_id"])
        return f"Recovery script deleted: {result}"

    def _handle_get_system_settings(self, params):
        settings = self.zvma_client.tweaks.get_system_settings(
            category=params.get("category")
        )
        return self._format_system_settings(settings)

    def _handle_update_system_settings(self, params):
        result = self.zvma_client.tweaks.update_system_settings(**params)
        return "System settings updated successfully"

    def _handle_create_vm_snapshot(self, params):
        result = self.zvma_client.vms.create_snapshot(
            vm_name=params["vm_name"],
            snapshot_name=params["snapshot_name"],
            description=params.get("description", ""),
            memory=params.get("memory", False)
        )
        return f"Created snapshot '{params['snapshot_name']}' for VM {params['vm_name']}"

    def _handle_remove_vm_snapshot(self, params):
        result = self.zvma_client.vms.remove_snapshot(
            vm_name=params["vm_name"],
            snapshot_name=params["snapshot_name"]
        )
        return f"Removed snapshot '{params['snapshot_name']}' from VM {params['vm_name']}"

    def _handle_get_vm_nics(self, params):
        nics = self.zvma_client.vms.get_network_interfaces(params["vm_name"])
        if not nics:
            return f"No network interfaces found for VM {params['vm_name']}"
        return self._format_vm_nics(nics)

    def _handle_update_vm_network(self, params):
        result = self.zvma_client.vms.update_network_interface(
            vm_name=params["vm_name"],
            nic_id=params["nic_id"],
            network_name=params["network_name"],
            ip_address=params.get("ip_address"),
            subnet_mask=params.get("subnet_mask")
        )
        return f"Updated network settings for VM {params['vm_name']}"

    def _handle_get_network_stats(self, params):
        stats = self.zvma_client.networks.get_statistics(
            entity_type=params["entity_type"],
            entity_name=params["entity_name"],
            timeframe=params.get("timeframe", "24hours")
        )
        return self._format_network_stats(stats)

    def _handle_create_backup(self, params):
        result = self.zvma_client.backups.create_backup(
            vpg_name=params["vpg_name"],
            backup_name=params["backup_name"],
            repository_name=params["repository_name"]
        )
        return f"Backup creation initiated for VPG {params['vpg_name']}: {result}"

    def _handle_restore_backup(self, params):
        result = self.zvma_client.backups.restore_backup(
            backup_name=params["backup_name"],
            target_datastore=params["target_datastore"],
            power_on=params.get("power_on", False)
        )
        return f"Backup restore initiated: {result}"

    def _handle_get_resource_usage(self, params):
        stats = self.zvma_client.monitoring.get_resource_usage(
            resource_type=params["resource_type"],
            timeframe=params.get("timeframe", "24hours"),
            entity_type=params.get("entity_type")
        )
        return self._format_resource_usage(stats)

    def _handle_get_performance_metrics(self, params):
        metrics = self.zvma_client.monitoring.get_performance_metrics(
            metric_type=params["metric_type"],
            vpg_name=params.get("vpg_name"),
            interval=params.get("interval", "1hour")
        )
        return self._format_performance_metrics(metrics)

    def _handle_get_replication_status(self, params):
        status = self.zvma_client.monitoring.get_replication_status(
            vpg_name=params["vpg_name"],
            include_details=params.get("include_details", False)
        )
        return self._format_replication_status(status)

    def _handle_generate_site_report(self, params):
        report_data = self.zvma_client.reporting.generate_site_report(
            report_type=params["report_type"],
            time_range=params.get("time_range", "24hours"),
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            export_format=params.get("export_format", "JSON")
        )
        return self._format_site_report(report_data)

    def _handle_analyze_performance_trends(self, params):
        trends = self.zvma_client.analytics.analyze_performance_trends(
            metric=params["metric"],
            period=params["period"],
            vpg_name=params.get("vpg_name")
        )
        return self._format_performance_trends(trends)

    def _handle_get_sla_compliance(self, params):
        compliance = self.zvma_client.analytics.get_sla_compliance(
            vpg_name=params.get("vpg_name"),
            time_range=params.get("time_range", "24hours"),
            include_details=params.get("include_details", False)
        )
        return self._format_sla_compliance(compliance)

    def _handle_get_capacity_planning(self, params):
        planning = self.zvma_client.analytics.get_capacity_planning(
            resource_type=params["resource_type"],
            forecast_period=params["forecast_period"],
            include_recommendations=params.get("include_recommendations", True)
        )
        return self._format_capacity_planning(planning)

    def _handle_get_protection_assessment(self, params):
        assessment = self.zvma_client.analytics.get_protection_assessment(
            assessment_type=params["assessment_type"],
            include_recommendations=params.get("include_recommendations", True)
        )
        return self._format_protection_assessment(assessment)

    def _handle_run_health_check(self, params):
        check_type = params["check_type"]
        components = params.get("components", [])
        
        if check_type == "Custom" and not components:
            return "Custom health check requires specific components to check"
        
        results = {}
        
        # VPG Health Check
        if check_type in ["Full", "Quick"] or "VPGs" in components:
            vpg_health = self._check_vpg_health()
            results["VPGs"] = vpg_health
        
        # VRA Health Check
        if check_type == "Full" or "VRAs" in components:
            vra_health = self._check_vra_health()
            results["VRAs"] = vra_health
        
        # Network Health Check
        if check_type == "Full" or "Networks" in components:
            network_health = self._check_network_health()
            results["Networks"] = network_health
        
        # Storage Health Check
        if check_type == "Full" or "Storage" in components:
            storage_health = self._check_storage_health()
            results["Storage"] = storage_health
        
        # Connectivity Health Check
        if check_type in ["Full", "Quick"] or "Connectivity" in components:
            connectivity_health = self._check_connectivity_health()
            results["Connectivity"] = connectivity_health
        
        return self._format_health_check_results(results)

    def _handle_schedule_health_check(self, params):
        schedule = {
            "frequency": params["frequency"],
            "time": params["time"],
            "day": params.get("day")
        }
        
        # Store the schedule in the system
        result = self.zvma_client.monitoring.schedule_health_check(**schedule)
        return f"Health check scheduled: {result}"

    def _handle_run_dr_test(self, params):
        test_config = {
            "vpg_name": params["vpg_name"],
            "test_type": params["test_type"],
            "test_network": params.get("test_network"),
            "run_scripts": params.get("run_scripts", False),
            "validate_apps": params.get("validate_apps", False)
        }
        
        # Initialize test
        test_id = self.zvma_client.testing.initialize_dr_test(**test_config)
        
        # Start test execution
        result = self.zvma_client.testing.execute_dr_test(test_id)
        
        return self._format_dr_test_results(result)

    def _handle_schedule_dr_test(self, params):
        schedule = {
            "vpg_name": params["vpg_name"],
            "frequency": params["frequency"],
            "test_type": params["test_type"],
            "notification_email": params.get("notification_email")
        }
        
        # Store the DR test schedule
        result = self.zvma_client.testing.schedule_dr_test(**schedule)
        return f"DR test scheduled for VPG {params['vpg_name']}: {result}"

    def _check_vpg_health(self):
        vpgs = self.zvma_client.vpgs.list_vpgs()
        logging.info(f"VPGS: {json.dumps(vpgs, indent=4)}")
        health_status = {
            "total": len(vpgs),
            "meeting_sla": 0,
            "not_meeting_sla": 0,
            "issues": []
        }
        
        for vpg in vpgs:
            if vpg.get("Status") == "MeetingSLA":
                health_status["meeting_sla"] += 1
            else:
                health_status["not_meeting_sla"] += 1
                health_status["issues"].append({
                    "vpg": vpg["VpgName"],
                    "status": vpg["Status"],
                    "issue": vpg.get("StatusDescription")
                })
        
        return health_status

    def _check_vra_health(self):
        vras = self.zvma_client.vras.list_vras()
        health_status = {
            "total": len(vras),
            "healthy": 0,
            "issues": []
        }
        
        for vra in vras:
            if vra.get("Status") == "Normal":
                health_status["healthy"] += 1
            else:
                health_status["issues"].append({
                    "vra": vra["VraName"],
                    "status": vra["Status"],
                    "issue": vra.get("StatusDescription")
                })
        
        return health_status

    def _check_network_health(self):
        # Check network connectivity and performance
        return self.zvma_client.networks.check_health()

    def _check_storage_health(self):
        # Check storage capacity and performance
        return self.zvma_client.monitoring.check_storage_health()

    def _check_connectivity_health(self):
        # Check connectivity between sites and components
        return self.zvma_client.monitoring.check_connectivity()

    def _format_health_check_results(self, results):
        output = ["Health Check Results:"]
        
        for component, status in results.items():
            output.append(f"\n{component} Health:")
            
            if component == "VPGs":
                output.append(
                    f"Total VPGs: {status['total']}\n"
                    f"Meeting SLA: {status['meeting_sla']}\n"
                    f"Not Meeting SLA: {status['not_meeting_sla']}"
                )
                if status['issues']:
                    output.append("\nIssues:")
                    for issue in status['issues']:
                        output.append(f"- VPG {issue['vpg']}: {issue['issue']}")
            
            elif component == "VRAs":
                output.append(
                    f"Total VRAs: {status['total']}\n"
                    f"Healthy: {status['healthy']}"
                )
                if status['issues']:
                    output.append("\nIssues:")
                    for issue in status['issues']:
                        output.append(f"- VRA {issue['vra']}: {issue['issue']}")
            
            else:
                output.append(f"Status: {status.get('Status', 'Unknown')}")
                if status.get('Issues'):
                    output.append("Issues:")
                    for issue in status['Issues']:
                        output.append(f"- {issue}")
        
        return "\n".join(output)

    def _format_dr_test_results(self, results):
        return (
            f"DR Test Results:\n"
            f"Test ID: {results.get('TestId', 'Unknown')}\n"
            f"Status: {results.get('Status', 'Unknown')}\n"
            f"Start Time: {results.get('StartTime', 'Unknown')}\n"
            f"Duration: {results.get('Duration', 'Unknown')}\n\n"
            f"Test Steps:\n" +
            "\n".join([
                f"- {step['Name']}: {step['Status']}"
                for step in results.get('Steps', [])
            ]) +
            f"\n\nValidation Results:\n" +
            "\n".join([
                f"- {check['Name']}: {check['Result']}"
                for check in results.get('Validations', [])
            ])
        )

    def _handle_configure_alert_settings(self, params):
        alert_config = {
            "AlertType": params["alert_type"],
            "Enabled": params["enabled"],
            "Recipients": params.get("recipients", []),
            "SeverityLevel": params.get("severity_level", "Warning"),
            "NotificationTimeout": params.get("notification_timeout", 30)
        }
        
        result = self.zvma_client.alerts.configure_alert_settings(**alert_config)
        return f"Alert settings configured for {params['alert_type']}: {result}"

    def _handle_configure_external_monitoring(self, params):
        monitoring_config = {
            "SystemType": params["system_type"],
            "EndpointUrl": params["endpoint_url"],
            "AuthToken": params.get("auth_token"),
            "Metrics": params.get("metrics", ["Health"]),
            "Interval": params.get("interval", 5)
        }
        
        result = self.zvma_client.monitoring.configure_external_monitoring(**monitoring_config)
        return self._format_monitoring_config(result)

    def _handle_create_alert_rule(self, params):
        rule_config = {
            "Name": params["name"],
            "Condition": params["condition"],
            "Severity": params["severity"],
            "EntityType": params.get("entity_type"),
            "Actions": params.get("actions", ["Email"])
        }
        
        result = self.zvma_client.alerts.create_alert_rule(**rule_config)
        return f"Alert rule '{params['name']}' created: {result}"

    def _handle_configure_monitoring_thresholds(self, params):
        threshold_config = {
            "MetricType": params["metric_type"],
            "WarningThreshold": params["warning_threshold"],
            "ErrorThreshold": params["error_threshold"],
            "MeasurementPeriod": params.get("measurement_period", "15min"),
            "EntityType": params.get("entity_type")
        }
        
        result = self.zvma_client.monitoring.configure_thresholds(**threshold_config)
        return self._format_threshold_config(result)

    def _format_monitoring_config(self, config):
        return (
            f"External Monitoring Configuration:\n"
            f"System: {config.get('SystemType', 'Unknown')}\n"
            f"Endpoint: {config.get('EndpointUrl', 'Unknown')}\n"
            f"Metrics: {', '.join(config.get('Metrics', []))}\n"
            f"Interval: {config.get('Interval', 'Unknown')} minutes\n"
            f"Status: {config.get('Status', 'Unknown')}\n"
            f"Last Sync: {config.get('LastSync', 'Never')}"
        )

    def _format_threshold_config(self, config):
        return (
            f"Monitoring Threshold Configuration:\n"
            f"Metric: {config.get('MetricType', 'Unknown')}\n"
            f"Warning Threshold: {config.get('WarningThreshold', 'Unknown')}\n"
            f"Error Threshold: {config.get('ErrorThreshold', 'Unknown')}\n"
            f"Measurement Period: {config.get('MeasurementPeriod', 'Unknown')}\n"
            f"Entity Type: {config.get('EntityType', 'Unknown')}\n"
            f"Status: {config.get('Status', 'Unknown')}"
        )

    def _create_analysis_agent(self):
        """Create a specialized analysis agent for interpreting VPG data and user intent"""
        return {
            "role": "system",
            "content": """You are a specialized analysis agent for Zerto operations.
            Your tasks are to:
            1. Analyze VPG data and understand the current state
            2. Interpret user queries and their intent
            3. Identify relevant VPGs based on the query
            4. Recommend and execute appropriate actions
            5. Provide concise, relevant information based on context

            Format your response as JSON:
            {
                "analysis": {
                    "relevant_vpgs": [],
                    "current_state": "",
                    "user_intent": "",
                    "recommended_action": ""
                },
                "action": {
                    "function": "",
                    "parameters": {},
                    "reason": ""
                },
                "display": {
                    "summary": "",
                    "details": []
                }
            }"""
        }

    def process_query(self, user_query):
        """Process user query by calling appropriate function handler"""
        try:
            # First, check if this is a Zerto-related query
            classify_messages = [
                {
                    "role": "system",
                    "content": "You are a classifier. Respond with 'ZERTO' if the query is about Zerto operations (VPGs, failover, etc), or 'CHAT' if it's a general conversation (greetings, thanks, weather, etc)."
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ]

            classify_response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=classify_messages
            )
            
            query_type = classify_response.choices[0].message.content
            logging.info(f"Query type: {query_type}")

            if query_type == "CHAT":
                chat_messages = [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Keep responses brief and always end by mentioning that you're primarily focused on Zerto operations."
                    },
                    {
                        "role": "user",
                        "content": user_query
                    }
                ]
                chat_response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=chat_messages
                )
                return f"{chat_response.choices[0].message.content}\n\nI'm primarily focused on Zerto operations like managing VPGs, failover testing, etc. How can I help you with those?"

            # If it's a Zerto query, process normally
            messages = [
                {
                    "role": "system",
                    "content": """You are a Zerto operations assistant. Match user queries to the appropriate function:
                    - "stop failover test" -> stop_failover_test function
                    - "start failover test" -> start_failover_test function
                    - "create vpg" -> ASK_VPG_NAME function
                    - "delete vpg" -> delete_vpg function
                    - "list vpgs" -> list_vpgs function
                    
                    When no VPG name is provided, use empty parameters and let the code handle the prompting."""
                },
                {
                    "role": "user",
                    "content": f"Based on the user query: '{user_query}', determine which function to call and its parameters."
                }
            ]

            logging.info(f"process_query: {user_query}")
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                functions=self._define_functions(),
                function_call="auto"
            )

            function_call = response.choices[0].message.function_call
            logging.info(f"process_query: Function call: {function_call}")
            
            if function_call:
                function_name = function_call.name
                function_params = json.loads(function_call.arguments) if function_call.arguments else {}
                logging.info(f"process_query: Function name: {function_name}, params: {function_params}")
                
                if function_name in ["delete_vpg", "start_failover_test", "stop_failover_test"]:
                    vpg_name = function_params.get("vpg_name")
                    if not vpg_name or vpg_name in ["specify VPG name", "specify the VPG name"]:
                        vpg_name = input(f"\nPlease enter the VPG name for {function_name}: ")
                        function_params["vpg_name"] = vpg_name
                
                return self.handle_function(function_name, function_params)
            
            return "Please be more specific. Available commands include:\n- start failover test\n- stop failover test\n- create vpg\n- delete vpg\n- list vpgs"

        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            return f"Error processing query: {str(e)}"

    def _format_alerts(self, alerts):
        return "\n".join([
            f"Alert: {alert.get('Description', 'Unknown')}\n"
            f"- Level: {alert.get('Level', 'Unknown')}\n"
            f"- Status: {alert.get('Status', 'Unknown')}\n"
            f"- Entity: {alert.get('Entity', 'Unknown')}\n"
            f"- Time: {alert.get('TurnedOn', 'Unknown')}"
            for alert in alerts
        ])

    def _format_suspected_volumes(self, volumes):
        return "\n".join([
            f"Volume: {vol.get('VolumeName', 'Unknown')}\n"
            f"- VM: {vol.get('VMName', 'Unknown')}\n"
            f"- Detection Type: {vol.get('DetectionType', 'Unknown')}\n"
            f"- Confidence: {vol.get('Confidence', 'Unknown')}%\n"
            f"- Last Detected: {vol.get('LastDetected', 'Unknown')}"
            for vol in volumes
        ])

    def _format_detection_types(self, types):
        return "\n".join([
            f"Type: {t.get('Name', 'Unknown')}\n"
            f"- Description: {t.get('Description', 'Unknown')}\n"
            f"- Confidence Level: {t.get('ConfidenceLevel', 'Unknown')}"
            for t in types
        ])

    def _format_recovery_reports(self, reports):
        return "\n".join([
            f"Report: {report.get('Name', 'Unknown')}\n"
            f"- Operation Type: {report.get('OperationType', 'Unknown')}\n"
            f"- Start Time: {report.get('StartTime', 'Unknown')}\n"
            f"- End Time: {report.get('EndTime', 'Unknown')}\n"
            f"- Status: {report.get('Status', 'Unknown')}\n"
            f"- Duration: {report.get('Duration', 'Unknown')}"
            for report in reports
        ])

    def _format_recovery_scripts(self, scripts):
        return "\n".join([
            f"Script: {script.get('Name', 'Unknown')}\n"
            f"- Description: {script.get('Description', 'Unknown')}\n"
            f"- Type: {script.get('Type', 'Unknown')}\n"
            f"- Timeout: {script.get('Timeout', 'Unknown')} seconds"
            for script in scripts
        ])

    def _format_volumes(self, volumes):
        return "\n".join([
            f"Volume: {vol.get('Name', 'Unknown')}\n"
            f"- Size: {vol.get('SizeInGB', 'Unknown')} GB\n"
            f"- Type: {vol.get('VolumeType', 'Unknown')}\n"
            f"- Status: {vol.get('Status', 'Unknown')}\n"
            f"- Datastore: {vol.get('Datastore', 'Unknown')}"
            for vol in volumes
        ])

    def _format_volume_details(self, volume):
        return (
            f"Volume Details:\n"
            f"Name: {volume.get('Name', 'Unknown')}\n"
            f"Size: {volume.get('SizeInGB', 'Unknown')} GB\n"
            f"Type: {volume.get('VolumeType', 'Unknown')}\n"
            f"Status: {volume.get('Status', 'Unknown')}\n"
            f"Provisioned: {volume.get('ProvisionedSizeInGB', 'Unknown')} GB\n"
            f"Path: {volume.get('Path', 'Unknown')}\n"
            f"Format: {volume.get('Format', 'Unknown')}"
        )

    def _format_tasks(self, tasks):
        return "\n".join([
            f"Task: {task.get('TaskIdentifier', 'Unknown')}\n"
            f"- Type: {task.get('Type', 'Unknown')}\n"
            f"- Status: {task.get('Status', 'Unknown')}\n"
            f"- Progress: {task.get('Progress', 0)}%\n"
            f"- Started: {task.get('StartTime', 'Unknown')}"
            for task in tasks
        ])

    def _format_task_details(self, task):
        return (
            f"Task Details:\n"
            f"Identifier: {task.get('TaskIdentifier', 'Unknown')}\n"
            f"Type: {task.get('Type', 'Unknown')}\n"
            f"Status: {task.get('Status', 'Unknown')}\n"
            f"Progress: {task.get('Progress', 0)}%\n"
            f"Started: {task.get('StartTime', 'Unknown')}\n"
            f"Completed: {task.get('EndTime', 'Unknown')}\n"
            f"Result: {task.get('Result', 'Unknown')}\n"
            f"Description: {task.get('Description', 'Unknown')}"
        )

    def _format_service_profiles(self, profiles):
        return "\n".join([
            f"Profile: {profile.get('Name', 'Unknown')}\n"
            f"- Description: {profile.get('Description', 'N/A')}\n"
            f"- RPO: {profile.get('RPO', 'Unknown')} seconds\n"
            f"- History: {profile.get('History', 'Unknown')} hours"
            for profile in profiles
        ])

    def _format_session_info(self, session):
        return (
            f"Session Information:\n"
            f"User: {session.get('UserName', 'Unknown')}\n"
            f"Role: {session.get('Role', 'Unknown')}\n"
            f"Session ID: {session.get('SessionId', 'Unknown')}\n"
            f"Started: {session.get('StartTime', 'Unknown')}\n"
            f"Expires: {session.get('ExpiryTime', 'Unknown')}"
        )

    def _format_repositories(self, repositories):
        return "\n".join([
            f"Repository: {repo.get('Name', 'Unknown')}\n"
            f"- Type: {repo.get('Type', 'Unknown')}\n"
            f"- Path: {repo.get('Path', 'Unknown')}\n"
            f"- Capacity: {repo.get('CapacityInGB', 'Unknown')} GB\n"
            f"- Free Space: {repo.get('FreeSpaceInGB', 'Unknown')} GB"
            for repo in repositories
        ])

    def _format_server_time(self, time_info):
        return (
            f"Server Time Information:\n"
            f"Current Time: {time_info.get('CurrentTime', 'Unknown')}\n"
            f"Time Zone: {time_info.get('TimeZone', 'Unknown')}\n"
            f"UTC Offset: {time_info.get('UTCOffset', 'Unknown')}"
        )

    def _format_zorgs(self, zorgs):
        return "\n".join([
            f"ZORG: {zorg.get('Name', 'Unknown')}\n"
            f"- Contact: {zorg.get('ContactName', 'N/A')}\n"
            f"- Email: {zorg.get('ContactEmail', 'N/A')}\n"
            f"- Phone: {zorg.get('ContactPhone', 'N/A')}\n"
            f"- Status: {zorg.get('Status', 'Unknown')}"
            for zorg in zorgs
        ])

    def _format_vm_nics(self, nics):
        return "\n".join([
            f"Network Interface: {nic.get('Name', 'Unknown')}\n"
            f"- MAC Address: {nic.get('MacAddress', 'Unknown')}\n"
            f"- Network: {nic.get('NetworkName', 'Unknown')}\n"
            f"- IP Address: {nic.get('IpAddress', 'Unknown')}\n"
            f"- Connected: {nic.get('Connected', 'Unknown')}"
            for nic in nics
        ])

    def _format_network_stats(self, stats):
        return (
            f"Network Statistics:\n"
            f"Throughput:\n"
            f"- Current: {stats.get('CurrentThroughputMbps', 'Unknown')} Mbps\n"
            f"- Average: {stats.get('AverageThroughputMbps', 'Unknown')} Mbps\n"
            f"- Peak: {stats.get('PeakThroughputMbps', 'Unknown')} Mbps\n"
            f"Packet Loss: {stats.get('PacketLossPercentage', 'Unknown')}%\n"
            f"Latency: {stats.get('LatencyMs', 'Unknown')} ms\n"
            f"Period: {stats.get('Period', 'Unknown')}"
        )

    def _handle_get_encryption_status(self, params):
        status = self.zvma_client.encryptiondetection.get_encryption_status(
            vm_name=params.get("vm_name"),
            include_history=params.get("include_history", False)
        )
        return self._format_encryption_status(status)

    def _handle_update_detection_settings(self, params):
        settings = {
            "DetectionTypes": params["detection_types"],
            "ScanInterval": params.get("scan_interval", 24),
            "ConfidenceThreshold": params.get("confidence_threshold", 80)
        }
        result = self.zvma_client.encryptiondetection.update_settings(**settings)
        return f"Detection settings updated: {result}"

    def _format_encryption_status(self, status):
        basic_info = (
            f"Encryption Detection Status:\n"
            f"Total Volumes Scanned: {status.get('TotalVolumes', 0)}\n"
            f"Suspected Volumes: {status.get('SuspectedVolumes', 0)}\n"
            f"Last Scan: {status.get('LastScan', 'Never')}\n"
        )
        
        if status.get('Details'):
            details = "\nDetailed Results:\n" + "\n".join([
                f"Volume: {vol['Name']}\n"
                f"- Detection Type: {vol['DetectionType']}\n"
                f"- Confidence: {vol['Confidence']}%\n"
                f"- Last Detected: {vol['LastDetected']}"
                for vol in status['Details']
            ])
            return basic_info + details
        
        return basic_info

    def _handle_update_recovery_script(self, params):
        script_id = params["script_id"]
        update_data = {k: v for k, v in params.items() if k != "script_id" and v is not None}
        result = self.zvma_client.recoveryscripts.update_script(script_id, **update_data)
        return f"Recovery script updated: {result}"

    def _handle_test_recovery_script(self, params):
        result = self.zvma_client.recoveryscripts.test_script(
            params["script_id"],
            test_parameters=params.get("test_parameters", {})
        )
        return self._format_script_test_results(result)

    def _format_script_test_results(self, results):
        return (
            f"Script Test Results:\n"
            f"Status: {results.get('Status', 'Unknown')}\n"
            f"Duration: {results.get('Duration', 'Unknown')} seconds\n"
            f"Exit Code: {results.get('ExitCode', 'Unknown')}\n"
            f"Output:\n{results.get('Output', 'No output')}\n"
            f"Errors:\n{results.get('Errors', 'No errors')}"
        )

    def _handle_cancel_task(self, params):
        result = self.zvma_client.tasks.cancel_task(
            params["task_id"],
            force=params.get("force", False)
        )
        return f"Task cancellation result: {result}"

    def _handle_get_task_history(self, params):
        history = self.zvma_client.tasks.get_task_history(**params)
        return self._format_task_history(history)

    def _format_task_history(self, history):
        return "\n".join([
            f"Task: {task.get('TaskIdentifier', 'Unknown')}\n"
            f"- Type: {task.get('Type', 'Unknown')}\n"
            f"- Status: {task.get('Status', 'Unknown')}\n"
            f"- Started: {task.get('StartTime', 'Unknown')}\n"
            f"- Completed: {task.get('EndTime', 'Unknown')}\n"
            f"- Duration: {task.get('Duration', 'Unknown')}"
            for task in history
        ])

    def _handle_get_security_posture(self, params):
        categories = params.get("categories", ["Access", "Network", "Data", "Compliance"])
        include_details = params.get("include_details", False)
        
        posture = {}
        
        # Check access security
        if "Access" in categories:
            posture["Access"] = self.zvma_client.security.check_access_security()
        
        # Check network security
        if "Network" in categories:
            posture["Network"] = self.zvma_client.security.check_network_security()
        
        # Check data security
        if "Data" in categories:
            posture["Data"] = self.zvma_client.security.check_data_security()
        
        # Check compliance status
        if "Compliance" in categories:
            posture["Compliance"] = self.zvma_client.security.check_compliance_status()
        
        return self._format_security_posture(posture, include_details)

    def _handle_run_compliance_check(self, params):
        check_result = self.zvma_client.security.run_compliance_check(
            standard=params["standard"],
            scope=params.get("scope", "Full"),
            include_remediation=params.get("include_remediation", True)
        )
        return self._format_compliance_check(check_result)

    def _handle_get_audit_logs(self, params):
        logs = self.zvma_client.security.get_audit_logs(
            start_time=params.get("start_time"),
            end_time=params.get("end_time"),
            event_type=params.get("event_type"),
            severity=params.get("severity")
        )
        return self._format_audit_logs(logs)

    def _handle_verify_security_settings(self, params):
        check_categories = params.get("check_categories", ["Authentication", "Encryption", "NetworkSecurity", "DataProtection"])
        generate_report = params.get("generate_report", True)
        
        verification_results = {}
        for category in check_categories:
            verification_results[category] = self.zvma_client.security.verify_settings(category)
        
        return self._format_security_verification(verification_results, generate_report)

    def _format_security_posture(self, posture, include_details):
        output = ["Security Posture Assessment:"]
        
        for category, results in posture.items():
            output.append(f"\n{category} Security:")
            output.append(f"Status: {results.get('Status', 'Unknown')}")
            output.append(f"Risk Level: {results.get('RiskLevel', 'Unknown')}")
            output.append(f"Score: {results.get('Score', 'Unknown')}/100")
            
            if include_details and results.get('Findings'):
                output.append("\nFindings:")
                for finding in results['Findings']:
                    output.append(f"- {finding['Description']}")
                    output.append(f"  Severity: {finding['Severity']}")
                    if finding.get('Recommendation'):
                        output.append(f"  Recommendation: {finding['Recommendation']}")
        
        return "\n".join(output)

    def _format_compliance_check(self, results):
        output = [
            f"Compliance Check Results for {results.get('Standard', 'Unknown')}:",
            f"Overall Status: {results.get('Status', 'Unknown')}",
            f"Compliance Score: {results.get('Score', 'Unknown')}%",
            f"Controls Checked: {results.get('ControlsChecked', 0)}",
            f"Controls Passed: {results.get('ControlsPassed', 0)}",
            f"Controls Failed: {results.get('ControlsFailed', 0)}\n"
        ]
        
        if results.get('Findings'):
            output.append("Findings:")
            for finding in results['Findings']:
                output.append(f"\nControl: {finding.get('Control', 'Unknown')}")
                output.append(f"Status: {finding.get('Status', 'Unknown')}")
                output.append(f"Description: {finding.get('Description', 'Unknown')}")
                
                if finding.get('Remediation'):
                    output.append("Remediation Steps:")
                    for step in finding['Remediation']:
                        output.append(f"- {step}")
        
        return "\n".join(output)

    def _format_audit_logs(self, logs):
        if not logs:
            return "No audit logs found for the specified criteria."
        
        output = ["Audit Logs:"]
        for log in logs:
            output.extend([
                f"\nTimestamp: {log.get('Timestamp', 'Unknown')}",
                f"Event Type: {log.get('EventType', 'Unknown')}",
                f"Severity: {log.get('Severity', 'Unknown')}",
                f"User: {log.get('User', 'Unknown')}",
                f"Action: {log.get('Action', 'Unknown')}",
                f"Resource: {log.get('Resource', 'Unknown')}",
                f"Result: {log.get('Result', 'Unknown')}",
                f"Details: {log.get('Details', 'No additional details')}"
            ])
        
        return "\n".join(output)

    def _format_security_verification(self, results, generate_report):
        output = ["Security Settings Verification Results:"]
        
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            output.append(f"\n{category}:")
            category_checks = len(checks)
            category_passed = sum(1 for check in checks if check['Status'] == 'Pass')
            
            total_checks += category_checks
            passed_checks += category_passed
            
            output.append(f"Status: {category_passed}/{category_checks} checks passed")
            
            if generate_report:
                for check in checks:
                    output.append(f"\n- Setting: {check['Setting']}")
                    output.append(f"  Status: {check['Status']}")
                    output.append(f"  Current Value: {check['CurrentValue']}")
                    output.append(f"  Expected Value: {check['ExpectedValue']}")
                    if check['Status'] == 'Fail':
                        output.append(f"  Recommendation: {check['Recommendation']}")
        
        compliance_percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        output.insert(1, f"\nOverall Compliance: {compliance_percentage:.1f}%")
        output.insert(2, f"Total Checks: {total_checks}")
        output.insert(3, f"Passed Checks: {passed_checks}")
        
        return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(description="Zerto AI Agent")
    parser.add_argument("--zvm_address", required=True, help="ZVM address")
    parser.add_argument('--client_id', required=True, help='Keycloak client ID')
    parser.add_argument('--client_secret', required=True, help='Keycloak client secret')
    parser.add_argument("--ignore_ssl", action="store_true", help="Ignore SSL certificate verification")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        load_dotenv()
        agent = ZertoAIAgent(args)

        # Display welcome message and capabilities
        welcome_message = """
Welcome to Zerto AI Agent! I can help you with the following operations:

VPG Management:
- List and monitor VPGs
- Create and delete VPGs
- Add VMs to VPGs
- Create checkpoints
- Start/stop failover tests

Monitoring and Reporting:
- Check system alerts
- Monitor replication status
- View performance metrics
- Generate reports
- Check SLA compliance

Infrastructure Management:
- Manage VRAs
- Monitor datastores and networks
- Check site connectivity
- View resource usage

Security and Compliance:
- Run health checks
- View audit logs
- Check security posture
- Monitor encryption status

You can ask questions in natural language, and I'll help you manage your Zerto environment.
Type 'quit' to exit.

What would you like to help you with?
"""
        print(welcome_message)

        while True:
            try:
                query = input("\nEnter your question (or 'quit' to exit): ")
                if query.lower() == 'quit':
                    break
                elif query.lower() in ['help', 'how can you help me?', 'what can you do?']:
                    print(welcome_message)
                    continue
                    
                result = agent.process_query(query)
                print("\nResponse:", result)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logging.error(f"Error: {e}")

    except Exception as e:
        logging.exception("Error:")
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main() 