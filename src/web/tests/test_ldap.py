from backend.ldap.utils import merge_divisions


def test_merge_divisions():
    config_divisions = {
        'it': 'IT',
        'leg': 'Legal',
        'random': 'Random'
    }
    ldap_divisions = [{'fqdn': 'cn=it,ou=divisions,dc=entint,dc=org', 'cn': [b'it'], 'description': [b'It']},
                      {'fqdn': 'cn=pub,ou=divisions,dc=entint,dc=org', 'cn': [b'pub'], 'description': [b'Publishing']},
                      {'fqdn': 'cn=qwe,ou=divisions,dc=entint,dc=org', 'cn': [b'qwe']},
                      {'fqdn': 'cn=qwe1,ou=divisions,dc=entint,dc=org', 'cn': [b'qwe1']}
                      ]
    ldap_only_divisions = ['pub', 'qwe', 'qwe1']
    config_only_divisions = ['leg', 'random']
    common_division_name = 'it'
    merged_divisions = merge_divisions(config_divisions, ldap_divisions)
    # check if total count of merged divs equals sum of ldap, config divs, except common divisions
    assert len(merged_divisions) == len(config_divisions) + len(ldap_divisions) - 1

    for div_machine_name, div_data in merged_divisions.items():
        if div_machine_name in ldap_only_divisions:  # check params of ldap only divisions
            assert div_data['exists_in_ldap']
            assert not div_data['exists_in_config']
        elif div_machine_name in config_only_divisions:  # check params of config only divisions
            assert not div_data['exists_in_ldap']
            assert div_data['exists_in_config']
        elif div_machine_name == common_division_name:  # check params of common division
            assert div_data['exists_in_ldap']
            assert div_data['exists_in_config']
            assert div_data['ldap_display_name'] == 'It'
            assert div_data['config_display_name'] == 'IT'
        else:
            raise Exception('Unknown division')



