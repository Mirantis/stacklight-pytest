import pytest


@pytest.mark.run(order=-1)
@pytest.mark.telemetry
def test_telemetry_up(prometheus_api, k8s_api, chart_releases):
    if "telemeter-server" in chart_releases:
        def create_err_msg(failed_clusters):
            msg = ""
            for f in failed_clusters.keys():
                msg += "Telemeter-client of {}/{}/{} cluster does't sent" \
                       " data to telemeter-server." \
                    .format(failed_clusters[f][0], failed_clusters[f][1], f)
            return msg

        query = r'count({__name__=~"telemetry:.*",_id=~".+"}) by (_id)'
        output = prometheus_api.get_query(query)
        clusters_info = {}
        for i in k8s_api.get_clusters()['items']:
            releases = (i['spec']['providerSpec']
                        ['value'].get('helmReleases'))
            if releases:
                if any(r.get('name') == 'stacklight' for r in releases):
                    k = i['metadata']['annotations']['kaas.mirantis.com/uid']
                    v = [i['metadata']['namespace'], i['metadata']['name']]
                    clusters_info[k] = v
        clusters_id_expected = clusters_info.keys()
        clusters_id_actual = [o['metric']['_id'].split('/')[2] for o in output]
        failed_clusters = {}
        for i in clusters_id_expected:
            if i not in clusters_id_actual:
                failed_clusters[i] = clusters_info[i]
        assert len(failed_clusters) == 0, create_err_msg(failed_clusters)
    elif "telemeter-client" in chart_releases:
        pytest.skip("This test is only for management cluster")
    elif "kaas" not in k8s_api.list_namespaces():
        pytest.skip("This test is only for KaaS deployment")
    else:
        raise ValueError("Releases doesn't contain 'telemeter-client' "
                         "or 'telemeter-server'")


@pytest.mark.run(order=-1)
@pytest.mark.telemetry
def test_telemetry_recording_rules_consistency(prometheus_api, k8s_api,
                                               chart_releases):
    def create_err_msg(expected, actual):
        msg = "Actual count of recording rules " \
              "doesn't correspond to expected. " \
              "Difference is {} rules." \
            .format(abs(actual - expected))
        return msg

    prometheus_chart = k8s_api.get_stacklight_chart("prometheus")
    groups_with_recording_rules = (prometheus_chart['values']
                                                   ['extraRecordingRules']
                                                   ['extra-rules']['groups'])

    if "telemeter-server" in chart_releases:
        query = r'count(count({__name__=~"telemetry:.*",_id=~".+"}) ' \
                r'by (_id,__name__)) by (_id)'
        output = prometheus_api.get_query(query)
        recording_rules_total_expected = \
            len(filter(lambda x: x['name'] == 'telemetry.server.rules',
                       groups_with_recording_rules)[0]['rules'])
        recording_rules_per_cluster = {o['metric']['_id']: int(o['value'][1])
                                       for o in output}
        for k, v in recording_rules_per_cluster.items():
            recording_rules_total_actual = v
            current_expected = recording_rules_total_expected
            if k.split('/')[0] == 'default':
                current_expected = recording_rules_total_expected - 3
            err_msg = create_err_msg(current_expected,
                                     recording_rules_total_actual)
            assert current_expected == recording_rules_total_actual, \
                err_msg

    elif "telemeter-client" in chart_releases:
        query = r'count(count({__name__=~"telemetry:.*"}) by (__name__))'
        output = prometheus_api.get_query(query)
        recording_rules_total_expected = \
            len(filter(lambda x: x['name'] == 'telemetry.client.rules',
                       groups_with_recording_rules)[0]['rules'])
        recording_rules_total_actual = int(output[0]['value'][1])
        err_msg = create_err_msg(recording_rules_total_expected,
                                 recording_rules_total_actual)
        assert recording_rules_total_expected == recording_rules_total_actual,\
            err_msg
    else:
        pytest.skip("Releases doesn't contain 'telemeter-client' "
                    "or 'telemeter-server'")
