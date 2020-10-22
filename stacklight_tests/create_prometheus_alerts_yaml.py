import yaml

'''

1. Download repository of the 'prometheus' chart
2. Run validation and generate CSV with alerts:
   command: python3 styler.py --validate --csv
   (you will get the file 'alerts.csv')
3. Move file 'alerts.csv' into the directory '/files'
4. Run getting of the alerts
   command: python3 create_prometheus_alerts_yaml.py
5. Delete file 'alerts.csv'

'''


def main():
    with open('files/alerts.csv', 'r') as input_file:
        alerts_csv = input_file.read()
    alerts_csv_list = alerts_csv.strip('\n').split('\n')
    hash_alerts_dict = {}
    for alert in alerts_csv_list:
        current_alert = alert.split(';')
        hash_alerts_dict[current_alert[0]] = current_alert[3]
    with open('files/prometheus_alerts.yaml', 'w') as output_file:
        yaml.dump(hash_alerts_dict, output_file, default_flow_style=False)


if __name__ == '__main__':
    main()
