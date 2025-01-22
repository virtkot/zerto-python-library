"""
Zerto Reports Example

Note: The reports functionality is demonstrated in vpg_failover_example.py, which includes:

1. Recovery Reports:
   - Getting recovery reports for VPGs
   - Filtering reports by date range
   - Getting specific recovery operation details
   - Getting latest failover test reports

2. Resource Reports:
   - Getting resource reports with various filters
   - Filtering by site, cluster, and organization
   - Getting detailed resource information

Please refer to vpg_failover_example.py for practical examples of using the reports functionality.

You can run vpg_failover_example.py with:
    python vpg_failover_example.py \
        --site1_address <zvm_ip> \
        --site1_client_id <client_id> \
        --site1_client_secret <client_secret> \
        --vcenter1_ip <vcenter_ip> \
        --vcenter1_user <vcenter_user> \
        --vcenter1_password <vcenter_password> \
        --ignore_ssl

For more information about the reports API, see the RecoveryReports class in zvma/recovery_reports.py
"""

if __name__ == "__main__":
    print(__doc__) 