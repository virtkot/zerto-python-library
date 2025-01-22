# zerto-python-library
Zerto API python writer


# vpg command line
python3 ./vpg_example.py --site1_address 192.168.111.20 --site1_client_id zerto-api --site1_client_secret QhmYHoya063pc0vHa7QZtsz6r3a32PLi  --vcenter1_ip 192.168.111.10 --vcenter1_user administrator@vsphere.local --vcenter1_password Zertodata1! --site2_address 192.168.222.20 --site2_client_id zerto-api --site2_client_secret P4UdUottG97iIWzeWe1jVD5z2vvz1dx4 --vcenter2_ip 192.168.222.10 --vcenter2_user administrator@vsphere.local --vcenter2_password Zertodata1! --ignore_ssl

# alerts command line
python3 ./alerts_example.py --site1_address 192.168.111.20 --site1_client_id zerto-api --site1_client_secret QhmYHoya063pc0vHa7QZtsz6r3a32PLi  --vcenter1_ip 192.168.111.10 --vcenter1_user administrator@vsphere.local --vcenter1_password Zertodata1! --site2_address 192.168.222.20 --site2_client_id zerto-api --site2_client_secret P4UdUottG97iIWzeWe1jVD5z2vvz1dx4 --vcenter2_ip 192.168.222.10 --vcenter2_user administrator@vsphere.local --vcenter2_password Zertodata1! --ignore_ssl

# datastore command line
python3 ./datastore_example.py --zvm_address 192.168.111.20 --client_id zerto-api --client_secret QhmYHoya063pc0vHa7QZtsz6r3a32PLi  --vcenter_address 192.168.111.10 --vcenter_user administrator@vsphere.local --vcenter_password Zertodata1! --ignore_ssl