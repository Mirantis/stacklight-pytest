import pytest


@pytest.mark.run(order=-1)
@pytest.mark.telemetry
def test_telemetry_up(prometheus_api, k8s_api, chart_releases):
    if "telemeter-client" in chart_releases:
        pytest.skip("This test is only for management cluster.")
    elif "telemeter-server" in chart_releases:
        def create_err_msg(failed_clusters):
            msg = ""
            for f in failed_clusters.keys():
                msg += "Telemeter-client of {}/{}/{} cluster does't sent" \
                       " data to telemeter-server." \
                    .format(failed_clusters[f][0], failed_clusters[f][1], f)
            return msg

        query = r'count({__name__=~"telemetry:.*",cluster_id=~".+"}) ' \
                r'by (cluster_id)'
        output = prometheus_api.get_query(query)
        clusters_info = {}
        for i in k8s_api.get_clusters()['items']:
            releases = (i['spec']['providerSpec']
                        ['value'].get('helmReleases'))
            if releases:
                if any(r.get('name') == 'stacklight' for r in releases):
                    k = i['metadata']['annotations']\
                        .get('kaas.mirantis.com/uid', i['metadata']
                             ['annotations'].get('uid'))
                    v = [i['metadata']['namespace'], i['metadata']['name']]
                    clusters_info[k] = v
        clusters_id_expected = clusters_info.keys()
        clusters_id_actual = [o['metric']['cluster_id'].split('/')[2]
                              for o in output]
        failed_clusters = {}
        for i in clusters_id_expected:
            if i not in clusters_id_actual:
                failed_clusters[i] = clusters_info[i]
        assert len(failed_clusters) == 0, create_err_msg(failed_clusters)
    elif "kaas" not in k8s_api.list_namespaces():
        pytest.skip("This test is only for KaaS deployment.")
    else:
        raise ValueError("Releases doesn't contain 'telemeter-client' "
                         "or 'telemeter-server'.")


@pytest.mark.run(order=-1)
@pytest.mark.telemetry
def test_telemetry_recording_rules_consistency(prometheus_api, k8s_api,
                                               chart_releases,
                                               stacklight_bundle):
    skip_list_general = ['telemetry:openstack']

    skip_list_management = ['telemetry:federate_errors',
                            'telemetry:federate_filtered_samples',
                            'telemetry:federate_samples'] + skip_list_general
    skip_list_child = ['telemetry:kaas_clusters',
                       'telemetry:kaas_machines_requested',
                       'telemetry:kaas_machines_ready'] + skip_list_general

    prometheus_chart = k8s_api.get_stacklight_chart("prometheus")

    def get_expected_metrics(group_of_rules):
        groups_with_recording_rules = (prometheus_chart['values']
                                       ['extraRecordingRules']
                                       ['extra-rules']['groups'])
        expected_metrics = set([metric['record'] for metric in
                               filter(lambda x: x['name'] == group_of_rules,
                                      groups_with_recording_rules)
                               [0]['rules']])
        return expected_metrics

    def get_label_injection(s_b):
        s_b = str(s_b)
        if 'management_id' in s_b:
            return 'management_id'
        elif 'region_id' in s_b:
            return 'region_id'
        else:
            return 'cluster_id'

    def apply_skip_list(m_expected, skip_list):
        metrics_to_remove = []
        for m_e in m_expected:
            for m_s_l in skip_list:
                if m_e.startswith(m_s_l):
                    metrics_to_remove.append(m_e)
        for m_t_r in metrics_to_remove:
            m_expected.remove(m_t_r)

    def create_err_msg(m_expected=None, m_actual=None, f_c=None):
        if f_c:
            msg = "Actual count of metrics generated by recording rules " \
                  "doesn't correspond to expected on these clusters: {}."\
                .format(f_c)
            return msg
        else:
            msg = "Actual count of metrics generated by recording rules " \
                  "doesn't correspond to expected. " \
                  "These metrics {} were not found."\
                .format(m_expected.difference(m_actual))
            return msg

    if "telemeter-server" in chart_releases:
        label_injection = get_label_injection(stacklight_bundle)
        failed_clusters = []
        query = r'count(count({{__name__=~"telemetry:.*",{0}=~".+"}}) ' \
                r'by ({0},__name__)) by ({0})'.format(label_injection)
        output = prometheus_api.get_query(query)
        cluster_ids = [o['metric']['{}'.format(label_injection)]
                       for o in output]
        metrics_expected = get_expected_metrics(
            'telemetry.cluster.rules')
        for c_id in cluster_ids:
            metrics_expected_iter = set(metrics_expected)
            query_to_get_metrics = 'count({{__name__=~"telemetry:.*",' \
                                   '{0}="{1}"}}) by (__name__)'\
                .format(label_injection, c_id)
            output = prometheus_api.get_query(query_to_get_metrics)
            metrics_actual = set([metric['metric']['__name__']
                                 for metric in output])
            if "telemeter-client" in chart_releases:
                apply_skip_list(metrics_expected_iter,
                                skip_list_child)
            elif c_id.split('/')[0] == 'default':
                apply_skip_list(metrics_expected_iter,
                                skip_list_management)
            else:
                apply_skip_list(metrics_expected_iter, skip_list_child)
            if metrics_expected_iter != metrics_actual:
                failed_clusters.append({'cluster_info': c_id,
                                        'absent_rules':
                                        metrics_expected_iter
                                       .difference(metrics_actual)})
        assert len(failed_clusters) == 0, \
            create_err_msg(f_c=failed_clusters)
    elif "telemeter-client" in chart_releases:
        query_to_get_metrics = 'count({__name__ =~"telemetry:.*"}) ' \
                               'by(__name__)'
        output = prometheus_api.get_query(query_to_get_metrics)
        metrics_expected = get_expected_metrics(
            'telemetry.cluster.rules')
        apply_skip_list(metrics_expected, skip_list_child)
        metrics_actual = set([metric['metric']['__name__']
                             for metric in output])
        assert metrics_expected == metrics_actual, \
            create_err_msg(metrics_expected, metrics_actual)
    else:
        pytest.skip("Releases doesn't contain 'telemeter-client' "
                    "or 'telemeter-server'.")
